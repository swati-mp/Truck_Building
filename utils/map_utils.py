import folium
from folium.plugins import BeautifyIcon
import pandas as pd
import random
from branca.colormap import linear

# Define a palette for multiple routes
COLOR_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

def create_colored_route_map(allocated_df, customers_df):
    start_coord = (customers_df.iloc[0]['latitude'], customers_df.iloc[0]['longitude'])
    m = folium.Map(location=start_coord, zoom_start=10)

    # Group by each truck
    grouped = allocated_df.groupby("truck_id")
    for i, (truck_id, group) in enumerate(grouped):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        points = list(zip(group['latitude'], group['longitude']))

        # Draw polyline for the truck's route
        folium.PolyLine(points, color=color, weight=4, opacity=0.8, tooltip=f"Truck {truck_id}").add_to(m)

        # Add customer markers with order labels
        for j, row in group.iterrows():
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
