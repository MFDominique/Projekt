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


def simulation_of_a_houshold(location, current_time):
    power_draw = 0 # kW

    # Use Data from here: https://moodle-ext.thm.de/mod/page/view.php?id=8993
    # Load data from the dataset and calculate overall powerdraw from
    # the household at the given time
    #
    ## Your Code Here


    ##
    return power_draw


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