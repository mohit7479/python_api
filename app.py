from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import requests
from geopy.distance import geodesic

app = Flask(__name__)
CORS(app)

# Google Maps API Key 
GOOGLE_MAPS_API_KEY = "AIzaSyBKdFdzO7mtiH1SGpqTox5Bmxlye2HpAHE"

# Charging stations data
stations_data = {
    'station_name': ['FORT', 'KALMASSERY', 'VITYILLA', 'EDAPALLY'],
    'latitude': [9.9658, 10.0531, 9.9658, 10.0261],
    'longitude': [76.2421, 76.3528, 76.3217, 76.3125],
    'charging_speed': [100, 100, 75, 150]  # Charging speed in kW
}

# Creating DataFrame for stations
stations_df = pd.DataFrame(stations_data)

# Function to calculate the distance between two locations
def calculate_distance(location1, location2):
    try:
        return geodesic(location1, location2).kilometers
    except Exception as e:
        return str(e)

# Function to get traffic ETA using Google Directions API
def get_traffic_eta(origin, destination):
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&traffic_model=best_guess&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            duration_in_traffic = data["routes"][0]["legs"][0]["duration_in_traffic"]["value"]  # in seconds
            return duration_in_traffic
        else:
            print(f"Traffic data unavailable for {origin} to {destination}: {data['status']}")
            return None
    except Exception as e:
        print(f"Error fetching traffic data: {str(e)}")
        return None

# Function to get the nearest stations based on traffic conditions
def get_nearest_stations(current_location, destination_coords, battery_percentage):
    try:
        if battery_percentage <= 0:
            return {'message': 'Your battery is too low to reach any charging station.'}

        max_range = 300 * (battery_percentage / 100)
        within_range = []

        for _, row in stations_df.iterrows():
            station_location = (row['latitude'], row['longitude'])
            distance_to_station = calculate_distance(current_location, station_location)
            distance_to_destination = calculate_distance(station_location, destination_coords)

            if distance_to_station <= max_range:
                origin_to_station_eta = get_traffic_eta(f"{current_location[0]},{current_location[1]}", f"{station_location[0]},{station_location[1]}")
                station_to_destination_eta = get_traffic_eta(f"{station_location[0]},{station_location[1]}", f"{destination_coords[0]},{destination_coords[1]}")

                if origin_to_station_eta is not None and station_to_destination_eta is not None:
                    total_eta = origin_to_station_eta + station_to_destination_eta
                    total_distance = distance_to_station + distance_to_destination

                    within_range.append({
                        'station_name': row['station_name'],
                        'distance_to_station': distance_to_station,
                        'distance_to_destination': distance_to_destination,
                        'total_distance': total_distance,
                        'charging_speed': row['charging_speed'],
                        'total_eta': total_eta,
                        'origin_to_station_eta': origin_to_station_eta,
                        'station_to_destination_eta': station_to_destination_eta
                    })

        if not within_range:
            return {'message': 'You cannot reach any charging station with the current battery level.'}

        # Sort stations by total ETA (shortest travel time first)
        return sorted(within_range, key=lambda x: x['total_eta'])[:3]
    except Exception as e:
        print(f"Error in get_nearest_stations: {str(e)}")
        return {'error': str(e)}

# Route to check API status
@app.route('/status')
def status():
    return jsonify({'status': 'OK'})

# Route to find nearest stations
@app.route('/api/nearest-stations', methods=['POST'])
def nearest_stations():
    try:
        data = request.json
        print("Received data:", data)  # Debugging log
        current_location = tuple(data.get('current_location', ()))  # (lat, long)
        destination_coords = tuple(data.get('destination', ()))  # (lat, long)
        battery_percentage = data.get('battery_percentage', 0)

        if not current_location or not destination_coords or None in destination_coords:
            return jsonify({'error': 'Invalid input: Please provide valid current location and destination coordinates'}), 400

        stations = get_nearest_stations(current_location, destination_coords, battery_percentage)

        print("Stations found:", stations)  # Debugging log
        return jsonify(stations)
    except Exception as e:
        print(f"Error in nearest_stations route: {str(e)}")
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

# # Function to calculate the distance between two locations
# def calculate_distance(location1, location2):
#     try:
#         return geodesic(location1, location2).kilometers
#     except Exception as e:
#         return str(e)

# # Function to get traffic ETA using Google Directions API
# def get_traffic_eta(origin, destination):
#     try:
#         url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&traffic_model=best_guess&key={GOOGLE_MAPS_API_KEY}"
#         response = requests.get(url)
#         data = response.json()

#         if data["status"] == "OK":
#             duration_in_traffic = data["routes"][0]["legs"][0]["duration_in_traffic"]["value"]  # in seconds
#             return duration_in_traffic
#         else:
#             print(f"Traffic data unavailable for {origin} to {destination}: {data['status']}")
#             return None
#     except Exception as e:
#         print(f"Error fetching traffic data: {str(e)}")
#         return None

# # Function to get the nearest stations based on traffic conditions
# def get_nearest_stations(current_location, destination_coords, battery_percentage):
#     try:
#         if battery_percentage <= 0:
#             return {'message': 'Your battery is too low to reach any charging station.'}

#         max_range = 300 * (battery_percentage / 100)
#         within_range = []

#         for _, row in stations_df.iterrows():
#             station_location = (row['latitude'], row['longitude'])
#             distance_to_station = calculate_distance(current_location, station_location)
#             distance_to_destination = calculate_distance(station_location, destination_coords)

#             if distance_to_station <= max_range:
#                 origin_to_station_eta = get_traffic_eta(f"{current_location[0]},{current_location[1]}", f"{station_location[0]},{station_location[1]}")
#                 station_to_destination_eta = get_traffic_eta(f"{station_location[0]},{station_location[1]}", f"{destination_coords[0]},{destination_coords[1]}")

#                 if origin_to_station_eta is not None and station_to_destination_eta is not None:
#                     total_eta = origin_to_station_eta + station_to_destination_eta
#                     total_distance = distance_to_station + distance_to_destination

#                     within_range.append({
#                         'station_name': row['station_name'],
#                         'distance_to_station': distance_to_station,
#                         'distance_to_destination': distance_to_destination,
#                         'total_distance': total_distance,
#                         'charging_speed': row['charging_speed'],
#                         'total_eta': total_eta,
#                         'origin_to_station_eta': origin_to_station_eta,
#                         'station_to_destination_eta': station_to_destination_eta
#                     })

#         if not within_range:
#             return {'message': 'You cannot reach any charging station with the current battery level.'}

#         # Sort stations by total ETA (shortest travel time first)
#         return sorted(within_range, key=lambda x: x['total_eta'])[:3]
#     except Exception as e:
#         print(f"Error in get_nearest_stations: {str(e)}")
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
#         print("Received data:", data)  # Debugging log
#         current_location = tuple(data.get('current_location', ()))  # (lat, long)
#         destination_coords = tuple(data.get('destination', ()))  # (lat, long)
#         battery_percentage = data.get('battery_percentage', 0)

#         if not current_location or not destination_coords or None in destination_coords:
#             return jsonify({'error': 'Invalid input: Please provide valid current location and destination coordinates'}), 400

#         stations = get_nearest_stations(current_location, destination_coords, battery_percentage)

#         print("Stations found:", stations)  # Debugging log
#         return jsonify(stations)
#     except Exception as e:
#         print(f"Error in nearest_stations route: {str(e)}")
#         return jsonify({'error': f"An error occurred: {str(e)}"}), 500

# # Main entry point
# if __name__ == '__main__':
#     app.run(debug=True)














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
