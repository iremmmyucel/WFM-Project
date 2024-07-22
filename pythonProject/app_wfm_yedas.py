from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import random
import osmnx as ox
import folium
import contextily as ctx
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import random
from wfm_yedas_config import *
from flask_cors import CORS
import math
import pandas as pd
import mysql.connector
import time
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from threading import Lock

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app)
thread = None
thread_lock = Lock()

center_location = 41.19732911223483, 36.719378543270956
G = ox.graph_from_point(center_location, dist=500, network_type="drive")
pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
selected_nodes = select_random_nodes_with_min_distance(G, 20, 3, 4)

ihbar_points_x=[]
ihbar_points_y=[]

# Örnek veriler


df1 = pd.read_excel(r"excels/result_wfm.xlsx")
df1 = df1.sample(frac=1).reset_index(drop=True)

df2 = df1.sort_values(by="Score", ascending=False)
df2.reset_index(drop=True, inplace=True)


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

df_ekip = pd.read_excel(r"excels/Ekip_DataBase.xlsx")
df_ekip['Müsaitlik'] = True
df_ekip = df_ekip.sort_values(by="AORT DEĞERLEME", ascending=False)
df_ekip = df_ekip.drop_duplicates()
df_ekip = df_ekip.reset_index(drop=True)

df_ekip['Shift Start (HH:MM) (M)'] = df_ekip['Shift Start (HH:MM) (M)'].astype(str)
df_ekip['Shift End (HH:MM) (M)'] = df_ekip['Shift End (HH:MM) (M)'].astype(str)

# Convert 'Shift Start (HH:MM) (M)' to time format
df_ekip['Shift Start (HH:MM) (M)'] = pd.to_datetime(df_ekip['Shift Start (HH:MM) (M)'], format='%H:%M:%S').dt.time

# Conditional conversion for 'Shift End (HH:MM) (M)'
df_ekip['Shift End (HH:MM) (M)'] = df_ekip['Shift End (HH:MM) (M)'].apply(
    lambda x: pd.to_datetime(x.split()[-1], format='%H:%M:%S').time() if '1900' in x else pd.to_datetime(x, format='%H:%M:%S').time()
)


ekip_sayisi = 10
G = ox.graph_from_point(center_location, dist=1400, network_type="drive")
pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}

selected_nodes = select_random_nodes_with_min_distance(G, len(df_clean), 3, 4)

df_lons_list = df_clean["Longitude(M)"].to_list()
df_lats_list = df_clean["Latitude(M)"].to_list()
selected_nodes = ox.distance.nearest_nodes(G, df_lons_list, df_lats_list)
selected_nodes_set = list(set(selected_nodes))


point_ariza_row = df2.iloc[0]
point_lat, point_lon = point_ariza_row["Latitude(M)"], point_ariza_row["Longitude(M)"]

ariza_node = ox.distance.nearest_nodes(G, point_lon, point_lat)
ariza_position = pos.get(ariza_node, None)
index_of_row = (df_clean['Activity ID (M)'] == point_ariza_row["Activity ID (M)"]).idxmax()
ariza_row = df_clean.iloc[index_of_row]
print("**" * 10)
print(ariza_row)
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
                                                   str(ekip["Shift End (HH:MM) (M)"]), str(ekip["Day"]).split(' ')[0])
    


sorted_teams = sorted(shortest_distances.items(), key=lambda x: (x[1][0], x[1][2]), reverse=False)  # Mesafe ve yetkinlik sırasına göre sıralama

# 5. Seçilen node a en yakın nodeları çıkar
x_distance = 1
nodes_within_x = nodes_up_to_distance_x(G, ariza_node, x_distance)

# 6. Bu nodeların etrafında kesinti ihbarları oluştur, database bağlantısı
def get_db_connection():
    conn = mysql.connector.connect(
        host="3.71.18.135",
        user="furkan-ecevit",
        password="arge1234",
        database="wfmdb"
    )
    return conn

