import pandas as pd
from sklearn.model_selection import train_test_split
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3 import DDPG, SAC, TD3, PPO, A2C
from stable_baselines3.common.callbacks import EvalCallback
import torch as th
import wandb
from wandb.integration.sb3 import WandbCallback
from stable_baselines3.common.monitor import Monitor
from battery_agent.data_preprocessor import BatteryAgentDataProcessor
from battery_agent.battery_env import BatteryEnv

class BatteryAgent:
    """
    Class for training and testing battery agent models.

    Parameters
    ----------
    train_data : pd.DataFrame
        Training data for the agent.
    test_data : pd.DataFrame
        Testing data for the agent.
    """

    def __init__(self, train_data, test_data):
        self.train_data = train_data
        self.test_data = test_data

        data_processor = BatteryAgentDataProcessor()

        self.mean_ci, self.std_dev_ci = data_processor.get_mean_std(train_data)

    def make_env(self, max_power, max_charge):
        """
        Create an environment for the battery agent. Used when making vectorized
        envs for parallel training algorithms like PPO or A2C.

        Parameters
        ----------
        max_power : float
            Battery's power capacity
        max_charge : float
            Battery's energy capacity

        Returns
        -------
        BatteryEnv
            The training environment.
        """
        config = {
            "policy_type": 'MlpPolicy',
            "total_timesteps": len(self.train_data)-1000,
            # "batch_size": 512,
            "gamma": 0.95,
            # "learning_rate: 0.001
        }

        train_env = BatteryEnv(
            initial_charge=max_charge/2,
            max_power=max_power,
            max_charge=max_charge,
            min_charge=0,
            ci_data=self.train_data,
            mean_ci=self.mean_ci,
            std_dev_ci=self.std_dev_ci)

        return train_env

    def train_agent(self, max_power, max_charge, model_save_name):
        """
        Train the battery agent. Edit the algorithm called for training if
        needed.

        Parameters
        ----------
        max_power : float
            Battery's power capacity
        max_charge : float
            Battery's energy capacity
        model_save_name : str
            The file name to save the trained model to
        """

        config = {
            "policy_type": 'MlpPolicy',
            "total_timesteps": len(self.train_data)-1000,
            # "batch_size": 512,
            "gamma": 0.91,
            # "learning_rate: 0.001
        }

        train_env = BatteryEnv(
            initial_charge=max_charge/2,
            max_power=max_power,
            max_charge=max_charge,
            min_charge=0,
            ci_data=self.train_data,
            mean_ci=self.mean_ci,
            std_dev_ci=self.std_dev_ci)

        check_env(train_env)

        # train_env = make_vec_env(self.make_env, n_envs=4, env_kwargs={"max_power": max_power, "max_charge": max_charge})

        run = wandb.init(
            project="batteryagent_final",
            config=config,
            sync_tensorboard=True,
        )

        # policy_kwargs = dict(activation_fn=th.nn.ReLU,
        #              net_arch=dict(pi=[200, 100], qf=[200, 100]))

        model = DDPG(config['policy_type'],
                     train_env,
                     verbose=1,
                     # learning_starts=500,
                    #  action_noise=action_noise,
                     seed=42,
                     # learning_rate=config['learning_rate'],
                     # policy_kwargs=policy_kwargs,
                     # batch_size=config['batch_size'],
                     # buffer_size=100000,
                     gamma=config['gamma'],
                     tensorboard_log=f"./final/{run.id}")


        # Train the model and calculate the reward.
        model.learn(total_timesteps=config['total_timesteps'],
                    callback=WandbCallback(
                        gradient_save_freq=100,
                        model_save_path=f"models/{run.id}",
                        model_save_freq=100,
                        verbose=2))

        model.save(f"battery_agent/models/{model_save_name}")

        # wandb.finish()

    def test_agent(self, max_power, max_charge, model_name):
        """
        Test the trained battery management agent.

        Parameters
        ----------
        max_power : float
            Battery's power capacity
        max_charge : float
            Battery's energy capacity
        model_name : str
            The name of the saved model to use for testing

        Returns
        -------
        pd.DataFrame, list, list
            A DataFrame containing test results,
            a list of daily charge cycles during testing,
            and a list of daily discharge cycles during testing
        """
        env = BatteryEnv(
            initial_charge=0,
            max_power=max_power,
            max_charge=max_charge,
            min_charge=0,
            ci_data=self.test_data,
            mean_ci=self.mean_ci,
            std_dev_ci=self.std_dev_ci)

        model = DDPG.load(f"battery_agent/models/{model_name}")

        charge_values = []
        daily_charge = []
        daily_discharge = []

        obs, _ = env.reset()
        total_reward = 0
        energy_out = []
        for _ in range(len(self.test_data)):
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, info, _ = env.step(action)
            total_reward += reward

            if env.current_timestep >= len(self.test_data)-1:
              break

            energy_out.append(env.energy_out)

            charge_values.append(float(env.charge))
            # reward_values.append(env.reward)
            if env.sp == 48:
                  daily_charge.append(float(env.daily_charge))
                  daily_discharge.append(float(env.daily_discharge))

            if done:
                obs, _i = env.reset()

        test_results = self.test_data
        test_results.reset_index(drop=True, inplace=True)
        test_results['energyOut'] = pd.Series(energy_out).astype(float)
        test_results['charge'] = pd.Series(charge_values).astype(float)

        return test_results, daily_charge, daily_discharge
