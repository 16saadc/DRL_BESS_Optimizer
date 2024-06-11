from carbon_abatement_api.bmrs_api_accessor import BmrsApiAccessor
from carbon_abatement_api.nationalgrid_api_accessor import NationalGridApiAccessor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from carbon_abatement_api.config import PN_STREAM_ENDPOINT, UK_regions_map, BESS_fleet
from datetime import datetime, timedelta
import os
from carbon_abatement_api.plotting_functions import plot_avg_energy_output


class CarbonAbatementCalculator:
    def __init__(self):
        self.bmrs_api_accessor = BmrsApiAccessor()
        self.nationalgrid_api_accessor = NationalGridApiAccessor()
        self.bmu_list = list(BESS_fleet.index)

    def get_bmu_selection(self):
        print("Select a BMU from the following options:")

        for i, bmu in enumerate(self.bmu_list, 1):
            print(f"{i}: {bmu}")

        bmu_selection = input("Enter the number or ID of your selected BMU: ")

        while not self.validate_bmu_selection(bmu_selection):
            print("Invalid selection. Please select a valid number or name.")
            bmu_selection = input("Enter the number or name of your selected BMU: ")

        return bmu_selection


    def validate_bmu_selection(self, bmu_selection):
        if bmu_selection.isdigit():

            return 1 <= int(bmu_selection) <= len(self.bmu_list)
        else:
            return bmu_selection in self.bmu_list


    def get_actual_bmu(self, bmu_selection):
        if bmu_selection.isdigit():
            return self.bmu_list[int(bmu_selection) - 1]
        else:
            return bmu_selection

    def get_date_selection(self):
        from_date = input("Enter the from_date (yyyy-mm-dd): ")
        to_date = input("Enter the to_date (yyyy-mm-dd): ")

        while not self.validate_dates(from_date, to_date):
            print("Invalid dates. The to_date must be later than the from_date.")
            from_date = input("Enter the from_date (yyyy-mm-dd): ")
            to_date = input("Enter the to_date (yyyy-mm-dd): ")

        return from_date, to_date


    def validate_dates(self, from_date, to_date):
        to_date_converted = datetime.strptime(to_date, "%Y-%m-%d")
        from_date_converted = datetime.strptime(from_date, "%Y-%m-%d")
        return (to_date_converted > from_date_converted)


    def get_weighted_average_ci(self, full_data):
        """
        Calculates an average value of the regional and national carbon intensity across all PNs, with
        the energyCharged or energyDischarged for each PN as weights for each intensity value.

        Parameters
        ----------
        full_data : pd.DataFrame
            the physical notification data with regional and national
            carbon intensity values for each PN

        Returns
        -------
        CIc_regional
            the weighted average regional carbon intensity during times the BMU charged
        CId_regional
            the weighted average regional carbon intensity during times the BMU discharged
        CIc_national
            the weighted average national carbon intensity during times the BMU charged
        CId_national
            the weighted average national carbon intensity during times the BMU discharged
        """

        CIc_regional = np.average(full_data.loc[full_data['energyCharged'].notnull(), 'regionalIntensity'], weights=full_data.loc[full_data['energyCharged'].notnull(), 'energyCharged']) / 0.001
        CId_regional = np.average(full_data.loc[full_data['energyDischarged'].notnull(), 'regionalIntensity'], weights=full_data.loc[full_data['energyDischarged'].notnull(), 'energyDischarged']) / 0.001

        CIc_national = np.average(full_data.loc[full_data['energyCharged'].notnull(), 'nationalIntensity'], weights=full_data.loc[full_data['energyCharged'].notnull(), 'energyCharged']) / 0.001
        CId_national = np.average(full_data.loc[full_data['energyDischarged'].notnull(), 'nationalIntensity'], weights=full_data.loc[full_data['energyDischarged'].notnull(), 'energyDischarged']) / 0.001
        return CIc_regional, CId_regional, CIc_national, CId_national


    def calculate_total_carbon_abated(self, bmu_bess_data, from_date="2023-01-01", to_date="2023-01-10", output_dir=""):
        """
        Calculates the total carbon abated by a BMU between the selected date, not inclusive of the to_date

        Makes calls to NGESO and BMRS classes to get their respective data and merges them

        Calculates the carbon abated using both regional and national intensities, using this formula:

            ((CId - CIc) * Ec - ((Ec - Ed) * CIc)) * 0.001 / Ed


        Parameters
        ----------
        from_date : str
            the date to start the analysis from
        to_date : str
            the date to end the analysis (not inclusive)
        bmu:
            the BMU to analyze. Add this to BMU_region_map in config.py if it's not there

        Returns
        -------
        results : pd.DataFrame
            the carbon_abated_regional, carbon_abated_national, CIc_regional, CId_regional, CIc_national, CId_national (all in grams and tons), energyCharged, energyDischarged,
            capacity, duration, regionId, regionName of each BMU analyzed concatenated into a DataFrame

        """
        # bmu_bess_data = BESS_fleet.loc[bmu]

        bmu = bmu_bess_data.name
        region_id = bmu_bess_data['Region']

        ci_data = self.nationalgrid_api_accessor.get_carbon_intensity(from_date, to_date, region_id, get_regional=True)

        results = []

        print("------------------------------------------- \n")
        print(f"Running analysis on BMU {bmu}")

        try:
            pn_data = self.bmrs_api_accessor.get_pn_stream_data(PN_STREAM_ENDPOINT, from_date, to_date, bm_unit=[bmu])
        except:
            # if thers no PN data in the time frame
            return {
                "BMUID": bmu,
                "carbon_abated_regional (g CO2/MWh Discharged)": carbon_abated_regional,
                "carbon_abated_national (g CO2/MWh Discharged)": 0,
                "carbon_abated_regional (mt CO2/MWh Discharged)": carbon_abated_regional / 1e6,
                "carbon_abated_national (mt CO2/MWh Discharged)": 0,
                "CIc_regional (g CO2/MWh)": CIc_regional,
                "CId_regional (g CO2/MWh)": CId_regional,
                "CIc_national (g CO2/MWh)": 0,
                "CId_national (g CO2/MWh)": 0,
                "CIc_regional (mt CO2/MWh)": CIc_regional / 1e6,
                "CId_regional (mt CO2/MWh)": CId_regional / 1e6,
                "CIc_national (mt CO2/MWh)": 0,
                "CId_national (mt CO2/MWh)": 0,
                "Ec (MWh)": 0,
                "Ed (MWh)": 0,
                "MW Capacity": bmu_bess_data['MW'],
                "MWh Capacity": bmu_bess_data['MWh'],
                "Duration": bmu_bess_data['MWh'] / bmu_bess_data['MW'],
                "RegionId": region_id,
                "RegionName": UK_regions_map[region_id]
            }

        full_data = self.map_dates_and_intensities(pn_data, ci_data)

        # data always returns an extra settlement period on each end
        full_data = full_data.iloc[1:-1]

        CIc_regional, CId_regional, CIc_national, CId_national = self.get_weighted_average_ci(full_data)

        energyCharged = full_data['energyCharged'].sum()
        energyDischarged = full_data['energyDischarged'].sum()

        print(f"CIc regional: {CIc_regional}")
        print(f"CIc national: {CIc_national}")

        print(f"CId regional: {CId_regional}")
        print(f"CId national: {CId_national}")

        print(f"energyCharged: {energyCharged}")
        print(f"energyDischarged {energyDischarged}")

        carbon_abated_regional = ((CId_regional - CIc_regional) * energyDischarged - ((energyCharged - energyDischarged) * CIc_regional))  / energyDischarged
        carbon_abated_national = ((CId_national - CIc_national) * energyDischarged - ((energyCharged - energyDischarged) * CIc_national)) / energyDischarged

        columns_to_remove = ['dataset', 'nationalGridBmUnit', 'time_gap', 'intensity.index', 'dnoregion', 'shortname', 'from', 'to']
        full_data.drop(labels=columns_to_remove, axis=1, inplace=True)

        bmu_name = bmu_bess_data['Name']
        dir_name = f'{output_dir}/{bmu_name}'
        # Check if directory exists
        os.makedirs(dir_name, exist_ok=True)

        for column in full_data.columns:
            if isinstance(full_data[column].dtype, pd.DatetimeTZDtype):
                full_data[column] = full_data[column].dt.tz_localize(None)

        full_data.to_excel(f'{dir_name}/{bmu_name}_CA_analysis_{from_date}_{to_date}.xlsx')

        fig = plot_avg_energy_output(full_data, ci_data, bmu, bmu_bess_data, from_date, to_date)

        plt.savefig(f'{dir_name}/{bmu_name}_energyOut_vs_time_{from_date}_{to_date}.png')


        result = {
            "BMUID": bmu,
            # "carbon_abated_regional (g CO2/MWh Discharged)": carbon_abated_regional,
            "carbon_abated_national (g CO2/MWh Discharged)": carbon_abated_national,
            # "carbon_abated_regional (mt CO2/MWh Discharged)": carbon_abated_regional / 1e6,
            "carbon_abated_national (mt CO2/MWh Discharged)": carbon_abated_national / 1e6,
            # "CIc_regional (g CO2/MWh)": CIc_regional,
            # "CId_regional (g CO2/MWh)": CId_regional,
            "CIc_national (g CO2/MWh)": CIc_national,
            "CId_national (g CO2/MWh)": CId_national,
            # "CIc_regional (mt CO2/MWh)": CIc_regional / 1e6,
            # "CId_regional (mt CO2/MWh)": CId_regional / 1e6,
            "CIc_national (mt CO2/MWh)": CIc_national / 1e6,
            "CId_national (mt CO2/MWh)": CId_national / 1e6,
            "Ec (MWh)": energyCharged,
            "Ed (MWh)": energyDischarged,
            "MW Capacity": bmu_bess_data['MW'],
            "MWh Capacity": bmu_bess_data['MWh'],
            "Duration": bmu_bess_data['MWh'] / bmu_bess_data['MW'],
            # "RegionId": region_id,
            # "RegionName": UK_regions_map[region_id]
        }

        return result


    def map_dates_and_intensities(self, pn_data, ci_data):
        """
        Merges the carbon intesnity data into the PN data.
        Adds the row of ci_data using the nearest 'from' value that is less than or equal to the 'timeFrom' value in the pn_data.

        Parameters
        ----------
        pn_data : pd.DataFrame
            the physical notification data of the BMU
        ci_data : pd.DataFrame
            the carbon intensity data containing both regionalIntensity and nationalIntensity

        Returns
        -------
        full_data
            the merged dataframe containing PN data and its respected carbon intensity at each row
        """

        print('merging PN and CI data...')

        # Ensure datetime columns are in datetime format
        pn_data['timeFrom'] = pd.to_datetime(pn_data['timeFrom'])
        ci_data['from'] = pd.to_datetime(ci_data['from'])

        pn_data.drop(['settlementDate', 'settlementPeriod'], axis=1, inplace=True)
        # Sort dataframes
        pn_data = pn_data.sort_values('timeFrom')
        ci_data = ci_data.sort_values('from')

        # join on nearest 'from' less than or equal to 'timeFrom'
        # since ci data covers all time intervals we wont miss any
        full_data = pd.merge_asof(pn_data, ci_data, left_on='timeFrom', right_on='from')

        return full_data
