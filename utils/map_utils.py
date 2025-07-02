import folium
from folium.plugins import BeautifyIcon
from utils.constants import COLOR_PALETTE
import numpy as np

def create_colored_route_map(allocated_df, customers_df, warehouses_df):
    # Calculate map center based on all warehouse locations
    all_lat = warehouses_df['latitude'].tolist()
    all_lon = warehouses_df['longitude'].tolist()
    center_lat = np.mean(all_lat)
    center_lon = np.mean(all_lon)

    # ✅ Initialize folium map here with wider zoom
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)  # 👈 Add here

    # 🏢 Plot all warehouses as green buildings
    for _, warehouse in warehouses_df.iterrows():
        folium.Marker(
            location=(warehouse['latitude'], warehouse['longitude']),
            popup=f"🏢 Warehouse: {warehouse['warehouse_name']} ({warehouse['state']})",
            icon=folium.Icon(color="green", icon="building", prefix='fa')
        ).add_to(m)

    # 🚛 Plot delivery routes per truck
    grouped = allocated_df.groupby("truck_id")
    for i, (truck_id, group) in enumerate(grouped):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]

        # Get warehouse for this truck’s customers
        state = group.iloc[0].get('state') or customers_df.iloc[0].get('state')
        warehouse = warehouses_df[warehouses_df['state'] == state]
        if not warehouse.empty:
            start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
        else:
            start_coord = [center_lat, center_lon]  # fallback

        points = list(zip(group['latitude'], group['longitude']))
        points.insert(0, start_coord)

        folium.PolyLine(points, color=color, weight=4, opacity=0.8, tooltip=f"Truck {truck_id}").add_to(m)

        for _, row in group.iterrows():
            folium.Marker(
                location=(row['latitude'], row['longitude']),
                icon=BeautifyIcon(
                    icon_shape='marker',
                    number=row['route_order'],
                    border_color=color,
                    text_color=color
                ),
                tooltip=f"{row['customer_name']}\nRoute Order: {row['route_order']}\nTruck: {row['truck_id']}"
            ).add_to(m)

    return m
