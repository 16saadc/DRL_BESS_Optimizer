from carbon_abatement_calculator import CarbonAbatementCalculator
import warnings
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from config import BMUs_for_analysis, BESS_fleet, output_path, user_prompted, FROM_DATE, TO_DATE
import openpyxl
import time
import os
from plotting_functions import plot_comparison, plot_comparison_four_bars, box_plot_asset

def user_prompted_analysis():

    calculator = CarbonAbatementCalculator()

    # Get BMU selection
    bmu_selection = calculator.get_bmu_selection()

    print("\n ------------------------------------------- \n")

    # Get the actual BMU
    bmu = calculator.get_actual_bmu(bmu_selection)

    # Get date selection
    from_date, to_date = calculator.get_date_selection()

    print("\n ------------------------------------------- \n")

    print("Selected BMU:", bmu)
    print("From date:", from_date)
    print("To date:", to_date)

    print("\n ------------------------------------------- \n")
    # Get and process the data
    output_dir = make_output_directory()

    bmu_bess_data = BESS_fleet.loc[bmu]
    results = calculator.calculate_total_carbon_abated(bmu_bess_data, from_date, to_date, output_dir)
    results = pd.Series(results)

    # os.makedirs(f'{output_dir}/portfolio', exist_ok=True)
    # results.to_excel(f"{output_dir}/portfolio/carbon_abatement_analysis_{from_date}_{to_date}.xlsx", sheet_name='Results')

    print("\n ------------------------------------------- \n")

    save_outputs(results, from_date, to_date, output_dir)



def analyze_multiplt_assets():

    calculator = CarbonAbatementCalculator()

    bmus = BMUs_for_analysis
    print(f"Running analysis on BMUs: {bmus}")

    # PN data starts at 2022-07-09
    from_date = FROM_DATE
    to_date = TO_DATE

    to_date_converted = datetime.strptime(to_date, "%Y-%m-%d")
    from_date_converted = datetime.strptime(from_date, "%Y-%m-%d")


    if (to_date_converted <= from_date_converted):
        raise Exception("to_date must be later than from_date")

    if (to_date_converted > datetime.now()):
        raise Exception("to_date cannot be in the future")


    results = []

    output_dir = make_output_directory()

    for bmu in bmus:
        bmu_bess_data = BESS_fleet.loc[bmu]
        result = calculator.calculate_total_carbon_abated(bmu_bess_data, from_date, to_date, output_dir)
        results.append(result)

    results = pd.DataFrame(results)

    results['Asset'] = results['BMUID'].map(BESS_fleet['Name'])

    print("\n ------------------------------------------- \n")

    save_outputs(results, from_date, to_date, output_dir)

def make_output_directory():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = f"{output_path}/{timestamp}/"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def save_outputs(results, from_date, to_date, output_dir):
    os.makedirs(f'{output_dir}/portfolio', exist_ok=True)
    results.to_excel(f"{output_dir}/portfolio/carbon_abatement_analysis_{from_date}_{to_date}.xlsx", sheet_name='Results')

    if isinstance(results, pd.DataFrame):
        plots = generate_plots(results, from_date, to_date, output_dir)

    print(f"\n Results saved to {output_dir} \n")


def generate_plots(results, from_date, to_date, output_dir):
    plots = []
    # plots.append(box_plot_asset(results, 'carbon_abated_regional (mt CO2/MWh Discharged)', 'Carbon Abated Using Regional Intensity', 'Carbon Abated (mt CO2/MWh Discharged)', 'Total Carbon Abated', from_date, to_date, output_dir))
    plots.append(box_plot_asset(results, 'carbon_abated_national (mt CO2/MWh Discharged)', 'Carbon Abated', 'Carbon Abated (mt CO2/MWh Discharged)', 'Total Carbon Abated', from_date, to_date, output_dir))
    # plots.append(plot_comparison(results, 'CIc_regional (mt CO2/MWh)', 'CId_regional (mt CO2/MWh)', 'Regional Carbon Intensity During Charging and Discharging', 'Average Carbon Intensity (mt CO2/MWh)', 'Average Carbon Intensity During Charging', 'Average Carbon Intensity During Discharging', from_date, to_date, output_dir))
    plots.append(plot_comparison(results, 'CIc_national (mt CO2/MWh)', 'CId_national (mt CO2/MWh)', 'National Carbon Intensity During Charging and Discharging', 'Average Carbon Intensity (mt CO2/MWh)', 'Average Carbon Intensity During Charging', 'Average Carbon Intensity During Discharging', from_date, to_date, output_dir))
    plots.append(plot_comparison(results, 'Ec (MWh)', 'Ed (MWh)', 'Comparison of Energy Charged and Discharged', 'Energy (MWh)', 'Total Energy Charged', 'Total Energy Discharged', from_date, to_date, output_dir))
    return plots


if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    if user_prompted:
        user_prompted_analysis()
    else:
        analyze_multiplt_assets()
