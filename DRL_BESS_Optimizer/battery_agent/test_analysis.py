import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np

font_title = FontProperties()
font_title.set_size('x-large')
font_title.set_weight('bold')

font_axes = FontProperties()
font_axes.set_size('large')


def plot_charge_trend(results):
  window_size=48
  charge_values = results['charge'].rolling(window=window_size).mean()
  plt.figure(figsize=(10, 6))
  plt.plot(charge_values, color='blue', linestyle='-')
  plt.title("State of Charge Values over Time")
  plt.xlabel("Timestep")
  plt.ylabel("State of Charge (% of Energy Capacity)")
  plt.grid(True, which='both', linestyle='--', linewidth=0.5)
  plt.tight_layout()
  plt.show()

# 2. Plot for daily_charge
def plot_daily_cycles(daily_charge, daily_discharge):
  window_size=7
  daily_charge = pd.Series(daily_charge).rolling(window=window_size).mean()
  daily_discharge = pd.Series(daily_discharge).rolling(window=window_size).mean()
  plt.figure(figsize=(10, 6))
  plt.plot(daily_charge, color='green', linestyle='-', label="Daily Charge")
  plt.plot(daily_discharge, color='red', linestyle='-', label="Daily Discharge")
  plt.title("Daily Charge and Discharge Cycles over Time")
  plt.xlabel("Time (days)")
  plt.ylabel("Daily Charge and Discharge Cycles")
  plt.legend(loc="upper left")
  plt.xticks([])
  plt.grid(True, which='both', linestyle='--', linewidth=0.5)
  plt.tight_layout()
  plt.show()

def plot_avg_energy_output_comparison(df, real_file=None):

    fig, ax1 = plt.subplots(figsize=(12, 6))

    real_df=None
    average_power_output_real=None
    if real_file:
        real_df = pd.read_excel(real_file)

        average_power_output_real = real_df.groupby('settlementPeriod')['energyOut'].mean()
        average_power_output_real.plot(kind='bar', alpha=0.7, color='skyblue', edgecolor='dodgerblue', label='Power Output', ax=ax1)

    # Group by 'settlementPeriod' and calculate mean energy output
    average_power_output = df.groupby('settlementPeriod')['energyOut'].mean()

    average_n_intensity = df.groupby('settlementPeriod')['nationalIntensity'].mean()

    # Plot the average energy output per settlement period
    average_power_output.plot(kind='bar', alpha=0.7, color='lightgreen', edgecolor='green', label='Energy Output', ax=ax1)


    # Set gridlines
    ax1.grid(color='gray', linestyle='--', linewidth=0.1)

    # Set the y-axis label
    ax1.set_ylabel('Average Energy Output (MWh)', fontsize=12, fontproperties=font_axes)

    # Set the second y-axis and plot the average regional and national intensities
    ax2 = ax1.twinx()
    # ax2.set_ylim(0, 350)
    ax2.plot(average_n_intensity, color='blue', linewidth=1.2, linestyle='--', alpha=0.7, label='National Intensity')

    # Set the y-axis label for the intensities
    ax2.set_ylabel('Carbon Intensity (g CO2/MWh)', fontsize=12, fontproperties=font_axes)

    # Set the title and x-axis label
    ax1.set_title("Average Energy Output Per Settlement Period", fontsize=14, fontproperties=font_title)
    ax1.set_xlabel('Settlement Period', fontsize=12, fontproperties=font_axes)

    if real_file:
        custom_lines = [Line2D([0], [0], color='skyblue', lw=4),
                        Line2D([0], [0], color='lightgreen', lw=4),
                        Line2D([0], [0], color='blue', lw=2, linestyle='--')]

        ax1.legend(custom_lines, ['Bloxwich Energy Output', 'Agent Energy Output', 'National Carbon Intensity'], loc='upper left')

    else:
        custom_lines = [Line2D([0], [0], color='lightgreen', lw=4),
                        Line2D([0], [0], color='blue', lw=2, linestyle='--')]

        ax1.legend(custom_lines, ['Energy Output', 'National Carbon Intensity'], loc='upper left')

    plt.xticks(rotation=45, ha='right')

    return fig

