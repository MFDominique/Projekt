#Importing standard libraries
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  
from windpowerlib import WindPowerPlant
from pvlib import pvgis


def main():
    startdate = np.datetime64("2024-01-01T00")
    days_to_simulate = 1
    location = "FRIEDBERG"
    # location = "ST_NAZAIRE"

    # Start Simulationloop
    simulation_loop(location, startdate, days_to_simulate)


def simulation_loop(location, startdate, days=1):
    for i in range(days * 24):
        current_time = startdate + np.timedelta64(i, 'h')
        #f or each hour in every to be simulated day run simulation
        power_output_microgrid = simulation_of_a_microgrid(location, current_time)
        power_usage_household = simulation_of_a_houshold(location, current_time)
        energy_delta_battery = simulation_of_a_battery_storage(power_output_microgrid -
                                                               power_usage_household, location,
                                                               current_time)
        energy_imported_cost = importing_of_energy_from_the_grid(power_output_microgrid -
                                                                 power_usage_household -
                                                                 energy_delta_battery, location,
                                                                 current_time)
        visualize_results(power_output_microgrid, power_usage_household, energy_delta_battery,
                          energy_imported_cost, current_time, location)
    visualize_results(0,0,0,
                      0,0,0, True)


def simulation_of_a_microgrid(location, current_time):
    efficiency_of_microgrid = 0.9 # 90%
    maximum_power_output = 10 # kW
    power_output = 0 #kW

    # Use current_time, maximum_power_output and efficiency_of_microgrid
    # together with data from pvgis to define current power_output
    #
    # Use PVLib for your calculations: https://moodle-ext.thm.de/mod/url/view.php?id=7899
    # Extend for the use of a location
    #
    ## Your Code Here


    ##
    return power_output



def simulation_of_a_household(current_time):
    power_draw = 0  # kW

    # Load data from a CSV file
    data = pd.read_csv('C:/Users/domin/Downloads/CESI-THM-Project1-Load-Profile.csv', delimiter=';')

    # Columns of interest for the residential building DE_KN_residential4
    columns_of_interest = [
        'cet_cest_timestamp',
        'DE_KN_residential4_dishwasher',
        'DE_KN_residential4_ev',
        'DE_KN_residential4_freezer',
        'DE_KN_residential4_grid_export',
        'DE_KN_residential4_grid_import',
        'DE_KN_residential4_heat_pump',
        'DE_KN_residential4_pv',
        'DE_KN_residential4_washing_machine',
        'DE_KN_residential4_refrigerator'
    ]

    # Select only the columns of interest
    residential_data = data[columns_of_interest]

    # Convert timestamps to datetime objects
    residential_data['cet_cest_timestamp'] = pd.to_datetime(residential_data['cet_cest_timestamp'], errors='coerce', utc=True)

    # Fill missing values with zeros (if necessary)
    residential_data.fillna(0, inplace=True)

    # Define the function to calculate consumption
    def calculate_total_consumption(row):
        total_consumption = (
            row['DE_KN_residential4_dishwasher'] +
            row['DE_KN_residential4_ev'] +
            row['DE_KN_residential4_freezer'] +
            row['DE_KN_residential4_heat_pump'] +
            row['DE_KN_residential4_washing_machine'] +
            row['DE_KN_residential4_refrigerator']
        )

        # Adjust consumption by PV production and grid import/export
        net_consumption = total_consumption + row['DE_KN_residential4_grid_import'] - row['DE_KN_residential4_grid_export'] - row['DE_KN_residential4_pv']
        return net_consumption

    # Apply the calculation function to each row of the DataFrame
    residential_data['total_consumption_kwh'] = residential_data.apply(calculate_total_consumption, axis=1)

    # Add columns for hour, day of the week, and month
    residential_data['hour'] = residential_data['cet_cest_timestamp'].dt.hour
    residential_data['day_of_week'] = residential_data['cet_cest_timestamp'].dt.dayofweek
    residential_data['month'] = residential_data['cet_cest_timestamp'].dt.month

    # Function to adjust consumption based on hourly, daily, and seasonal profiles
    def adjusted_consumption(hour, day_of_week, month, base_consumption):
        # Consumption profiles based on the hour (expressed as a multiplicative factor)
        hourly_profile = {
            'night': 0.5,
            'morning': 1.2,
            'afternoon': 1.0,
            'evening': 1.5
        }

        # Consumption profiles based on the day of the week
        weekday_profile = {
            'weekday': 1.0,
            'weekend': 1.1
        }

        # Consumption profiles based on the season (expressed as a multiplicative factor)
        seasonal_profile = {
            'winter': 1.3,
            'spring': 1.0,
            'summer': 0.8,
            'autumn': 1.1
        }

        # Determine the time of day profile
        if 0 <= hour < 6:
            time_of_day = 'night'
        elif 6 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 18:
            time_of_day = 'afternoon'
        else:
            time_of_day = 'evening'

        # Determine the day type profile
        if day_of_week in [0, 1, 2, 3, 4]:  # Monday to Friday
            day_type = 'weekday'
        else:
            day_type = 'weekend'

        # Determine the seasonal profile
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'autumn'

        # Adjust consumption based on the profiles
        adjusted_consumption = (base_consumption * hourly_profile[time_of_day] *
                                weekday_profile[day_type] * seasonal_profile[season])

        return adjusted_consumption

    # Extract time information from current_time
    current_time = pd.to_datetime(current_time, utc=True)
    hour = current_time.hour
    day_of_week = current_time.dayofweek
    month = current_time.month

    # Find the row of data closest to current_time
    closest_row = residential_data.iloc[(residential_data['cet_cest_timestamp'] - current_time).abs().argmin()]

    # Calculate the adjusted consumption for this row
    base_consumption = closest_row['total_consumption_kwh']
    power_draw = adjusted_consumption(hour, day_of_week, month, base_consumption)

    return power_draw

