import gymnasium as gym
from gymnasium import spaces
import numpy as np

class BatteryEnv(gym.Env):

    def __init__(self, initial_charge, max_power, max_charge, min_charge, ci_data, mean_ci, std_dev_ci):
        """
        Custom environment for simulating the charging of a battery energy
        storage system for maximum carbon abatement

        Parameters
        ----------
        initial_charge : float
            The initial state of charge of the battery.
        max_power : float
            The maximum power output of the battery (power capacity).
        max_charge : float
            The maximum charge level of the battery (energy capacity)
        min_charge : float
            The minimum charge level of the battery (0)
        ci_data : dict
            Dictionary containing data related to carbon intensity
        mean_ci : float
            Mean value of training carbon intensity data for normalization.
        std_dev_ci : float
            Standard deviation of training carbon intensity data for normalization.
        """

        super(BatteryEnv, self).__init__()
        self.num_cycles = 2
        self.penalty = -50

        self.mean_ci = mean_ci
        self.std_dev_ci = std_dev_ci

        self.energy_out = 0

        self.max_power = max_power
        self.min_charge = min_charge
        self.max_charge = max_charge
        self.duration = max_charge / max_power

        self.carbon_intensity_data = np.array(ci_data['nationalIntensity'])
        self.forecast_min = np.array(ci_data['forecast_min'])
        self.forecast_max = np.array(ci_data['forecast_max'])
        self.forecast_mean = np.array(ci_data['forecast_mean'])
        self.settlement_periods = np.array(ci_data['settlementPeriod'])

        self.current_timestep = 0

        self.daily_charge = 0.0
        self.daily_discharge = 0.0

        self.initial_charge = initial_charge
        self.charge = initial_charge / max_charge
        self.reward = 0
        self.sp = self.settlement_periods[0]

        self.actions = []

        # Define action space to be a number between -max_power/2 to max_power/2 (since its MW * 0.5 hrs)
        self.action_space = spaces.Box(low=-1, high=1, shape=(1,))

        # charge, intensity, forecastmin, forecastmax, forecastmean, cycle c, cycle d
        self.observation_space = spaces.Box(low=np.array([ 0, -5, -5, -5, -5, -1, -1]),
                                            high=np.array([1,  5, 5, 5, 5, 1, 1]))


        curr_ci = (self.carbon_intensity_data[0] - self.mean_ci) / self.std_dev_ci
        fcast_min = (self.forecast_min[0] - self.mean_ci) / self.std_dev_ci
        fcast_max = (self.forecast_max[0] - self.mean_ci) / self.std_dev_ci
        fcast_mean = (self.forecast_mean[0] - self.mean_ci) / self.std_dev_ci

        self.state = np.array([self.charge, curr_ci, fcast_min, fcast_max, fcast_mean, self.daily_charge/2, self.daily_discharge/2], dtype=np.float32)


    def step(self, action):
        """
        Simulate one time step in the environment.

        Parameters
        ----------
        action : float
            The action to be taken, ranging from -1 to 1.

        Returns
        -------
        tuple
            A tuple containing the new state, reward, done flag, and additional info.
        """
        charge, ci, fcast_min, fcast_max, fcast_mean, daily_charge, daily_discharge = self.state

        if self.sp == 1:
            self.daily_charge = 0.0
            self.daily_discharge = 0.0

        # get number of cycles of this action for update later
        # action_cycles = (action/2) / self.duration

        print("action norm: ", action)

        # un_normalize action for 0.5 hrs
        self.energy_out = action * self.max_power / 2

        energy_out = self.energy_out

        action_cycles = self.energy_out / self.max_charge

        print("action_cycles: ", action_cycles)

        print("SP: ", self.sp)
        print("full action: ", energy_out)

        self.actions.append(energy_out)

        done = False

        # Check if the action would result in a battery charge outside the valid range, and end the episode if it does
        charge = charge * self.max_charge

        if charge - energy_out > self.max_charge:
            self.energy_out = charge - self.max_charge

            charge = self.max_charge
            self.charge=1.0
            return self.out_of_bounds_end()

        elif charge - energy_out < self.min_charge:
            # clip the action to remove only charge amount
            self.energy_out = charge - self.min_charge

            charge = self.min_charge
            self.charge=0.0
            return self.out_of_bounds_end()

        curr_reward = 0

        # update state values based on the action
        # Discharging action
        if energy_out > 0:

          # if we go above 2 discharge cycles penalize
          self.daily_discharge += action_cycles

          if self.daily_discharge > self.num_cycles:
              self.energy_out=0
              return self.out_of_bounds_end()

          curr_reward = self.calculate_discharge_reward(energy_out, ci, fcast_mean, fcast_max)
          self.reward = float(curr_reward)

        # Charging action
        else:
          energy_out = -1 * energy_out # make positive

          #subtracting a negative
          self.daily_charge -= action_cycles

          # if we go above 2 charge cycles penalize
          if self.daily_charge > self.num_cycles:
              self.energy_out=0
              return self.out_of_bounds_end()

          curr_reward = self.calculate_charge_reward(energy_out, ci, fcast_mean, fcast_min)
          self.reward = float(curr_reward)

        # update charge
        self.charge = self.charge - (action / 2)

        if self.sp == 48:
          # self.reward += 50
          # reward reaching end of day based on amount charged in that day
          self.reward += self.get_cycles_reward(self.daily_charge)
          self.reward += self.get_cycles_reward(self.daily_discharge)
          self.state = self.get_next_state()
          done = True
          return self.state, self.reward, done, False, {}

        self.state = self.get_next_state()
        print("state: ", self.state)
        print("timestep: ", self.current_timestep)
        return self.state, self.reward, done, False, {}

    def out_of_bounds_end(self):
        """
        Handle the scenario where the action results in state of charge going
        out of bounds or exceeding max charge cycles

        Returns
        -------
        tuple
            The next state, penalty reward, done flag, and additional info.
        """
        self.reward = self.penalty
        done=True
        self.state = self.get_next_state()
        return self.state, self.reward, done, False, {}

    def get_next_state(self):
        """
        Compute the next state of the environment.

        Returns
        -------
        np.array
            The next state as an array.
        """
        self.current_timestep += 1

        self.sp = self.settlement_periods[self.current_timestep]
        next_ci = (self.carbon_intensity_data[self.current_timestep] - self.mean_ci) / self.std_dev_ci
        fcast_min = (self.forecast_min[self.current_timestep] - self.mean_ci) / self.std_dev_ci
        fcast_max = (self.forecast_max[self.current_timestep] - self.mean_ci) / self.std_dev_ci
        fcast_mean = (self.forecast_mean[self.current_timestep] - self.mean_ci) / self.std_dev_ci

        state = np.array([self.charge, next_ci, fcast_min, fcast_max, fcast_mean, self.daily_charge/2, self.daily_discharge/2], dtype=np.float32)
        return state

    def get_cycles_reward(self, cycles):
        return cycles**10
        # if cycles > 1.8:
        #     return 300
        # elif cycles > 1.5:
        #     return 200
        # elif cycles > 1.3:
        #     return 100
        # elif cycles > 1.1:
        #     return 50
        # elif cycles > 0.8:
        #     return 20
        # return 0

    def calculate_charge_reward(self, energy_out, ci, fcast_mean, fcast_min):
      curr_reward = 0

      diff = ci - fcast_mean
      if diff > 0:
        # higher CI than fcast mean, so negative reward
        curr_reward -= energy_out * 5
      else:
        # negative diff, so positive reward
        curr_reward += energy_out
      if ci <= fcast_min:
        # extreme positive reward
        curr_reward += energy_out * 5

      return curr_reward

    def calculate_discharge_reward(self, energy_out, ci, fcast_mean, fcast_max):
      curr_reward = 0
      diff = ci - fcast_mean

      if diff < 0:
        curr_reward -= energy_out * 5
      # if above average
      else:
        curr_reward += energy_out
      if ci >= fcast_max:
        curr_reward += energy_out * 5

      return curr_reward

    def reset(self, seed=42, options=None):
        """
        Reset the environment to its initial state.

        Parameters
        ----------
        seed : int, optional
            The random seed for the environment.
        options : any, optional
            Additional options for resetting the environment.

        Returns
        -------
        np.array, dict
            The initial state and info
        """
        super().reset(seed=seed)
        # Reset to initial state
        # already increment timestep in get_next_state

        self.reward = 0.0

        self.sp = self.settlement_periods[self.current_timestep]

        # if we reach a new day, reset the cycles
        # if self.sp == 1:
        # always resetting the cycles allows the agent to learn to get closer to 2
        self.daily_charge = 0.0
        self.daily_discharge = 0.0

        ci = (self.carbon_intensity_data[self.current_timestep] - self.mean_ci) / self.std_dev_ci
        fcast_min = (self.forecast_min[self.current_timestep] - self.mean_ci) / self.std_dev_ci
        fcast_max = (self.forecast_max[self.current_timestep] - self.mean_ci) / self.std_dev_ci
        fcast_mean = (self.forecast_mean[self.current_timestep] - self.mean_ci) / self.std_dev_ci

        self.state = np.array([self.charge, ci, fcast_min, fcast_max, fcast_mean, self.daily_charge/2, self.daily_discharge/2], dtype=np.float32)
        return self.state, {}
