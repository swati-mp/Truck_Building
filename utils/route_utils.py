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
