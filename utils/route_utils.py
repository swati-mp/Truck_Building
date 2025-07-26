#For Point to Point connections
import numpy as np

# Fast Haversine Function
def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

# Enhanced Nearest Neighbor Route Optimizer using Haversine

def nearest_neighbor_route(customer_coords, start_coord):
    """
    Approximate TSP using nearest neighbor heuristic.
    Inputs: list of (lat, lon), starting point (lat, lon)
    Output: ordered list of coordinates (route including start)
    """
    if not customer_coords:
        return [start_coord]

    coords = np.array(customer_coords)
    visited = [start_coord]
    current = np.array(start_coord)
    remaining = coords.copy()

    while len(remaining) > 0:
        lat1, lon1 = current[0], current[1]
        lat2, lon2 = remaining[:, 0], remaining[:, 1]
        distances = haversine_np(lat1, lon1, lat2, lon2)
        nearest_idx = np.argmin(distances)
        nearest_coord = remaining[nearest_idx]
        visited.append(tuple(nearest_coord))
        remaining = np.delete(remaining, nearest_idx, axis=0)
        current = nearest_coord

    return visited

<<<<<<< HEAD
=======

# # -------------------------------------LIVE ROUTE-------------------------------------------#
# #rout_uils.py

# import requests
# import polyline
# import streamlit as st
# import os
# import json

# GRAPH_HOPPER_API_KEY = "a986bd9b-108a-4395-9811-f7779b0f7184"  # Replace with your real API key
# ROUTE_CACHE_FILE = "data/route_cache.json"

# # Load existing cache
# if os.path.exists(ROUTE_CACHE_FILE):
#     with open(ROUTE_CACHE_FILE, "r") as f:
#         route_cache = json.load(f)
# else:
#     route_cache = {}

# def generate_route_key(start_lat, start_lon, end_lat, end_lon):
#     return f"{start_lat:.4f}_{start_lon:.4f}_{end_lat:.4f}_{end_lon:.4f}"

# def save_cache():
#     with open(ROUTE_CACHE_FILE, "w") as f:
#         json.dump(route_cache, f, indent=2)

# @st.cache_data(show_spinner=False)
# def get_route_graphhopper(start_lat, start_lon, end_lat, end_lon):
#     """
#     Checks cache first, then fetches truck route using GraphHopper and saves to local cache.
#     """
#     route_key = generate_route_key(start_lat, start_lon, end_lat, end_lon)
#     if route_key in route_cache:
#         return route_cache[route_key]

#     url = "https://graphhopper.com/api/1/route"
#     params = {
#         "point": [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
#         "vehicle": "car",
#         "locale": "en",
#         "calc_points": True,
#         "points_encoded": True,
#         "key": GRAPH_HOPPER_API_KEY
#     }

#     try:
#         response = requests.get(url, params=params)
#         response.raise_for_status()
#         data = response.json()

#         if 'paths' not in data or not data['paths']:
#             st.warning("GraphHopper returned no path data.")
#             return [(start_lat, start_lon), (end_lat, end_lon)]

#         encoded = data['paths'][0]['points']
#         decoded = polyline.decode(encoded)

#         route_cache[route_key] = decoded
#         save_cache()

#         return decoded

#     except requests.exceptions.HTTPError as e:
#         if response.status_code == 429:
#             st.error("🚫 GraphHopper API limit exceeded for today.")
#         else:
#             st.error(f"GraphHopper Error: {e}")
#         return [(start_lat, start_lon), (end_lat, end_lon)]

#     except Exception as e:
#         st.warning(f"⚠️ Failed to fetch route: {e}")
#         return [(start_lat, start_lon), (end_lat, end_lon)]





>>>>>>> df81800 (Enhanced delivery map with GraphHopper for optimized truck routing.)
