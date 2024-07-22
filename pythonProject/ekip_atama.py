import pandas as pd
import osmnx as ox
import networkx as nx
from geopy.distance import geodesic

def skills_compare(ariza_skills, ekip_skills):
    availability = False
    for skill in ariza_skills:
        if skill in ekip_skills:
            availability = True
    return availability




df_kesinti = pd.read_excel(r"excels/DataBase.xlsx")
df_ekip = pd.read_excel(r"excels/Ekip_DataBase.xlsx")
df_ekip['Müsaitlik'] = True

df_ekip = df_ekip.sort_values(by="AORT DEĞERLEME", ascending=False)
df_kesinti = df_kesinti.sort_values(by="Priority (1-10) (O)", ascending=True)
# 'Latitude(M)' ve 'Longitude(M)' sütunlarını virgülü noktaya dönüştür
df_kesinti['Latitude(M)'] = df_kesinti['Latitude(M)'].str.replace(',', '.')
df_kesinti['Longitude(M)'] = df_kesinti['Longitude(M)'].str.replace(',', '.')

# Şimdi sütunları ondalıklı sayılara dönüştür ve ortalamasını al
latitude_mean = df_kesinti['Latitude(M)'].astype(float).mean()
longitude_mean = df_kesinti['Longitude(M)'].astype(float).mean()



df_cleaned = df_ekip.drop_duplicates()
df_cleaned = df_cleaned.reset_index(drop=True)

df_cleaned['Shift Start (HH:MM) (M)'] = df_cleaned['Shift Start (HH:MM) (M)'].astype(str)
df_cleaned['Shift End (HH:MM) (M)'] = df_cleaned['Shift End (HH:MM) (M)'].astype(str)

df_cleaned['Shift Start (HH:MM) (M)'] = pd.to_datetime(df_cleaned['Shift Start (HH:MM) (M)']).dt.time
df_cleaned['Shift End (HH:MM) (M)'] = pd.to_datetime(df_cleaned['Shift End (HH:MM) (M)']).dt.time



ariza = df_kesinti.iloc[0]
ariza_skill_req = ariza["Skills Required (comma separated) (O)"].split('-')
ariza_ekipler = list()

for i in range(len(df_cleaned)):
    ekip = df_cleaned.iloc[i]
    skills = ekip["Skills (Comma separated) (O)"].split(',')
    ekip_quality = skills_compare(ariza_skill_req, skills)
    if ekip_quality and \
        (ekip["Shift Start (HH:MM) (M)"] <=ariza["SLA End Time (M)"].time() <= ekip["Shift End (HH:MM) (M)"]) and \
        (ariza["SLA End Time (M)"].date()==ekip["Day"].date()):
        ariza_ekipler.append(ekip)



G = ox.graph_from_point((latitude_mean, longitude_mean), dist=10000, network_type='all')
pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}

shortest_distances = {}
for ekip in ariza_ekipler:
    ekip_lat = ekip['Latitude(M)']
    ekip_lon = ekip['Longitude(M)']
    ekip_node = ox.distance.nearest_nodes(G, ekip_lon, ekip_lat)
    ariza_node = ox.distance.nearest_nodes(G, float(ariza["Longitude(M)"]), float(ariza["Latitude(M)"]))
    shortest_path_i = nx.shortest_path(G, source=ekip_node, target=ariza_node, weight='length')
    shortest_distance = nx.shortest_path_length(G, ekip_node, ariza_node, weight='length')
    shortest_distances[ekip['Resource ID (M)']] = shortest_distance

closest_ekip_id = min(shortest_distances, key=shortest_distances.get)
closest_ekip_distance = shortest_distances[closest_ekip_id]

print(f"En yakın ekip: {closest_ekip_id}, Uzaklık: {closest_ekip_distance} metre")
