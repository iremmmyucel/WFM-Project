import folium
import pandas as pd
import geopy.distance
import contextily as ctx
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
import random
import numpy as np
from wfm_yedas_config import *




center_location = 41.19732911223483, 36.719378543270956 ## lat, lon

df1 = pd.read_excel(r"excels/result_wfm.xlsx")
df1 = df1.sample(frac=1).reset_index(drop=True)

df2 = df1.sort_values(by="Score", ascending=False)

df = pd.read_excel(r"excels/DataBase.xlsx")
df.dropna(subset=["Latitude(M)", "Longitude(M)"], inplace=True)
df["Latitude(M)"] = df["Latitude(M)"].str.replace(',', '.').astype(float)
df["Longitude(M)"] = df["Longitude(M)"].str.replace(',', '.').astype(float)
df["Completion Time (O)"] = pd.to_datetime(df["Completion Time (O)"], format='%d.%m.%Y %H:%M:%S')
df["Arrival Time (O)"] = pd.to_datetime(df["Arrival Time (O)"], format='%d.%m.%Y %H:%M:%S')
df["Repair Time"] = (df["Completion Time (O)"] - df["Arrival Time (O)"]).dt.total_seconds()
df_clean = pd.DataFrame(columns=df.columns)  # df_clean DataFrame'i, df ile aynı sütunlara sahip olmalıdır.



for i in range(len(df)):  # DataFrame'deki her satırı döngüye almak için range(len(df)) kullanılabilir.
    row = df.iloc[i]
    location = (row["Latitude(M)"], row["Longitude(M)"])
    distance = geopy.distance.geodesic(center_location, location).km
    if distance < 1.01:
        df_clean = pd.concat([df_clean, pd.DataFrame(row).transpose()], ignore_index=True)  

df_clean.to_excel("excels/df_clean.xlsx", index=False)
        

df_ekip = pd.read_excel(r"excels/Ekip_DataBase.xlsx")
df_ekip['Müsaitlik'] = True
df_ekip = df_ekip.sort_values(by="AORT DEĞERLEME", ascending=False)
df_ekip = df_ekip.drop_duplicates()
df_ekip = df_ekip.reset_index(drop=True)

df_ekip['Shift Start (HH:MM) (M)'] = df_ekip['Shift Start (HH:MM) (M)'].astype(str)
df_ekip['Shift End (HH:MM) (M)'] = df_ekip['Shift End (HH:MM) (M)'].astype(str)

df_ekip['Shift Start (HH:MM) (M)'] = pd.to_datetime(df_ekip['Shift Start (HH:MM) (M)']).dt.time
df_ekip['Shift End (HH:MM) (M)'] = pd.to_datetime(df_ekip['Shift End (HH:MM) (M)']).dt.time



ekip_sayisi = 5
G = ox.graph_from_point(center_location, dist=1000, network_type="all")
pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}

selected_nodes = select_random_nodes_with_min_distance(G, len(df_clean), 3, 4)

point_ariza_row = df2.iloc[0]
point_lat, point_lon = point_ariza_row["Latitude(M)"], point_ariza_row["Longitude(M)"]

df_lons_list = df_clean["Longitude(M)"].to_list()
df_lats_list = df_clean["Latitude(M)"].to_list()
selected_nodes = ox.distance.nearest_nodes(G, df_lons_list, df_lats_list)
selected_nodes_set = list(set(selected_nodes))

# ariza_node = selected_nodes[0]
ariza_node = ox.distance.nearest_nodes(G, point_lon, point_lat)
ariza_position = pos.get(ariza_node, None)
ariza_row = df_clean.iloc[0]
ariza_skill_req = ariza_row["Skills Required (comma separated) (O)"].split('-')
ariza_ekipler = list()


for i in range(len(df_ekip)):
    ekip = df_ekip.iloc[i]
    skills = ekip["Skills (Comma separated) (O)"].split(',')
    ekip_quality = skills_compare(ariza_skill_req, skills)
    if ekip_quality and \
        (ekip["Shift Start (HH:MM) (M)"] <=ariza_row["SLA End Time (M)"].time() <= ekip["Shift End (HH:MM) (M)"]) and \
        (ariza_row["SLA End Time (M)"].date()==ekip["Day"].date()):
        ariza_ekipler.append(ekip)

shortest_distances = {}
for idx, ekip in enumerate(ariza_ekipler):
    ekip_lat = ekip['Latitude(M)']
    ekip_lon = ekip['Longitude(M)']
    ekip_node = ox.distance.nearest_nodes(G, ekip_lon, ekip_lat)
    shortest_path_i = nx.shortest_path(G, source=ekip_node, target=ariza_node, weight='length')
    shortest_distance = nx.shortest_path_length(G, ekip_node, ariza_node, weight='length')
    shortest_distances[ekip['Resource ID (M)']] = (shortest_distance, ekip_node, ekip["YETERLİLİK SINIFI"],
                                                   idx, ekip["Name"], ekip["(O)-Surname"], str(ekip["Shift Start (HH:MM) (M)"]),
                                                   str(ekip["Shift End (HH:MM) (M)"]), str(ekip["Day"]).split(' ')[0],
                                                   )
    