latest_ihbar_id = None
def check_new_ihbarlar():
    global latest_ihbar_id
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("latest_ihbar_id: ", latest_ihbar_id)

        if latest_ihbar_id is None:
            cursor.execute("SELECT ihbar_id FROM ihbarlar ORDER BY ihbar_id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                latest_ihbar_id = result[0]
                cursor.execute("SELECT ihbar_id, lat, lon, ihbar_date FROM ihbarlar ORDER BY ihbar_id ASC")
                results = cursor.fetchall()
                if results:
                    lat_list = [lat for ihbar_id, lat, lon, date in results]
                    lon_list = [lon for ihbar_id, lat, lon, date in results]
                    ortalama_lat = sum(lat_list) / len(lat_list)
                    ortalama_lon = sum(lon_list) / len(lon_list)
                    date_now = datetime.now() - timedelta(hours=3)
                    new_ihbarlar = [{'id': ihbar_id, 'lat': lat, 'lon': lon, 'date': date.strftime("%Y-%m-%d %H:%M:%S")} for ihbar_id, lat, lon, date in results]
                    latest_ihbar_id = results[-1][0]
                    socketio.emit('update_latest_ihbar_id', latest_ihbar_id)
                    ag_node = find_ag_node(ortalama_lat, ortalama_lon, results)
                    print("position: ", pos)
                    print()
                    print(type(pos))
                    team = assign_team(pos)

                    if new_ihbarlar:
                        for item in new_ihbarlar:
                            print(item["date"], date_now, (date_now - datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S")).total_seconds())
                        socketio.emit('new_ihbarlar', new_ihbarlar)
                        socketio.emit('ag_node', ag_node)
                        socketio.emit('team', team)
                        print("new_ihbarlar: ", len(new_ihbarlar))
                        print()
        else:
            cursor.execute("SELECT ihbar_id, lat, lon, ihbar_date FROM ihbarlar WHERE ihbar_id > %s ORDER BY ihbar_id ASC", (latest_ihbar_id,))
            results = cursor.fetchall()
            if results:
                lat_list = [lat for ihbar_id, lat, lon, date in results]
                lon_list = [lon for ihbar_id, lat, lon, date in results]
                ortalama_lat = sum(lat_list) / len(lat_list)
                ortalama_lon = sum(lon_list) / len(lon_list)
                date_now = datetime.now() - timedelta(hours=3)
                new_ihbarlar = [{'id': ihbar_id, 'lat': lat, 'lon': lon, 'date': date.strftime("%Y-%m-%d %H:%M:%S")} for ihbar_id, lat, lon, date in results]
                latest_ihbar_id = results[-1][0]
                socketio.emit('update_latest_ihbar_id', latest_ihbar_id)
                ag_node = find_ag_node(ortalama_lat, ortalama_lon, results)
                team = assign_team(pos)

                if new_ihbarlar:
                    for item in new_ihbarlar:
                        print(item["date"], date_now, (date_now - datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S")).total_seconds())
                    socketio.emit('new_ihbarlar', new_ihbarlar)
                    socketio.emit('ag_node', ag_node)
                    socketio.emit('team', team)
                    print("new_ihbarlar: ", len(new_ihbarlar))
            # else:
            #     print("Yeni İhbar Yok..")

        cursor.close()
        conn.close()

        socketio.sleep(0.0001)

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(check_new_ihbarlar)


# r"""
node_ekipler = select_random_nodes_with_min_distance(G, ekip_sayisi, 5, 4)

def get_ihbar_points():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lat, lon FROM ihbarlar")
    results = cursor.fetchall()
    conn.close()
    ihbar_points_x = [lat for lat, lon in results]
    ihbar_points_y = [lon for lat, lon in results]
    return ihbar_points_x, ihbar_points_y


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
      

total_distance_list, shortest_paths = map(list, zip(*sorted(zip(total_distance_list, shortest_paths))))

      
# Sort according to distance
distance_dict = {}

for node_ekip in node_ekipler:
    total_distance_i = nx.shortest_path_length(G, source=node_ekip, target=ariza_node, weight='length')
    distance_dict[node_ekip] = total_distance_i
# Sort node_ekipler based on the shortest path distances in descending order
node_ekipler = sorted(node_ekipler, key=lambda x: distance_dict[x], reverse=True)


# addresses = get_addresses(ihbar_points_y, ihbar_points_x)
# addresses_with_streets = assign_street_names_to_addresses(addresses, street_names)
addresses_with_streets=[]

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_polylines = []
    for u, v in G.edges():
        points = [
            [pos[u][1], pos[u][0]],  # (latitude, longitude) for u
            [pos[v][1], pos[v][0]]   # (latitude, longitude) for v
        ]
        plot_polylines.append(points)
    
    g_nodes = list(G.nodes(data=True))
    df_clean_copy = df_clean.copy()
    df_clean_copy = df_clean_copy.sort_values(by="Completion Time (O)", ascending=True)
    is_emri_list = df_clean_copy.values.tolist()
    print(is_emri_list[0])
    ariza_row_list = [ariza_row["Activity ID (M)"],ariza_row["Type (M)"], ariza_row["Latitude(M)"], ariza_row["Longitude(M)"], sorted_teams[0][0],
                      (pd.to_datetime(ariza_row["Completion Time (O)"], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(ariza_row["Arrival Time (O)"], format='%d.%m.%Y %H:%M:%S')).total_seconds(),
                      ariza_row["Skills Required (comma separated) (O)"], str(ariza_row["Arrival Time (O)"]), str(ariza_row["Arrival Time (O)"] + pd.Timedelta(seconds=predict_repair_time(ariza_row["Repair Time"]))), str(predict_repair_time(ariza_row["Repair Time"]))]
    print("**" * 10)
    print("Ariza Row List: ", ariza_row_list)
    
    ihbar_points_x, ihbar_points_y = get_ihbar_points()
    street_names = generate_random_street_names(len(ihbar_points_y))
    musteriler = musteri_isimleri_uret(len(ihbar_points_x))

    return render_template('index4.html', plot_polylines=plot_polylines,g_nodes=g_nodes, selected_nodes=selected_nodes,
                           ariza_position=ariza_position, ihbar_points_x=ihbar_points_x, ihbar_points_y=ihbar_points_y,
                           node_ekipler=node_ekipler, pos=pos, shortest_path=shortest_path, shortest_paths=shortest_paths,
                           sorted_teams=sorted_teams[:ekip_sayisi], musteriler=musteriler, addresses_with_streets=addresses_with_streets,
                           is_emri_list=is_emri_list[:15], ariza_row=ariza_row_list, df1=df1, df2=df2, total_distance_list=total_distance_list
                           )




def safe_convert(value):
    """Convert non-serializable types to Python-native types."""
    if isinstance(value, (np.integer, int)):
        return int(value)
    elif isinstance(value, (np.floating, float)):
        return float(value) if not math.isnan(value) else None
    elif isinstance(value, pd.Timestamp):
        return str(value)
    # Check for NaN only if the value is a number
    elif isinstance(value, (float, np.floating)) and math.isnan(value):
        return None
    return value


@app.route('/api/data', methods=['GET'])
def get_data():
    plot_polylines = [[[pos[u][1], pos[u][0]], [pos[v][1], pos[v][0]]] for u, v in G.edges()]
    
    g_nodes = [(safe_convert(node), data) for node, data in G.nodes(data=True)]
    
    df_clean_copy = df_clean.copy()
    df_clean_copy.replace({np.nan: None}, inplace=True)  # Replace NaN with None
    is_emri_list = df_clean_copy.applymap(safe_convert).values.tolist()
    
    ariza_row_list = [
        safe_convert(ariza_row["Activity ID (M)"]),
        safe_convert(ariza_row["Type (M)"]),
        safe_convert(ariza_row["Latitude(M)"]),
        safe_convert(ariza_row["Longitude(M)"]),
        sorted_teams[0][0],
        safe_convert(
            (pd.to_datetime(ariza_row["Completion Time (O)"], format='%d.%m.%Y %H:%M:%S') -
             pd.to_datetime(ariza_row["Arrival Time (O)"], format='%d.%m.%Y %H:%M:%S')).total_seconds()
        ),
        ariza_row["Skills Required (comma separated) (O)"],
        str(ariza_row["Arrival Time (O)"]),
        str(ariza_row["Arrival Time (O)"] + pd.Timedelta(seconds=predict_repair_time(ariza_row["Repair Time"]))),
        str(predict_repair_time(ariza_row["Repair Time"]))
    ]

    data = {
        'plot_polylines': plot_polylines,
        'g_nodes': g_nodes,
        'selected_nodes': selected_nodes,
        'ariza_position': safe_convert(ariza_position),
        'ihbar_points_x': list(map(safe_convert, ihbar_points_x)),
        'ihbar_points_y': list(map(safe_convert, ihbar_points_y)),
        'node_ekipler': node_ekipler,
        'pos': {k: list(map(safe_convert, v)) for k, v in pos.items()},
        'shortest_path': list(map(safe_convert, shortest_path)),
        'shortest_paths': [list(map(safe_convert, path)) for path in shortest_paths],
        'sorted_teams': [team for team in sorted_teams[:ekip_sayisi]],
        'musteriler': musteriler,
        'addresses_with_streets': addresses_with_streets,
        'is_emri_list': is_emri_list[:15],
        'ariza_row': ariza_row_list,
        'df1': df1.applymap(safe_convert).values.tolist(),
        'df2': df2.applymap(safe_convert).values.tolist(),
        'total_distance_list': list(map(safe_convert, total_distance_list))
    }
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True, port=3000)