import folium
from folium.plugins import BeautifyIcon, AntPath, MiniMap, MeasureControl
from utils.constants import COLOR_PALETTE
import numpy as np
from geopy.distance import geodesic

def create_colored_route_map(allocated_df, customers_df, warehouses_df):
    all_lat = warehouses_df['latitude'].tolist()
    all_lon = warehouses_df['longitude'].tolist()
    center_lat = np.mean(all_lat)
    center_lon = np.mean(all_lon)

    # Modern Base Map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles="CartoDB Positron")
    m.add_child(MiniMap(toggle_display=True))
    m.add_child(MeasureControl(primary_length_unit='kilometers'))

    # Add warehouse layer
    warehouse_layer = folium.FeatureGroup(name="Warehouses").add_to(m)
    for _, warehouse in warehouses_df.iterrows():
        folium.Marker(
            location=(warehouse['latitude'], warehouse['longitude']),
            popup=f"🏢 Warehouse: {warehouse['warehouse_name']} ({warehouse['state']})",
            icon=folium.Icon(color="green", icon="building", prefix='fa')
        ).add_to(warehouse_layer)

    grouped = allocated_df.groupby("truck_id")
    truck_legend = []

    for i, (truck_id, group) in enumerate(grouped):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        truck_type = group.iloc[0].get("truck_type", "N/A")
        fuel_cost = group.iloc[0].get("fuel_cost", 0)
        emissions = group.iloc[0].get("emissions_estimate", 0)
        capacity = group.iloc[0].get("truck_capacity_kg", 0)
        utilization = group.iloc[0].get("utilization_percent", 0)
        state = group.iloc[0].get("state")

        warehouse = warehouses_df[warehouses_df['state'] == state]
        start_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude']) if not warehouse.empty else (group['latitude'].mean(), group['longitude'].mean())

        points = list(zip(group['latitude'], group['longitude']))
        points.insert(0, start_coord)

        # Add to separate truck layer
        truck_layer = folium.FeatureGroup(name=f"Truck {truck_id}", show=True)
        AntPath(points, color=color, weight=4, delay=800).add_to(truck_layer)

        # Distance Labels
        for j in range(1, len(points)):
            dist_km = round(geodesic(points[j - 1], points[j]).km, 2)
            midpoint = [(points[j - 1][0] + points[j][0]) / 2, (points[j - 1][1] + points[j][1]) / 2]
            folium.Marker(
                location=midpoint,
                icon=folium.DivIcon(html=f"<div style='font-size:10pt;color:black'>{dist_km} km</div>")
            ).add_to(truck_layer)

        # Depot marker
        folium.Marker(
            location=start_coord,
            popup=folium.Popup(f"""
                <b>Truck ID:</b> {truck_id}<br>
                <b>Truck Type:</b> {truck_type}<br>
                <b>Fuel Cost:</b> ₹{fuel_cost}<br>
                <b>Emissions:</b> {emissions} kg CO₂<br>
                <b>Capacity:</b> {capacity} kg<br>
                <b>Utilization:</b> {utilization}%
            """, max_width=300),
            icon=folium.Icon(color="blue", icon="truck", prefix='fa')
        ).add_to(truck_layer)

        # Customer markers
        for _, row in group.iterrows():
            folium.Marker(
                location=(row['latitude'], row['longitude']),
                icon=BeautifyIcon(
                    icon_shape='marker',
                    number=row['route_order'],
                    border_color=color,
                    text_color=color
                ),
                tooltip=f"{row['customer_name']}\nRoute Order: {row['route_order']}\nTruck: {truck_id}"
            ).add_to(truck_layer)

        truck_layer.add_to(m)
        truck_legend.append((color, truck_id))

    # 🚛 Truck Color Legend (black text)
    legend_html = """
    <div style='position: fixed; bottom: 30px; left: 30px; z-index:9999; font-size:14px;
        background: white; padding: 10px; border:2px solid grey; color:black;'>
    <b>🚛 Truck Color Legend</b><br>
    """ + "<br>".join([
        f"<i style='background:{color};padding:5px 10px;margin-right:6px;'>&nbsp;</i>Truck {truck_id}"
        for color, truck_id in truck_legend
    ]) + "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m

<<<<<<< HEAD
=======

# # -------------------------------------LIVE ROUTE-------------------------------------------#

# # map_utils.py
# import folium
# from folium.plugins import BeautifyIcon, AntPath, MiniMap, MeasureControl
# from utils.constants import COLOR_PALETTE
# import numpy as np
# from geopy.distance import geodesic
# from utils import route_utils

# def create_colored_route_map(allocated_df, customers_df, warehouses_df):
#     all_lat = warehouses_df['latitude'].tolist()
#     all_lon = warehouses_df['longitude'].tolist()
#     center_lat = np.mean(all_lat)
#     center_lon = np.mean(all_lon)

#     m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles="CartoDB Positron")
#     m.add_child(MiniMap(toggle_display=True))
#     m.add_child(MeasureControl(primary_length_unit='kilometers'))

