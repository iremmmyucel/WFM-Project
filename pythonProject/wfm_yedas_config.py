import folium
import pandas as pd
import geopy.distance
import contextily as ctx
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
import random
import numpy as np
import time

def predict_repair_time(rp_time):
    return int(np.random.uniform(round(rp_time - (rp_time / 10)), round(rp_time + (rp_time / 10))))

def assign_team(pos):
    secilen_lokasyonlar = random.sample(list(pos.keys()), 3)
    lokasyon_listesi = []
    
    for i, lokasyon in enumerate(secilen_lokasyonlar):
        lokasyon_sozluk = {"id": i+1, "lat": pos[lokasyon][1], "lon": pos[lokasyon][0]}
        lokasyon_listesi.append(lokasyon_sozluk)
    
    return random.choice(lokasyon_listesi)

def generate_random_street_names(num):
    street_names = ['Gül', 'Menekşe', 'Lale', 'Songül', 'Leylak', 'Orkide', 'Süngül']
    random_streets = []
    for _ in range(num):
        random_street = random.choice(street_names) + " Sk"
        random_streets.append(random_street)
    return random_streets

def assign_street_names_to_addresses(addresses, street_names):
    if len(addresses) != len(street_names):
        raise ValueError("Number of addresses and street names must be equal")
    for i in range(len(addresses)):
        addresses[i] = street_names[i] + ", " + addresses[i]
        addresses[i] = addresses[i].replace("Bulvarı", "Blv").replace("Mahallesi", "Mh").replace("Sokak", "Sk")
    return addresses

def get_addresses(latitudes, longitudes):
    geolocator = Nominatim(user_agent="Geopy Library")
    addresses = []
    for lat, lon in zip(latitudes, longitudes):
        location = geolocator.reverse((lat, lon))
        address_parts = location.address.split(',')
        new_address = ','.join(address_parts[:-3])
        addresses.append(new_address)
        time.sleep(0.5)
    return addresses



def skills_compare(ariza_skills, ekip_skills):
    availability = False
    for skill in ariza_skills:
        if skill in ekip_skills:
            availability = True
    return availability

def euclidean_distance(lat1, lon1, lat2, lon2):
    return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

def find_ag_node(center_lat, center_lon, results):
  # En yakın elemanı bulmak için en küçük mesafeyi başlangıçta sonsuz kabul edin
  en_kucuk_mesafe = float('inf')
  en_yakin_eleman = None

  # Her bir elemanın 'lat' ve 'lon' değerlerinin ortalamaya olan uzaklığını kontrol edin
  for ihbar_id, lat, lon, date in results:
      mesafe = euclidean_distance(lat, lon, center_lat, center_lon)
      if mesafe < en_kucuk_mesafe:
          en_kucuk_mesafe = mesafe
          en_yakin_eleman = {"ihbar_id": ihbar_id,
                             "lat":lat,
                             "lon": lon}

  print("En yakın eleman:", en_yakin_eleman)
  return en_yakin_eleman




def nodes_up_to_distance_x(G, starting_node, x):
    """
    Get a list of nodes that are up to x-distance away from the given starting node, including those exactly x-distance away.

    :param G: The graph to search.
    :param starting_node: The node from which distances are measured.
    :param x: The maximum distance from the starting node.
    :return: A list of nodes that are up to x-distance away from the starting node.
    """
    lengths = nx.single_source_shortest_path_length(G, starting_node, cutoff=x)
    return [node for node, length in lengths.items() if length <= x]

def select_random_nodes_with_min_distance(G, N, X, M, max_iterations=1000):
    """
    Select N random nodes from the graph G such that each node is at least X distance away from all previously selected nodes.

    :param G: NetworkX graph from which nodes are selected.
    :param N: The number of nodes to select.
    :param X: The minimum shortest path distance between any two selected nodes.
    :return: A list of selected nodes.
    """
    selected_nodes = []
    nodes_list = [node for node in G.nodes() if G.degree(node) >= M]

    iterations = 0
    while len(selected_nodes) < N and nodes_list  and iterations < max_iterations:
      try:
        node = random.choice(nodes_list)
        if all(nx.shortest_path_length(G, source=node, target=selected) >= X for selected in selected_nodes):
            selected_nodes.append(node)
        nodes_list.remove(node)
        iterations += 1
      except:
        iterations += 1
        pass

    return selected_nodes

def generate_random_points_around_node(node_position, n, distance_range):
    """
    Generate n random points around a given node_position.

    :param node_position: A tuple (x, y) representing the node's position.
    :param n: The number of random points to generate.
    :param distance_range: The maximum distance range for points around the node.
    :return: A list of n random points (tuples) around the node.
    """
    x, y = node_position
    random_points = []

    for _ in range(n):
        random_offset_x = np.random.uniform(-distance_range, distance_range)
        random_offset_y = np.random.uniform(-distance_range, distance_range)
        random_point = (x + random_offset_x, y + random_offset_y)
        random_points.append(random_point)

    return random_points


def musteri_isimleri_uret(N):
    def generate_turkish_name():
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        return f"{first_name} {last_name}"
    # Expanded lists of Turkish first and last names
    first_names = [
        'Emir', 'Ahmet', 'Mehmet', 'Ayşe', 'Elif', 'Zeynep', 'Yusuf', 'Can', 'Deniz', 'Fatma',
        'Ali', 'Hüseyin', 'Hasan', 'Murat', 'Ömer', 'Mustafa', 'Cem', 'Kerem', 'Halil', 'Selin',
        'Cansu', 'Işıl', 'Ece', 'Seda', 'Hande', 'Sinem', 'Oğuz', 'Kaan', 'Barış', 'Volkan',
        'Serdar', 'Onur', 'Burak', 'Tolga', 'Emre', 'Berk', 'Taylan', 'Umut', 'Rıza', 'Selim',
        'Derya', 'Nur', 'Esra', 'Hakan', 'Gizem', 'Merve', 'Büşra', 'Tuba', 'Aslı', 'Kübra'
    ]

    last_names = [
        'Yılmaz', 'Kaya', 'Demir', 'Şahin', 'Çelik', 'Turan', 'Öztürk', 'Aydın', 'Polat', 'Aslan',
        'Tekin', 'Güler', 'Kara', 'Koç', 'Yıldız', 'Yıldırım', 'Erbil', 'Erdoğan', 'Durmaz', 'Özdemir',
        'Kılıç', 'Çetin', 'Bayrak', 'Varol', 'Taş', 'Kurt', 'Özkan', 'Karadağ', 'Dağ', 'Sarı',
        'Çiftçi', 'Bulut', 'Kaplan', 'Dinç', 'Aksoy', 'Demirel', 'Güneş', 'Keskin', 'Gündüz', 'Coşkun',
        'Akar', 'Avcı', 'Çakır', 'Dönmez', 'Engin', 'Yalçın', 'Kalkan', 'Keser', 'Toprak', 'Demirkıran'
    ]

    # Generate N random Turkish names
    random_turkish_names_expanded = [generate_turkish_name() for _ in range(N)]
    return random_turkish_names_expanded


if __name__ == '__main__':
    pass