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


def get_location(location_name):
    if location_name == "ST_NAZAIRE":
        # Create Location object for Saint-Nazaire
        return Location(47.2735, -2.2137, name="Saint-Nazaire")
    elif location_name == "FRIEDBERG":
        # Create Location object for Friedberg
        return Location(50.3351, 8.7555, name="Friedberg")
    else:
        raise ValueError("Location not supported")

def simulation_of_a_microgrid(location, current_time):
    # Microgrid parameters
    efficiency_of_microgrid = 0.9  # 90%
    maximum_power_output = 10  # kW

    # Get Location object
    loc = get_location(location)

    # Define the time range for the simulation (just one point in this case)
    times = pd.DatetimeIndex([current_time])

    # Get clear sky data
    cs = loc.get_clearsky(times)

    # Extract irradiance data
    dni = cs['dni']  # Direct Normal Irradiance
    ghi = cs['ghi']  # Global Horizontal Irradiance
    dhi = cs['dhi']  # Diffuse Horizontal Irradiance

    # Assume the PV system is facing south and tilted at the latitude angle
    surface_tilt = loc.latitude
    surface_azimuth = 180

    # Calculate solar position
    solar_position = loc.get_solarposition(times)

    # Calculate total irradiance on the tilted surface
    total_irrad = pvlib.irradiance.get_total_irradiance(
        surface_tilt,
        surface_azimuth,
        solar_position['apparent_zenith'],
        solar_position['azimuth'],
        dni,
        ghi,
        dhi
    )

    # Assume a simple PV system with a certain efficiency
    pv_efficiency = 0.15  # 15% efficient PV panels
    pv_area = maximum_power_output / (pv_efficiency * 1000)  # Area in square meters

    # Calculate the DC power output from the PV system
    poa_irradiance = total_irrad['poa_global']  # Plane of array irradiance
    dc_power = poa_irradiance * pv_area * pv_efficiency  # DC power output

    # Convert DC power to AC power
    ac_power = dc_power * efficiency_of_microgrid

    # Ensure power output does not exceed maximum
    power_output = min(ac_power.iloc[0], maximum_power_output)

    return power_output



def simulation_of_a_household(current_time):
    power_draw = 0  # kW

    # Load data from a CSV file
    data = pd.read_csv('CESI-THM-Project1-Load-Profile.csv', delimiter=';')

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
#current_time = "2023-05-15 14:00:00"
#print(f"Power draw for DE_KN_residential4 at {current_time}: {simulation_of_a_household(current_time)} kW")


battery_charge_state = 0

def simulation_of_a_battery_storage(energy_delta, location, current_time):
    global battery_charge_state
    
    battery_capacity = 10
    battery_charge_efficiency = 0.9
    battery_discharge_efficiency = 0.9
    battery_max_charge_rate = 4
    battery_max_discharge_rate = 5
    energy_delta_battery = 0
    current_hour = current_time.hour

    if location == "Saint-Nazaire":
        if 20 <= current_hour or current_hour < 8: # Charge during night (off-peak hours) 20:00 - 08:00
            energy_delta = abs(energy_delta) # Ensure positive for charging
        elif 8 <= current_hour < 20: # Discharge during day 08:00 - 20:00
            energy_delta = -abs(energy_delta) # Ensure negative for discharging

    elif location == "Friedberg":
        if 5 <= current_hour < 21: # Charge during midday (solar abundance)
            energy_delta = abs(energy_delta) # Ensure positive for charging
        elif 21 <= current_hour < 5: # Discharge during peak hours
            energy_delta = -abs(energy_delta) # Ensure negative for discharging
    # Decide if we are charging or discharging
    if energy_delta > 0:
        # Charging
        # Ensure we do not exceed the max charge rate and battery capacity
        charge_amount = min(energy_delta, battery_max_charge_rate)
        effective_charge = charge_amount * battery_charge_efficiency
        
        if battery_charge_state + effective_charge > battery_capacity:
            # Limit to the maximum capacity
            effective_charge = battery_capacity - battery_charge_state
        
        battery_charge_state += effective_charge
        energy_delta_battery = effective_charge
    elif energy_delta < 0:
        # Discharging
        # Ensure we do not exceed the max discharge rate and do not discharge below 0
        discharge_amount = min(abs(energy_delta), battery_max_discharge_rate)
        effective_discharge = discharge_amount / battery_discharge_efficiency
        
        if battery_charge_state - effective_discharge < 0:
            # Limit to the minimum capacity (0)
            effective_discharge = battery_charge_state
        
        battery_charge_state -= effective_discharge
        energy_delta_battery = -effective_discharge

    return energy_delta_battery


def importing_of_energy_from_the_grid(energy_delta, location, current_time):
    energy_imported_cost = 0 # €
    
    if energy_delta > 0:  # Energy deficit, need to import
        hour = current_time.hour

        if location == "FRIEDBERG":
            # Fixed electricity price in Germany
            price_per_kwh = 0.3194

        elif location == "ST_NAZAIRE":
            # Peak and off-peak electricity prices in France
            if 8 <= hour < 20:  # Peak hours
                price_per_kwh = 0.26706
            else:  # Off-peak hours
                price_per_kwh = 0.20458

        # Calculate cost
        energy_imported_cost = energy_delta * price_per_kwh

    return energy_imported_cost


data = []
def visualize_results(power_output_microgrid, power_usage_household, energy_delta_battery,
                      energy_imported_cost, current_time, location, plot_data=False):
    data_in_timestep = [power_output_microgrid, power_usage_household,
                        energy_delta_battery, energy_imported_cost, 
                        current_time]
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