sorted_teams = sorted(shortest_distances.items(), key=lambda x: (x[1][0], x[1][2]), reverse=False)  # Mesafe ve yetkinlik sırasına göre sıralama



# 5. Seçilen node a en yakın nodeları çıkar
x_distance = 1
nodes_within_x = nodes_up_to_distance_x(G, ariza_node, x_distance)

# 6. Bu nodeların etrafında kesinti ihbarları oluştur
ihbar_points_x = []
ihbar_points_y = []
musteri_isimleri = []
for node in nodes_within_x:
    node_position = pos.get(node, None)
    if node_position:
        ihbar_sayisi = np.random.randint(10,25)
        random_points = generate_random_points_around_node(node_position, n=ihbar_sayisi, distance_range=0.0002)
        x, y = zip(*random_points)
        ihbar_points_x.append(x)
        ihbar_points_y.append(y)


ihbar_points_x = [item for tuple in ihbar_points_x for item in tuple] # lons
ihbar_points_y = [item for tuple in ihbar_points_y for item in tuple] # lats


node_colors = ['green' if node in selected_nodes_set else 'blue' for node in G.nodes()]
node_sizes = [150 if node in selected_nodes else 20 for node in G.nodes()]

# r"""
node_ekipler = select_random_nodes_with_min_distance(G, ekip_sayisi, 5, 4)


# 8. Calculate the shortest path for each team
total_distance = 1e9
shortest_paths=[]
total_distance_list = []
for node_ekip in node_ekipler:
    shortest_path_i = nx.shortest_path(G, source=node_ekip, target=ariza_node, weight='length')
    total_distance_i = nx.shortest_path_length(G, source=node_ekip, target=ariza_node, weight='length')
    shortest_paths.append(shortest_path_i)
    total_distance_list.append(total_distance_i)
    print("total_distance: ", total_distance_i)
    if total_distance_i<total_distance:
      shortest_path = shortest_path_i
      total_distance = total_distance_i
      

total_distance_list2, shortest_paths2 = map(list, zip(*sorted(zip(total_distance_list, shortest_paths))))

      
# Sort according to distance
distance_dict = {}
for node_ekip in node_ekipler:
    total_distance_i = nx.shortest_path_length(G, source=node_ekip, target=ariza_node, weight='length')
    distance_dict[node_ekip] = total_distance_i
# Sort node_ekipler based on the shortest path distances in descending order
node_ekipler = sorted(node_ekipler, key=lambda x: distance_dict[x], reverse=True)


m = folium.Map(location=center_location, zoom_start = 15)

# Plot bağlantılar
for u, v in G.edges():
    points = [
        [pos[u][1], pos[u][0]],  # (latitude, longitude) for u
        [pos[v][1], pos[v][0]]   # (latitude, longitude) for v
    ]
    folium.PolyLine(points, color='gray', weight=2).add_to(m)


# Plot AG and OG nodes
for node, data in G.nodes(data=True):
    if node in selected_nodes:
        # Selected nodes will be larger, filled with green color
        folium.CircleMarker(
            location=(data['y'], data['x']),
            radius=10,  # larger size for selected nodes
            color='green',  # border color for selected nodes
            fill=True,
            fill_color='green',  # fill color for selected nodes
            fill_opacity=0.8  # opacity of the fill color
        ).add_to(m)
    else:
        # Non-selected nodes will be smaller, filled with blue color
        folium.CircleMarker(
            location=(data['y'], data['x']),
            radius=4,  # smaller size for non-selected nodes
            color='blue',  # border color for non-selected nodes
            fill=True,
            fill_color='blue',  # fill color for non-selected nodes
            fill_opacity=0.6  # opacity of the fill color
        ).add_to(m)

# Plot arıza noktası
if ariza_position:  # ensure the position is not None
    folium.CircleMarker(location=(ariza_position[1], ariza_position[0]), radius=14, color='red',
                        fill=True, fill_opacity=1.0).add_to(m)

ihbar_address = []
# Plot ihbarlar
for (x, y) in zip(ihbar_points_x, ihbar_points_y):
    folium.CircleMarker(location=(y, x), radius=3, color='#FFA500', fill=True).add_to(m)


# Ekibin atanması ve gideceği yol
ii = 0
for shortest_p, node_ekip in zip(shortest_paths, node_ekipler):
    ii+=1
    if shortest_p == shortest_path:
        color = "cyan"
        weight = 9
    else:
        color = "red"
        weight = 5
    for i in range(len(shortest_p)-1):
        u = shortest_p[i]
        v = shortest_p[i+1]
        points = [ [pos[u][1], pos[u][0]], [pos[v][1], pos[v][0]] ]
        folium.PolyLine(points, color=color, weight=weight, zorder = ii).add_to(m)

        loc = pos.get(node_ekip, None)
        folium.CircleMarker(location=(loc[1],loc[0]), radius=7, color='cyan', fill=True).add_to(m)








m.save('map.html')


# r"""


























