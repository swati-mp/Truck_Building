from geopy.distance import geodesic

def nearest_neighbor_route(start_location, customer_ids, customers_df):
    locations = [(cid, (customers_df.loc[customers_df['customer_id'] == cid, 'latitude'].values[0],
                        customers_df.loc[customers_df['customer_id'] == cid, 'longitude'].values[0]))
                 for cid in customer_ids]
    route = []
    current = start_location

    while locations:
        next_point = min(locations, key=lambda x: geodesic(current, x[1]).km)
        route.append(next_point)
        current = next_point[1]
        locations.remove(next_point)

    return route
