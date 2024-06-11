import requests
import datetime
import pandas as pd

from carbon_abatement_api.config import NG_carbon_intensity_base_url
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from functools import lru_cache

class NationalGridApiAccessor:
    """
    Class to interact with the National Grid API for carbon intensity data retrieval.
    """

    def __init__(self):
        self.host = NG_carbon_intensity_base_url

    def get_carbon_intensity(self, from_date, to_date, region_id, get_regional=False):
        """
        Retrieve regional and national carbon intensity data.
        This parallelizes calls for every month of data, since NGESO API fails for date
        ranges greater than one month.

        Parameters
        ----------
        from_date : str
            The starting date for the data retrieval in the format 'YYYY-mm-dd'.
        to_date : str
            The end date for the data retrieval in the format 'YYYY-mm-dd'.
        region_id : int
            The ID of the region for which data is to be retrieved.
        get_regional: boolean
            Option to get regional data. Regional data is not needed for agent

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the carbon intensity data.
        """
        print(f"getting carbon intensity data for {from_date} to {to_date}")
        # Formatting the date to the required API format
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)

        # List to store all the intensity data
        regional_futures = [] if get_regional else None
        national_futures = []

        with ThreadPoolExecutor() as executor:
            while from_date < to_date:
                # NGESO API can only return up to 29 days of data at a time
                end_date = from_date + relativedelta(days=29)

                if from_date.year != end_date.year:
                    # Set end_date to the start of the next year
                    end_date = datetime.datetime(from_date.year + 1, 1, 1)

                if end_date > to_date:
                    end_date = to_date

                # Submit a new task to the executor
                if get_regional:
                    regional_intensity = executor.submit(self.get_regional_carbon_intensity, from_date, end_date + timedelta(days=1), region_id)
                    regional_futures.append(regional_intensity)

                national_intensity = executor.submit(self.get_national_carbon_intensity, from_date, end_date + timedelta(days=1))
                national_futures.append(national_intensity)

                from_date = end_date

        # Collect results as they become available
        regional_data_list = []
        if get_regional:
            for future in regional_futures:
                result = future.result()
                print(result)
                if isinstance(result, pd.DataFrame):  # Check if the result is a DataFrame
                    regional_data_list.append(result)

        national_data_list = []
        for future in national_futures:
            result = future.result()
            if isinstance(result, pd.DataFrame):  # Check if the result is a DataFrame
                national_data_list.append(result)

        # Concatenate all the dataframes
        national_df = pd.concat(national_data_list, ignore_index=True)

        # in case days overlap in the API calls
        national_df = national_df.drop_duplicates()

        if get_regional:
            regional_df = pd.concat(regional_data_list, ignore_index=True)
            regional_df = regional_df.drop_duplicates()
            print(regional_df)
            full_df = pd.merge(regional_df, national_df[['from', 'nationalIntensity']], on='from', how='left')
            full_df['nationalIntensity'] = full_df['nationalIntensity'].fillna(full_df['regionalIntensity'])
            return full_df

        return national_df

    def get_regional_carbon_intensity(self, from_date, to_date, region_id):
        """
        Retrieve the regional carbon intensity data for a specific region for up to one month.

        Parameters
        ----------
        from_date : datetime
            The starting date for the data retrieval.
        to_date : datetime
            The end date for the data retrieval.
        region_id : int
            The ID of the region for which data is to be retrieved.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the regional carbon intensity data.
        """
        headers = {
            'Accept': 'application/json'
        }

        from_date_str = from_date.strftime('%Y-%m-%dT%H:%MZ')
        to_date_str = to_date.strftime('%Y-%m-%dT%H:%MZ')

        url = f'{self.host}/regional/intensity/{from_date_str}/{to_date_str}/regionid/{region_id}'

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return self.process_regional_ci_data(response)
        else:
            print("Failed to retrieve regional intensity data for date range {0} to {1}".format(from_date_str, to_date_str))
            return pd.DataFrame()


    @lru_cache(maxsize=None)
    def get_national_carbon_intensity(self, from_date, to_date):
        """
        Retrieve the national carbon intensity data for up to one month.

        Parameters
        ----------
        from_date : datetime
            The starting date for the data retrieval.
        to_date : datetime
            The end date for the data retrieval.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the national carbon intensity data.
        """
        headers = {
            'Accept': 'application/json'
        }

        from_date_str = from_date.strftime('%Y-%m-%dT%H:%MZ')
        to_date_str = to_date.strftime('%Y-%m-%dT%H:%MZ')

        url = f'{self.host}/intensity/{from_date_str}/{to_date_str}'

        response = requests.get(url, headers=headers)

        if response.status_code == 200:

            return self.process_national_ci_data(response)

        else:
            print("Failed to retrieve national intensity data for date range {0} to {1}".format(from_date_str, to_date_str))
            return pd.DataFrame()


    def process_national_ci_data(self, response):
        # Concatenate the data DataFrame with the original DataFrame
        df = pd.DataFrame(response.json()['data'])
        # print(df)

        # Just get the actual intensity value, not the forecast
        # print(pd.json_normalize(df['intensity']))
        df['forecast'] = pd.json_normalize(df['intensity'])['forecast']
        df['intensity'] = pd.json_normalize(df['intensity'])['actual']



        # df['forecast'] = pd.json_normalize(df['intensity'])['forecast']

        df.reset_index(inplace=True)
        df.rename(columns={'intensity': 'nationalIntensity'}, inplace=True)
        df['from'] = pd.to_datetime(df['from'])
        df['to'] = pd.to_datetime(df['to'])

        return df

    def process_regional_ci_data(self, response):
        # Concatenate the data DataFrame with the original DataFrame
        df = pd.DataFrame(response.json()['data'])

        # Convert the data column into a DataFrame
        data = pd.json_normalize(df['data'])

        df = pd.concat([df.drop('data', axis=1), data], axis=1)

        df = df.drop(columns=['generationmix'])

        df.reset_index(inplace=True)
        df.rename(columns={'index': 'settlementPeriod', 'intensity.forecast': 'regionalIntensity'}, inplace=True)
        df['from'] = pd.to_datetime(df['from'])
        df['settlementPeriod'] = (df['settlementPeriod'] + 47) % 48 + 1
        df['settlementDate'] = df['from'].dt.date

        return df
