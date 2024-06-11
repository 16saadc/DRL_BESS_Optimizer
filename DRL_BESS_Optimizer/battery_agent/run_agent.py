from battery_agent.data_preprocessor import BatteryAgentDataProcessor
import matplotlib.pyplot as plt
import pandas as pd
from battery_agent.agent import BatteryAgent
from battery_agent.test_analysis import *


data_processor = BatteryAgentDataProcessor()


train_data, test_data = data_processor.get_train_test_data('2018-07-01', '2023-08-15', save_file="ci_data_test.csv")
# train_data, test_data = data_processor.get_train_test_data('2018-07-01', '2023-08-15', window_size=12, save_file="ci_data_12.csv")

test_data_1_year, test_data_q1, test_data_q2, test_data_q4 = data_processor.split_test_data(test_data)

# change test_data to test on different time periods
agent = BatteryAgent(train_data=train_data, test_data=test_data_q1)

# model_name="ddpg_best_keep_cycles"
# abatest more carbon per MWh

# if you have pretrained models, put them in 'battery_agent/models/'
model_name="DDPG_Best"

# agent.train_agent(25, 40, model_name)

test_results, daily_charge, daily_discharge = agent.test_agent(25, 50, model_name)

plot_charge_trend(test_results)
plot_daily_cycles(daily_charge, daily_discharge)
plot_avg_energy_output_comparison(test_results)
plot_energy_over_time(test_results)

full_data = process_test_data(test_results)
result = calculate_total_carbon_abated(full_data)
print(result)
