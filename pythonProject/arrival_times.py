import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt


df = pd.read_excel(r"excels/DataBase.xlsx")
df["Start Travel Time (O)"] = pd.to_datetime(df["Start Travel Time (O)"], format='%d.%m.%Y %H:%M:%S')
df["Arrival Time (O)"] = pd.to_datetime(df["Arrival Time (O)"], format='%d.%m.%Y %H:%M:%S')
df["Date Time"] = pd.to_datetime(df["Start Travel Time (O)"], format='%d.%m.%Y').dt.date

# "SLA Start Time (O)" sütununa göre sıralama yapalım
df = df.sort_values(by="Start Travel Time (O)")

grouped_df = df.groupby(['Type (M)','Resource ID (O)', 'Latitude(M)', 'Longitude(M)', 'Date Time'])
filtered_df = grouped_df.apply(lambda x: x.loc[x['Start Travel Time (O)'].idxmin()])


filtered_df['Travel Duration'] = filtered_df['Arrival Time (O)'] - filtered_df['Start Travel Time (O)']

saniyeler_listesi = [duration.total_seconds() for duration in filtered_df['Travel Duration']]
sayac = Counter(saniyeler_listesi)


for idx, item in enumerate(saniyeler_listesi):
    if item == 796625.0:
        print(idx, filtered_df.iloc[idx]["Activity ID (M)"])
        

plt.bar(sayac.keys(), sayac.values())

# Eksen isimlerini ve başlığı ekleyelim
plt.xlabel('Saniye')
plt.ylabel('Frekans')
plt.title('Saniye Dağılımı')

# Grafiği gösterelim
plt.show()