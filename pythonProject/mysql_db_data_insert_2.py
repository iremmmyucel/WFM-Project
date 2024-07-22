import geopy.distance
import contextily as ctx
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
import random
import numpy as np
import time
import mysql.connector

conn = mysql.connector.connect(
    host="3.71.18.135",
    user="furkan-ecevit",
    password="arge1234",
    database="wfmdb"
)
cursor = conn.cursor()

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


# İhbarlar
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

center_location = 41.19732911223483, 36.719378543270956
G = ox.graph_from_point(center_location, dist=500, network_type="drive")
pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
selected_nodes = select_random_nodes_with_min_distance(G, 20, 3, 4)
ariza_node = selected_nodes[5]
ariza_position = pos.get(ariza_node, None)
nodes_within_x = nodes_up_to_distance_x(G, ariza_node, 1)


ihbar_data = []

ihbar_points_x = []
ihbar_points_y = []

for node in nodes_within_x:
    node_position = pos.get(node, None)
    ihbar_sayisi = np.random.randint(10,25)
    random_points = generate_random_points_around_node(node_position, n=ihbar_sayisi, distance_range=0.0002)
    x, y = zip(*random_points)
    ihbar_points_x.append(x)
    ihbar_points_y.append(y)

print("İHBARLAR HAZIR")
ihbar_points_x = [item for tuple in ihbar_points_x for item in tuple]
ihbar_points_y = [item for tuple in ihbar_points_y for item in tuple]
combined = list(zip(ihbar_points_y, ihbar_points_x))

cursor.executemany("INSERT INTO wfmdb.ihbarlar (lat, lon) VALUES (%s, %s)", combined)
conn.commit()
cursor.close()
conn.close()
print("İHBARLAR EKLENDİ")


