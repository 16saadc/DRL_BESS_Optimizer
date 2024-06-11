import pandas as pd
import matplotlib.pyplot as plt
from carbon_abatement_api.config import UK_regions_map, BESS_fleet
from matplotlib.font_manager import FontProperties
import numpy as np


font_title = FontProperties()
font_title.set_size('x-large')
font_title.set_weight('bold')

font_axes = FontProperties()
font_axes.set_size('large')

font_legend = FontProperties()

def box_plot_asset(df, y, title, ylabel, legend_val, from_date, to_date, output_dir):
    labels = df['Asset'].values
    x = np.arange(len(labels))
    width = 0.3

    fig, ax = plt.subplots(figsize=(15,7))

    rects1 = ax.bar(x, df[y].values, width, label=legend_val, edgecolor='black', linewidth=0.7, color='lightsteelblue')

    ax.set_ylabel(ylabel, fontproperties=font_axes)
    ax.set_title(title + f" {from_date} - {to_date}", fontproperties=font_title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    legend = ax.legend(frameon=False)
    legend.set_bbox_to_anchor((1, 1))
    ax.axhline(0, color='black', linewidth=0.3)  # Draws line on y=0

    fig.tight_layout()

    fig.savefig(f"{output_dir}/portfolio/{title}_{from_date}_{to_date}.png")

    return fig

def plot_comparison(df, y1, y2, title, ylabel, y1_label, y2_label, from_date, to_date, output_dir):
    labels = df['Asset'].values
    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(15,7))

    rects1 = ax.bar(x - width/2, df[y1].values, width, label=y1_label, edgecolor='black', linewidth=0.7, color='lightsteelblue')
    rects2 = ax.bar(x + width/2, df[y2].values, width, label=y2_label, edgecolor='black', linewidth=0.7, color='cornflowerblue')

    ax.set_ylabel(ylabel, fontproperties=font_axes)
    ax.set_title(title + f" {from_date} - {to_date}", fontproperties=font_title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    legend = ax.legend(frameon=False)
    legend.set_bbox_to_anchor((1, 1))
    ax.axhline(0, color='black', linewidth=0.3)  # Draws line on y=0

    fig.tight_layout()

    fig.savefig(f"{output_dir}/portfolio/{title}_{from_date}_{to_date}.png")

    return fig



def plot_comparison_four_bars(df, y1, y2, y3, y4, title, y_label, from_date, to_date, output_dir):
    labels = df['Asset'].values
    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(15,7))

    rects1 = ax.bar(x - 3*width/2, df[y1].values, width, label=y1, edgecolor='black', linewidth=0.7, color='lightsteelblue')
    rects2 = ax.bar(x - width/2, df[y2].values, width, label=y2, edgecolor='black', linewidth=0.7, color='cornflowerblue')
    rects3 = ax.bar(x + width/2, df[y3].values, width, label=y3, edgecolor='black', linewidth=0.7, color='silver')
    rects4 = ax.bar(x + 3*width/2, df[y4].values, width, label=y4, edgecolor='black', linewidth=0.7, color='slategrey')

    ax.set_ylabel(y_label)
    ax.set_title(title + f" {from_date} - {to_date}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    legend = ax.legend(frameon=False)
    legend.set_bbox_to_anchor((1, 1))
    ax.axhline(0, color='black', linewidth=0.3)  # Draws line on y=0

    fig.tight_layout()

    fig.savefig(f"{output_dir}/portfolio/{title}_{from_date}_{to_date}.png")

    return fig

def plot_avg_energy_output(df, ci_data, bmu_id, bmu_bess_data, from_date, to_date):
    # Group by 'settlementPeriod' and calculate mean power output
    average_power_output = df.groupby('settlementPeriod')['energyOut'].mean()

    # average_r_intensity = df.groupby('settlementPeriod')['regionalIntensity'].mean()
    average_n_intensity = ci_data.groupby('settlementPeriod')['nationalIntensity'].mean()

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot the average power output per settlement period
    average_power_output.plot(kind='bar', alpha=0.7, color='skyblue', edgecolor='dodgerblue', label='Power Output', ax=ax1)

    # Set gridlines
    ax1.grid(color='gray', linestyle='--', linewidth=0.1)

    # Set the y-axis label
    ax1.set_ylabel('Average Energy Output (MWh)', fontsize=12, fontproperties=font_axes)

    # Set the second y-axis and plot the average regional and national intensities
    ax2 = ax1.twinx()
    # ax2.set_ylim(0, 350)
    # ax2.plot(average_r_intensity, color='red', linewidth=1.2, linestyle='--', alpha=0.7, label='Regional Intensity')
    ax2.plot(average_n_intensity, color='blue', linewidth=1.2, linestyle='--', alpha=0.7, label='National Intensity')

    # Set the y-axis label for the intensities
    ax2.set_ylabel('Carbon Intensity (g CO2/MWh)', fontsize=12, fontproperties=font_axes)

    # Set the title and x-axis label
    ax1.set_title(f"Average Energy Output Per Settlement Period for {bmu_bess_data['Name']}\n{from_date} - {to_date}", fontsize=14, fontproperties=font_title)
    ax1.set_xlabel('Settlement Period', fontsize=12, fontproperties=font_axes)

    # Create a custom legend
    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='skyblue', lw=4),
                    Line2D([0], [0], color='blue', lw=2, linestyle='--')]
    ax1.legend(custom_lines, ['Energy Output', 'National Carbon Intensity'], loc='upper left')

    # Add a text box with the asset overview
    region = bmu_bess_data['Region']
    regionName = UK_regions_map[region]
    asset_overview = f"Region: {regionName}\nCapacity (MW): {bmu_bess_data['MW']}\nEnergy capacity (MWh): {bmu_bess_data['MWh']}\nDuration (hr): {bmu_bess_data['MWh'] / bmu_bess_data['MW']}"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.5, 0.98, asset_overview, fontsize=8, ha='center', va='top', transform=ax1.transAxes, bbox=props)

    plt.xticks(rotation=45, ha='right')

    return fig