# Example usage of the function
current_time = "2023-05-15 14:00:00"
print(f"Power draw for DE_KN_residential4 at {current_time}: {simulation_of_a_household(current_time)} kW")


battery_charge_state = 0
def simulation_of_a_battery_storage(energy_delta, location, current_time):
    energy_delta_battery = 0  # kW
    battery_capacity = 10  # kWh
    battery_charge_efficiency = 0.9  # 90%
    battery_discharge_efficiency = 0.9  # 90%
    battery_max_charge_rate = 4  # kW
    battery_max_discharge_rate = 5  # kW

    # Calculate the energy_delta of the battery (kWh charged or discharged) depending
    # on location and current time
    # discharged -> energy_delta_battery < 0, charged -> energy_delta_battery > 0
    # Use the battery_charge_state to store state of charge across simulation iterations
    # Battery can be charged until battery_capacity is reached with speed battery_max_charge_rate
    # Battery can be discharged until empty with speed battery_max_discharge_rate
    # Charging and discharging happens with < 100% efficiency
    #
    # Depending on the location it might be useful to charge battery at special times
    # to maximize cost savings
    #
    ## Your Code Here

    ##
    return energy_delta_battery


def importing_of_energy_from_the_grid(energy_delta, location, current_time):
    energy_imported_cost = 0 # €

    # Calculate electricity price for location at given time for energy consumed
    # "The price of the electricity off-peak (from 20h to 8h) in France is
    # 0,20458€ and 0,26706€ in peak (from 8h to 20h)."
    # The price for electricity in Germany is fixed. Use 0,3194€
    #
    ## Your Code Here

    ##
    return energy_imported_cost


data = []
def visualize_results(power_output_microgrid, power_usage_household, energy_delta_battery,
                      energy_imported_cost, current_time, location, plot_data=False):
    data_in_timestep = [power_output_microgrid, power_usage_household,
                        power_usage_household, energy_delta_battery,
                        energy_imported_cost, current_time]
    if not plot_data:
        data.append(data_in_timestep)
    else:
        # Visualize data with matplotlib
        # Use Array data for input data and plot over current_time in array
        # Use location for title of your plot
        #
        ## Your Code Here
        print(f"Visualizing now! Number of dataitems: {len(data)}")

        ##


main()