from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
from geopy.distance import geodesic

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Google Maps API Key (Replace with your actual API Key)
GOOGLE_MAPS_API_KEY = "AIzaSyBKdFdzO7mtiH1SGpqTox5Bmxlye2HpAHE"

# Charging stations data
stations_data = {
    'station_name': ['FORT', 'KALMASSERY', 'VITYILLA', 'EDAPALLY','Maradu Ernakulam'],
    'latitude': [9.9658, 10.0531, 9.9658, 10.0261,9.936811],
    'longitude': [76.2421, 76.3528, 76.3217, 76.3125,76.323204],
    'charging_speed': [50, 100, 75, 150,100]  # Charging speed in kW
}

# Creating DataFrame for stations
stations_df = pd.DataFrame(stations_data)

# Function to calculate direct distance between two locations
def calculate_distance(loc1, loc2):
    try:
        return geodesic(loc1, loc2).kilometers
    except Exception as e:
        return str(e)

# Function to get real-time traffic ETA using Google Directions API
def get_traffic_eta(origin, destination):
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&traffic_model=best_guess&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            duration_in_traffic = data["routes"][0]["legs"][0]["duration_in_traffic"]["value"]  # in seconds
            return duration_in_traffic / 60  # Convert to minutes
        else:
            return float('inf')  # If traffic data unavailable, set a high value
    except Exception as e:
        return float('inf')

# Function to check if a station is on the route using Google Maps API
def is_station_on_route(origin, destination, station):
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&waypoints={station}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            return True  # If route includes the waypoint (station)
        return False
    except Exception as e:
        return False

# Function to find the best charging station based on destination
def get_best_charging_station(current_location, destination, battery_percentage):
    try:
        max_range = 300 * (battery_percentage / 100)
        best_station_on_route = None
        best_station_off_route = None
        shortest_total_eta = float('inf')
        shortest_off_route_eta = float('inf')

        for _, row in stations_df.iterrows():
            station_location = (row['latitude'], row['longitude'])
            distance = calculate_distance(current_location, station_location)

            if distance <= max_range:
                origin = f"{current_location[0]},{current_location[1]}"
                station = f"{station_location[0]},{station_location[1]}"
                dest = f"{destination[0]},{destination[1]}"

                # Check if the station is on the route
                if is_station_on_route(origin, dest, station):
                    eta_to_station = get_traffic_eta(origin, station)
                    eta_to_destination = get_traffic_eta(station, dest)
                    total_eta = eta_to_station + eta_to_destination

                    # Select the best station on route
                    if total_eta < shortest_total_eta:
                        shortest_total_eta = total_eta
                        best_station_on_route = {
                            'station_name': row['station_name'],
                            'distance': distance,
                            'charging_speed': row['charging_speed'],
                            'eta_to_station': eta_to_station,
                            'eta_to_destination': eta_to_destination,
                            'total_eta': total_eta,
                            'type': 'on_route'
                        }
                else:
                    # If not on route, find the best reachable station
                    eta_to_station = get_traffic_eta(origin, station)
                    if eta_to_station < shortest_off_route_eta:
                        shortest_off_route_eta = eta_to_station
                        best_station_off_route = {
                            'station_name': row['station_name'],
                            'distance': distance,
                            'charging_speed': row['charging_speed'],
                            'eta_to_station': eta_to_station,
                            'type': 'off_route'
                        }

        # Return the best option (preferably on route)
        if best_station_on_route:
            return best_station_on_route
        elif best_station_off_route:
            return best_station_off_route
        else:
            return {'error': 'No suitable charging station found'}
    except Exception as e:
        return {'error': str(e)}

# Route to check API status
@app.route('/status')
def status():
    return jsonify({'status': 'OK'})

# Route to find the best charging station considering destination
@app.route('/api/best-charging-station', methods=['POST'])
def best_charging_station():
    try:
        data = request.json
        current_location = tuple(data.get('current_location', ()))
        destination = tuple(data.get('destination', ()))
        battery_percentage = data.get('battery_percentage', 0)

        if not current_location or not destination or battery_percentage <= 0:
            return jsonify({'error': 'Invalid input: Please provide current location, destination, and battery percentage'}), 400

        best_station = get_best_charging_station(current_location, destination, battery_percentage)

        return jsonify(best_station)
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)














# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import pandas as pd
# import requests
# from geopy.distance import geodesic

# app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes

# # Google Maps API Key (Replace with your API Key)
# GOOGLE_MAPS_API_KEY = "AIzaSyBKdFdzO7mtiH1SGpqTox5Bmxlye2HpAHE"

# # Charging stations data
# stations_data = {
#     'station_name': ['FORT', 'KALMASSERY', 'VITYILLA', 'EDAPALLY'],
#     'latitude': [9.9658, 10.0531, 9.9658, 10.0261],
#     'longitude': [76.2421, 76.3528, 76.3217, 76.3125],
#     'charging_speed': [50, 100, 75, 150]  # Charging speed in kW
# }

# # Creating DataFrame for stations
# stations_df = pd.DataFrame(stations_data)

# # Function to calculate the distance between current location and station
# def calculate_distance(current_location, station_location):
#     try:
#         return geodesic(current_location, station_location).kilometers
#     except Exception as e:
#         return str(e)

# # Function to get traffic ETA using Google Directions API
# def get_traffic_eta(origin, destination):
#     try:
#         url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&traffic_model=best_guess&key={GOOGLE_MAPS_API_KEY}"
#         response = requests.get(url)
#         data = response.json()

#         if data["status"] == "OK":
#             duration_in_traffic = data["routes"][0]["legs"][0]["duration_in_traffic"]["text"]
#             return duration_in_traffic
#         else:
#             return "Traffic data unavailable"
#     except Exception as e:
#         return str(e)

# # Function to get the nearest stations based on traffic conditions
# def get_nearest_stations(current_location, battery_percentage):
#     try:
#         max_range = 300 * (battery_percentage / 100)
#         within_range = []

#         for _, row in stations_df.iterrows():
#             station_location = (row['latitude'], row['longitude'])
#             distance = calculate_distance(current_location, station_location)

#             if distance <= max_range:
#                 origin = f"{current_location[0]},{current_location[1]}"
#                 destination = f"{station_location[0]},{station_location[1]}"
#                 traffic_eta = get_traffic_eta(origin, destination)

#                 within_range.append({
#                     'station_name': row['station_name'],
#                     'distance': distance,
#                     'charging_speed': row['charging_speed'],
#                     'traffic_eta': traffic_eta
#                 })

#         # Sort stations by ETA (shortest travel time first)
#         return sorted(within_range, key=lambda x: x['distance'])[:3]
#     except Exception as e:
#         return {'error': str(e)}

# # Route to check API status
# @app.route('/status')
# def status():
#     return jsonify({'status': 'OK'})

# # Route to find nearest stations
# @app.route('/api/nearest-stations', methods=['POST'])
# def nearest_stations():
#     try:
#         data = request.json
#         current_location = tuple(data.get('current_location', ()))  # (lat, long)
#         battery_percentage = data.get('battery_percentage', 0)

#         if not current_location or battery_percentage <= 0:
#             return jsonify({'error': 'Invalid input: Please provide current location and battery percentage'}), 400

#         stations = get_nearest_stations(current_location, battery_percentage)

#         return jsonify(stations)
#     except Exception as e:
#         return jsonify({'error': f"An error occurred: {str(e)}"}), 500

# # Main entry point
# if __name__ == '__main__':
#     app.run(debug=True)
