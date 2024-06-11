import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress

"""
Utility file for running analysis on all UK BESS assets.
Additionally, add values for the agent's results to plot over the real BESS results
"""

# agent results
agent_durations = [1.12, 1, 2, 2.14, 1.51, 1]
agent_carbon_abated_values = [0.0531, 0.052, 0.053, 0.0528, 0.0532, 0.0528]


# file path for real asset results
file_path = 'carbon_abatement_api/outputs/all_bess_q2/portfolio/carbon_abatement_analysis_2023-04-01_2023-07-01.xlsx'
df = pd.read_excel(file_path)

# get >1 hr duration assets
df = df[df['Duration'] >= 1]

def remove_outliers(df, column_name):
    Q1 = df[column_name].quantile(0.25)
    Q3 = df[column_name].quantile(0.75)
    IQR = Q3 - Q1

    # remove outliers
    df_no_outliers = df[~((df[column_name] < (Q1 - 1.5 * IQR)) | (df[column_name] > (Q3 + 1.5 * IQR)))]

    return df_no_outliers

# remove outliers
df_no_outliers = remove_outliers(df, 'carbon_abated_national (mt CO2/MWh Discharged)')


# For the scatter plots
legend_elements = [plt.Line2D([0], [0], linestyle='None', marker='o', color='blue', label='Real Assets', markersize=10, markerfacecolor='blue'),
                   plt.Line2D([0], [0], linestyle='None', marker='o', color='red', label='Battery Agent', markersize=10, markerfacecolor='red')]

# duration vs. carbon abated
plt.figure(figsize=(10, 6))
sns.regplot(x=df_no_outliers['Duration'], y=df_no_outliers['carbon_abated_national (mt CO2/MWh Discharged)'], scatter_kws={'color': 'blue'})

for duration, carbon_abated in zip(agent_durations, agent_carbon_abated_values):
    plt.scatter(duration, carbon_abated, color='red')

plt.title("Carbon Abated vs. Battery Duration \n 04-2023 to 07-2023")
plt.xlabel("Battery Duration (hours)")
plt.ylabel("Carbon Abated (mt CO2/MWh Discharged)")
plt.legend(handles=legend_elements)
plt.show()

plt.hist(df_no_outliers['carbon_abated_national (mt CO2/MWh Discharged)'], bins=30, color='blue', edgecolor='black', label='Real Assets')

# Add vertical lines for the agent
for index, carbon_abated in enumerate(agent_carbon_abated_values):
    plt.axvline(carbon_abated, color='red', linestyle='dashed', linewidth=1)
    # plt.text(carbon_abated, -0.05, f'Agent {index+1}', rotation=0, verticalalignment='top', horizontalalignment='right', fontsize=6, color='red')


hist_legend_elements = [plt.Line2D([0], [0], color='blue', label='Real Assets'),
                        plt.Line2D([0], [0], linestyle='--', color='red', label='Battery Agent')]


plt.title("Carbon Abatement Distribution of BESS \n 04-2023 to 07-2023")
plt.xlabel("Carbon Abated (mt CO2/MWh Discharged)")
plt.ylabel("Number of BESS")
plt.legend(handles=hist_legend_elements)
plt.show()