#     warehouse_layer = folium.FeatureGroup(name="Warehouses").add_to(m)
#     for _, warehouse in warehouses_df.iterrows():
#         folium.Marker(
#             location=(warehouse['latitude'], warehouse['longitude']),
#             popup=f"🏢 Warehouse: {warehouse['warehouse_name']} ({warehouse['state']})",
#             icon=folium.Icon(color="green", icon="building", prefix='fa')
#         ).add_to(warehouse_layer)

#     grouped = allocated_df.groupby("truck_id")
#     truck_legend = []

#     for i, (truck_id, group) in enumerate(grouped):
#         color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
#         truck_type = group.iloc[0].get("truck_type", "N/A")
#         fuel_cost = group.iloc[0].get("fuel_cost", 0)
#         emissions = group.iloc[0].get("emissions_estimate", 0)
#         capacity = group.iloc[0].get("truck_capacity_kg", 0)
#         utilization = group.iloc[0].get("utilization_percent", 0)
#         state = group.iloc[0].get("state")

#         warehouse = warehouses_df[warehouses_df['state'] == state]
#         if not warehouse.empty:
#             warehouse_coord = (warehouse.iloc[0]['latitude'], warehouse.iloc[0]['longitude'])
#         else:
#             warehouse_coord = (group['latitude'].mean(), group['longitude'].mean())

#         # Build list of all route points with labels
#         route_points = [('W', warehouse_coord)]
#         for _, row in group.sort_values("route_order").iterrows():
#             route_points.append((str(row["route_order"]), (row['latitude'], row['longitude'])))

#         # Build full route with GraphHopper
#         full_route = []
#         for j in range(len(route_points) - 1):
#             start_pt = route_points[j][1]
#             end_pt = route_points[j + 1][1]
#             segment = route_utils.get_route_graphhopper(
#                 start_pt[0], start_pt[1], end_pt[0], end_pt[1]
#             )
#             if segment:
#                 if full_route and full_route[-1] == segment[0]:
#                     segment = segment[1:]
#                 full_route.extend(segment)

#         # Draw truck route
#         truck_layer = folium.FeatureGroup(name=f"Truck {truck_id}", show=True)
#         AntPath(full_route, color=color, weight=4, delay=800).add_to(truck_layer)

#         # Annotate distances between points
#         for j in range(1, len(route_points)):
#             from_label, from_coord = route_points[j - 1]
#             to_label, to_coord = route_points[j]
#             dist_km = round(geodesic(from_coord, to_coord).km, 2)
#             midpoint = [(from_coord[0] + to_coord[0]) / 2,
#                         (from_coord[1] + to_coord[1]) / 2]

#             folium.Marker(
#                 location=midpoint,
#                 icon=folium.DivIcon(
#                     html=f"""
#                     <div style='font-size:10pt;color:black;background:white;padding:2px 4px;
#                                 border-radius:4px;border:1px solid gray;box-shadow:1px 1px 2px rgba(0,0,0,0.2);'>
#                         {from_label} ➝ {to_label}: {dist_km} km
#                     </div>
#                     """)
#             ).add_to(truck_layer)

#         # Truck origin marker
#         folium.Marker(
#             location=warehouse_coord,
#             popup=folium.Popup(f"""
#                 <b>Truck ID:</b> {truck_id}<br>
#                 <b>Truck Type:</b> {truck_type}<br>
#                 <b>Fuel Cost:</b> ₹{fuel_cost}<br>
#                 <b>Emissions:</b> {emissions} kg CO₂<br>
#                 <b>Capacity:</b> {capacity} kg<br>
#                 <b>Utilization:</b> {utilization}%
#             """, max_width=300),
#             icon=folium.Icon(color="blue", icon="truck", prefix='fa')
#         ).add_to(truck_layer)

#         # Customer markers
#         for _, row in group.iterrows():
#             folium.Marker(
#                 location=(row['latitude'], row['longitude']),
#                 icon=BeautifyIcon(
#                     icon_shape='marker',
#                     number=row['route_order'],
#                     border_color=color,
#                     text_color=color
#                 ),
#                 tooltip=f"{row['customer_name']}\nRoute Order: {row['route_order']}\nTruck: {truck_id}"
#             ).add_to(truck_layer)

#         truck_layer.add_to(m)
#         truck_legend.append((color, truck_id))

#     # Legend
#     legend_html = """
#     <div style='position: fixed; bottom: 30px; left: 30px; z-index:9999; font-size:14px;
#         background: white; padding: 10px; border:2px solid grey; color:black;'>
#     <b>🚛 Truck Color Legend</b><br>
#     """ + "<br>".join([
#         f"<i style='background:{color};padding:5px 10px;margin-right:6px;'>&nbsp;</i>Truck {truck_id}"
#         for color, truck_id in truck_legend
#     ]) + "</div>"
#     m.get_root().html.add_child(folium.Element(legend_html))

#     folium.LayerControl(collapsed=False).add_to(m)
#     return m
>>>>>>> df81800 (Enhanced delivery map with GraphHopper for optimized truck routing.)
