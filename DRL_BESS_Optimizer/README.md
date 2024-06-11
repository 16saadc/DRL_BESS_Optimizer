# Deep Reinforcement Learning to Enhance Carbon Abatement Potential of Battery Energy Storage Systems

## Project Objectives

This project aims to
1.	Benchmark carbon abated by BESS assets using status quo trading strategies
2.  Provide a DRL solution that learns optimal charging strategies for BESS resulting in increased carbon abatement
3.  Provide tools for analysis of the API and agent's results

The final report and presentation can be found in ```reports/```

Weights & Biases experiment tracking can be found at https://wandb.ai/irp-cs1622/projects


## About the code

The code in this repository is separated into two packages:

```carbon_abatement_api```: This is the API for calculating carbon abated by BESS. It provides the option to analyze a single asset, or hundreds of assets at a time

```battery_agent```: This package contains code to create a battery model, fetch training data, and train and test a DRL agent for maximal carbon abatement


## Running the code

Run all code from the root directory of the project

### Install requirements

This project requires python3 >= 3.8.9

Install the necessary packages by running 
```pip install -e .```


### Carbon Abatement API

Modify the assets, time frame you want to analyse, and your output directory in ```carbon_abatement_api/config.py```

```BESS_fleet.xlsx``` contains the whole BESS fleet from https://www.bessanalytics.com/fleet retrieved in 08-2023

Or, if you would like to be prompted by the command line for your inputs, set ```user_prompted = True```. However, this limits to analysing 1 asset at a time.



#### Run the analysis:
``` python carbon_abatement_api/main.py ```

After the analysis is run, the analysis data and plots will be put into your specified output directory. This will contain:
- Individual asset results
    - Raw data: PNs, carbon intensity, energyOut per PN, etc.
    - Plots: average energy output per SP vs average CI per SP
- Portfolio Results
    - Data: Aggregated results of all assets analysed
    - Plots: Comparative figures displaying results across different assets


#### Other analysis:

To generate plots showing the carbon abatement distribution, and the carbon abatement vs duration of several assets, run:

```python carbon_abatement_api/full_bess_analysis.py```

Go into the file and modify the file path to the xlsx data generated for the portfolio you want to analyse.
You can also put the agent's results in the top lists, or leave them empty if you do not have agent results.



### Battery Agent

```battery_agent/run_agent.py``` contains a basic script to preprocess data, create a battery env, train an agent, and test an agent.
The data used for the best model is in ```ci_data.csv```, but new data can be retrieved with different parameters if needed.

If you would like to modify which algorithm is being used and its hyperparameters, modify directly in ```battery_agent/agent.py```

If you would like to modify the environment, such as the observation space, reward function, or transition function, modify in ```battery_agent/battery_env.py```
