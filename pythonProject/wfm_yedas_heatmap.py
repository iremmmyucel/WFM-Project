import folium
import pandas as pd
from folium.plugins import HeatMap


r"""
## NORMAL DATA
# Veri setini oku
df = pd.read_excel(r"excels/DataBase.xlsx")

# Eksik değerleri temizle
df.dropna(subset=["Latitude(M)", "Longitude(M)"], inplace=True)

# Latitude(M) ve Longitude(M) sütunlarını float'a dönüştür
df["Latitude(M)"] = df["Latitude(M)"].str.replace(',', '.').astype(float)
df["Longitude(M)"] = df["Longitude(M)"].str.replace(',', '.').astype(float)

# Ortalama enlem ve boylamı al
mean_lat = df["Latitude(M)"].mean()
mean_lon = df["Longitude(M)"].mean()

# Haritayı oluştur
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=8)

# Her bir konum için bir daire işareti oluştur
for index, row in df.iterrows():
    folium.CircleMarker(
        location=(row["Latitude(M)"], row["Longitude(M)"]),
        radius=4,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.8
    ).add_to(m)


lat1, lon1 = 41.2084703171146, 36.5507921965479
folium.CircleMarker(
    location=(lat1, lon1),
    radius=12,
    color='red',
    fill=True,
    fill_color='red',
    fill_opacity=0.8
).add_to(m)

# Haritayı kaydet
m.save("deneme.html")
r"""





## HEATMAP
# Veri setini oku
df = pd.read_excel(r"excels/DataBase.xlsx")

# Eksik değerleri temizle
df.dropna(subset=["Latitude(M)", "Longitude(M)"], inplace=True)

carsamba = df[(df["Address 1 (O)"] == "ÇARŞAMBA") & (df["Address 2 (O)"] == "BEYLERCE MH.")]

# Latitude(M) ve Longitude(M) sütunlarını float'a dönüştür
df["Latitude(M)"] = df["Latitude(M)"].str.replace(',', '.').astype(float)
df["Longitude(M)"] = df["Longitude(M)"].str.replace(',', '.').astype(float)

# Harita oluştur
m = folium.Map(location=[df["Latitude(M)"].mean(), df["Longitude(M)"].mean()], zoom_start=8)

# Yoğunluk haritası oluştur
heat_map = HeatMap(data=df[['Latitude(M)', 'Longitude(M)']], radius=15)

# Haritaya ekle
m.add_child(heat_map)
lat1, lon1 = 41.19732911223483, 36.719378543270956

folium.CircleMarker(
    location=(lat1, lon1),
    radius=12,
    color='red',
    fill=True,
    fill_color='red',
    fill_opacity=0.8
).add_to(m)



# Haritayı kaydet
m.save("heat_map.html")

