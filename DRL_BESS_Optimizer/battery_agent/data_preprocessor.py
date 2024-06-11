from carbon_abatement_api.nationalgrid_api_accessor import NationalGridApiAccessor
import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np
import matplotlib.pyplot as plt

class BatteryAgentDataProcessor:
    """
    Data processing class for the Battery Agent.
    """
    def __init__(self):
        self.ng = NationalGridApiAccessor()

    def get_train_test_data(self, from_date, to_date, test_size=0.2, data=None, window_size=24, save_file="ci_data.csv"):
        """
        Get and preprocess train and test data for carbon intensity.

        Parameters
        ----------
        from_date : str
            Start date for the CI data
        to_date : str
            End date for the CI data
        test_size : float, optional
            Proportion of the dataset to be used as test data.
        data : str, optional
            Path to a CSV file containing pre-fetched data.
        window_size : int, optional
            The window size for the forecasts. 24 will get the mean, max, and
            min of the next 24 forecast values
        save_file : str, optional
            File to save the full dataframe

        Returns
        -------
        pd.DataFrame, pd.DataFrame
            Train and test data as pandas DataFrames.
        """

        ci_data=None

        if data != None:
            ci_data = pd.read_csv(data)

        else:
            ci_data = self.ng.get_carbon_intensity(from_date, to_date, 5)

            #save full data
            ci_data.to_csv(save_file)

        ci_data['nationalIntensity'] = ci_data['nationalIntensity'].fillna(method='ffill')

        ci_data['settlementPeriod'] = ci_data['index'] % 48
        ci_data['settlementPeriod'].replace(0, 48, inplace=True)

        rolling_window = ci_data['forecast'].rolling(window=window_size, min_periods=1)

        ci_data['forecast_min'] = rolling_window.min().shift(-window_size)
        ci_data['forecast_max'] = rolling_window.max().shift(-window_size)
        ci_data['forecast_mean'] = rolling_window.mean().shift(-window_size)
        ci_data = ci_data[1:]

        train_ci_data, test_ci_data = train_test_split(ci_data, test_size=test_size, shuffle=False)

        return train_ci_data, test_ci_data

    def get_mean_std(self, train_data):
        """
        Calculate the mean and standard deviation of the nationalIntensity in the train data.

        Parameters
        ----------
        train_data : pd.DataFrame
            The train data

        Returns
        -------
        float, float
            Mean and standard deviation of the nationalIntensity.
        """
        mean_ci = np.mean(np.array(train_data['nationalIntensity']))
        std_dev_ci = np.std(np.array(train_data['nationalIntensity']))
        return mean_ci, std_dev_ci


    def split_test_data(self, df):
        """
        Split the test data for different date ranges

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame containing the test data.

        Returns
        -------
        pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
            DataFrames containing subsets of the data for a year, q1, q2, and q4
        """
        # Create subsets based on date ranges
        df["from"] = pd.to_datetime(df["from"])
        test_data_1_year = df[(df["from"] >= "2022-08-15") & (df["from"] < "2023-08-15")]
        test_data_q4 = df[(df["from"] >= "2022-09-01") & (df["from"] < "2023-01-01")]
        test_data_q1 = df[(df["from"] >= "2023-01-01") & (df["from"] < "2023-04-01")]
        test_data_q2 = df[(df["from"] >= "2023-04-01") & (df["from"] < "2023-08-01")]

        return test_data_1_year, test_data_q1, test_data_q2, test_data_q4

    def plot_ci_distribution(self, train_ci_data):
        plt.hist(train_ci_data['nationalIntensity'], bins=50, edgecolor='black')
        plt.xlabel('National Intensity')
        plt.ylabel('Frequency')
        plt.title('Histogram of National Intensity Values')
        plt.show()