# Plot the daily energy output of test results
def get_energy_values(df):
    df['from'] = pd.to_datetime(df['from'])

    # Separate the positive and negative energyOut values
    df['energy_discharged'] = df['energyOut'].apply(lambda x: x if x > 0 else 0)
    df['energy_charged'] = df['energyOut'].apply(lambda x: x if x < 0 else 0)

    # Group by day and sum the positive and negative values
    daily_energy = df.groupby(df['from'].dt.date).agg({
        'energy_discharged': 'sum',
        'energy_charged': 'sum'
    }).reset_index()

    return daily_energy


def plot_energy_over_time(test_results):
    daily_energy = get_energy_values(test_results)

    plt.figure(figsize=(10, 6))
    plt.plot(daily_energy['from'], daily_energy['energy_discharged'], linestyle='-', color='green', label='Energy Discharged')
    plt.plot(daily_energy['from'], daily_energy['energy_charged'], linestyle='-', color='red', label='Energy Charged')

    plt.title("Daily Energy Charged vs. Discharged")
    plt.xlabel("Date")
    plt.ylabel("Energy (MWh)")
    plt.legend(loc="upper left")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()

    plt.show()

def process_test_data(data):
  data['energyCharged'] = data['energyOut'].apply(lambda x: -x if x < 0 else None)
  data['energyDischarged'] = data['energyOut'].apply(lambda x: x if x > 0 else None)

  if data['energyCharged'].isnull().all() or data['energyDischarged'].isnull().all():
      data['energyCharged'] = 0.00001
      data['energyDischarged'] = 0.00001
  return data

def get_weighted_average_ci(full_data):
    """
    Calculates an average value of the national carbon intensity across all PNs, with
    the energyCharged or energyDischarged for each PN as weights for each intensity value.

    Parameters
    ----------
    full_data : pd.DataFrame
        the physical notification data with regional and national
        carbon intensity values for each PN

    Returns
    -------
    CIc_national
        the weighted average national carbon intensity during times the BMU charged
    CId_national
        the weighted average national carbon intensity during times the BMU discharged
    """

    CIc_national = np.average(full_data.loc[full_data['energyCharged'].notnull(), 'nationalIntensity'], weights=full_data.loc[full_data['energyCharged'].notnull(), 'energyCharged']) / 0.001
    CId_national = np.average(full_data.loc[full_data['energyDischarged'].notnull(), 'nationalIntensity'], weights=full_data.loc[full_data['energyDischarged'].notnull(), 'energyDischarged']) / 0.001
    return CIc_national, CId_national

def calculate_total_carbon_abated(full_data, from_date="2023-01-01", to_date="2023-01-10", output_dir=""):
    """
    Calculates the total carbon abated by a BMU between the selected date, not inclusive of the to_date

    Makes calls to NGESO and BMRS classes to get their respective data and merges them

    Calculates the carbon abated using this formula:

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
        the carbon_abated_national, CIc_national, CId_national, energyCharged, energyDischarged, Ec-Ed, CId-CIc

    """


    CIc_national, CId_national = get_weighted_average_ci(full_data)

    energyCharged = full_data['energyCharged'].sum()
    energyDischarged = full_data['energyDischarged'].sum()

    carbon_abated_national = ((CId_national - CIc_national) * energyDischarged - ((energyCharged - energyDischarged) * CIc_national)) / energyDischarged

    print(carbon_abated_national)

    for column in full_data.columns:
        if isinstance(full_data[column].dtype, pd.DatetimeTZDtype):
            full_data[column] = full_data[column].dt.tz_localize(None)

    result = {
        "carbon_abated_national (mt CO2/MWh Discharged)": carbon_abated_national / 1e6,
        "CIc_national (mt CO2/MWh)": CIc_national / 1e6,
        "CId_national (mt CO2/MWh)": CId_national / 1e6,
        "Ec (MWh)": energyCharged,
        "Ed (MWh)": energyDischarged,
        "Ec-Ed": energyCharged - energyDischarged,
        "CId-CIc": (CId_national / 1e6) - (CIc_national / 1e6)
    }

    return result
