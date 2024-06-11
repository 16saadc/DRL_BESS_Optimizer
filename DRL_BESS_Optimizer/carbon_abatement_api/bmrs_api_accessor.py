import requests
import httplib2
import pandas as pd
import io
import json
from carbon_abatement_api.config import BMRS_base_url
from concurrent.futures import ThreadPoolExecutor

class BmrsApiAccessor:
    """
    A class used to interact with Elexon's BMRS API.
    """

    def __init__(self):
        self.host = BMRS_base_url

    def get_pn_stream_data(self, endpoint, from_date, to_date, settlement_period_from=None, settlement_period_to=None, bm_unit=[], format='json'):
        """
        Fetches physical notification stream data for given parameters from the BMRS API.
        Note that settlement_period_from and settlement_period_to only apply to the from_date and to_date of the API.
        The days in between will contain data for all settlement periods

        Parameters
        ----------
        endpoint : str
            the API endpoint to use for fetching data
        from_date : str
            the starting date for fetching data
        to_date : str
            the ending date for fetching data
        settlement_period_from : int, optional
            the starting settlement period for fetching data
        settlement_period_to : int, optional
            the ending settlement period for fetching data
        bm_unit : list, optional
            a list of BM unit identifiers for fetching data
        format : str, optional
            the format of the response data (default is 'json')

        Returns
        -------
        pd.DataFrame
            a DataFrame containing the fetched data
        """


        params = {
            'from': from_date,
            'to': to_date,
            'settlementPeriodFrom': settlement_period_from,
            'settlementPeriodTo': settlement_period_to,
            'bmUnit': bm_unit,
            'format': format
        }

        url = f'{self.host}{endpoint}'

        data = self.pn_stream_api_call(url, params)

        return self.process_pn_data(data, from_date, to_date)

    def pn_stream_api_call(self, url, params):
        """
        Sends a GET request to the BMRS API.

        Parameters
        ----------
        url : str
            the URL for the API endpoint
        params : dict
            the parameters for the API request

        Returns
        -------
        pd.DataFrame
            a DataFrame containing the response data
        """
        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise Exception(f'{response.status_code}, {response.text}')

        data = json.loads(response.text)

        if data == None or len(data) == 0:
            raise Exception("No data is available for this BMU between the dates provided")

        return pd.DataFrame(data)

    def insert_row(self, df, idx, df_insert):
        dfA = df.iloc[:idx, ]
        dfB = df.iloc[idx:, ]

        df = dfA.append(df_insert).append(dfB).reset_index(drop=True)

        return df

    def process_pn_data(self, pn_data, from_date, to_date):
        """
        Processes physical notification data and calculates energy values.

        Parameters
        ----------
        pn_data : pd.DataFrame
            the physical notification data
        from_date : str
            the starting date for the data
        to_date : str
            the ending date for the data

        Returns
        -------
        pd.DataFrame
            the processed physical notification data with calculated energy values
        """
        pn_data['timeFrom'] = pd.to_datetime(pn_data['timeFrom'])
        pn_data['timeTo'] = pd.to_datetime(pn_data['timeTo'])
        pn_data['settlementDate'] = pd.to_datetime(pn_data['settlementDate'])

        # get time difference in hours to get energy in MWh
        pn_data['timeDifference'] = (pn_data['timeTo'] - pn_data['timeFrom']).dt.total_seconds() / 3600

        # check if there are gaps in the data
        pn_data['time_gap'] = pn_data['timeFrom'] - pn_data['timeTo'].shift(-1)
        # pn_data['time_gap'] = pn_data['timeFrom'] - pn_data['timeTo'].shift(1)

        pn_data = self.fill_time_gaps(pn_data)

        pn_data['energyOut'] = 0.5 * (pn_data['levelFrom'] + pn_data['levelTo']) * pn_data['timeDifference']


        pn_data['energyCharged'] = pn_data['energyOut'].apply(lambda x: -x if x < 0 else None)
        pn_data['energyDischarged'] = pn_data['energyOut'].apply(lambda x: x if x > 0 else None)

        if pn_data['energyCharged'].isnull().all() or pn_data['energyDischarged'].isnull().all():
            pn_data['energyCharged'] = 0.00001
            pn_data['energyDischarged'] = 0.00001
            # raise Exception("The selected BMU did not charge and/or discharge during this time, try different dates or a different BMU")


        return pn_data


    def fill_time_gaps(self, pn_data):
        """
        Identifies and fills time gaps in the physical notification data.

        i.e.
        levelFrom=10, levelTo=20, timeFrom=5:00, timeTo=5:30
        levelFrom=20, levelTo=25, timeFrom=6:00, timeTo=6:30

        it will add the following row in between them to fill the gap in time, assuming linear charging / discharging rate
        levelFrom=20, levelTo=20: timeFrom=5:30, timeTo=6:00

        Parameters
        ----------
        pn_data : pd.DataFrame
            the physical notification data

        Returns
        -------
        pd.DataFrame
            the physical notification data with time gaps filled
        """
        # reverse indices so that they dont affect subsequent iterations
        time_gap_indices = pn_data.loc[pn_data['time_gap'] > pd.Timedelta(seconds=0)].index[::-1]
        for i in time_gap_indices.tolist():
            df_insert = pn_data.iloc[i+1]
            # get timeTo from previous PN and timeFrom from next PN
            df_insert['timeFrom'] = df_insert['timeTo']
            df_insert['timeTo'] = pn_data.iloc[i]['timeFrom']
            pn_data['timeDifference'] = (pn_data['timeTo'] - pn_data['timeFrom']).dt.total_seconds() / 3600

            pn_data = self.insert_row(pn_data, i+1, df_insert)

        return pn_data

    def get_legacy_pn_data(self, from_date, to_date, settlement_period_from=None, settlement_period_to=None, bm_unit=None):
        """
        Fetches legacy physical notification data from the BMRS API.
        Parallelizes API calls for each day, since legacy API only supports 1 day of data at a time

        Parameters
        ----------
        from_date : str
            the starting date for fetching data
        to_date : str
            the ending date for fetching data
        settlement_period_from : int, optional
            the starting settlement period for fetching data
        settlement_period_to : int, optional
            the ending settlement period for fetching data
        bm_unit : str, optional
            a BM unit identifier for fetching data

        Returns
        -------
        pd.DataFrame
            a DataFrame containing the processed physical notification data
        """

        version_no = 'v1'
        response_fmt = 'csv'
        api_key = '6kxcthen75ci5os'

        list_of_dates = pd.date_range(start=from_date,end=to_date).strftime('%Y-%m-%d').to_list()

        futures = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            for sd in list_of_dates:
                futures.append(executor.submit(self.process_date_legacy, sd, version_no, response_fmt, bm_unit, api_key))

        # After all jobs have completed concatenate the results
        data = pd.concat([future.result() for future in futures], ignore_index=True)

        data[4]=pd.to_numeric(data[4]) #changing the MW columns to number types in ll record type sheets so we can manipulate data


        data[6]=pd.to_numeric(data[6])

        data[3] = pd.to_datetime(data[3], format='%Y%m%d%H%M%S')# converting all of the dates from strings to datetime format
        data[5] = pd.to_datetime(data[5], format='%Y%m%d%H%M%S')

        column_headers = ['dataset','bmUnit', 'settlementPeriod', 'timeFrom', 'levelFrom', 'timeTo', 'levelTo']
        data.columns = column_headers

        data['settlementDate'] = data['timeFrom'].dt.date

        return self.process_pn_data(data, from_date, to_date)


    def process_date_legacy(self, sd, version_no, response_fmt, bm_unit, api_key):
        """
        Fetches and processes PN data for a given date. Used for legacy API.
        Retries 3 times because this API times out sometimes.

        Parameters
        ----------
        sd : str
            the date for fetching data
        version_no : str
            the version number of the BMRS API
        response_fmt : str
            the format of the response data
        bm_unit : str
            a BM unit identifier for fetching data
        api_key : str
            the API key for accessing the BMRS API

        Returns
        -------
        pd.DataFrame
            a DataFrame containing the processed PN data for the given date
        """
        for _ in range(3): # retry 3 times, because sometimes the API call times out
            sp = '*'
            print(f"Getting PN data for {sd}")
            url = f'https://api.bmreports.com/BMRS/PHYBMDATA/{version_no}?APIKey={api_key}&SettlementDate={sd}&SettlementPeriod={sp}&BMUnitId={bm_unit}&ServiceType={response_fmt}'
            http_obj = httplib2.Http()
            resp, content = http_obj.request(uri=url, method='GET',headers={'Content-Type': 'application/xml; charset=UTF-8'},)

            if '504 Gateway Time-out' in content.decode():
                print(f"PN data retrieval timed out for {sd}. Retrying...")
                time.sleep(5)  # wait for 5 seconds before retrying
                continue


            temp = content.decode().split('\n')
            i = range(1,len(temp))
            system_det = []

            for values in i:
                x = temp[values].split(',')
                system_det.append(x)

            curr = pd.DataFrame(system_det)

            # relevant data is in first 7 columns
            curr = curr[curr[0] == 'PN'].iloc[:,:7]

            return curr
