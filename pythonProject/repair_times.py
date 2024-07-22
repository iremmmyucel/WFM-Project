import pandas as pd
import matplotlib.pyplot as plt


df_kesinti = pd.read_excel(r"excels/DataBase.xlsx")
df_kesinti = df_kesinti.sort_values(by="Priority (1-10) (O)", ascending=True)

df_kesinti['Latitude(M)'] = df_kesinti['Latitude(M)'].str.replace(',', '.')
df_kesinti['Longitude(M)'] = df_kesinti['Longitude(M)'].str.replace(',', '.')

df_kesinti["Completion Time (O)"] = pd.to_datetime(df_kesinti["Completion Time (O)"], format='%d.%m.%Y %H:%M:%S')
df_kesinti["Arrival Time (O)"] = pd.to_datetime(df_kesinti["Arrival Time (O)"], format='%d.%m.%Y %H:%M:%S')


df_kesinti = df_kesinti.reset_index(drop=True)



df_kesinti['Completion Time (O)'] = pd.to_datetime(df_kesinti['Completion Time (O)'])
df_kesinti['Arrival Time (O)'] = pd.to_datetime(df_kesinti['Arrival Time (O)'])

# Tamir sürelerini hesapla
df_kesinti['Repair Time'] = pd.to_timedelta(df_kesinti['Completion Time (O)'] - df_kesinti['Arrival Time (O)'])
df_kesinti['Repair Time (Seconds)'] = df_kesinti['Repair Time'].dt.total_seconds()

# Ekip bazında ortalama tamir sürelerini hesapla
avg_repair_time_by_team_and_type = df_kesinti.groupby(['Resource ID (O)', 'Type (M)'])['Repair Time (Seconds)'].mean()
avg_repair_time_by_team_and_type_sorted = avg_repair_time_by_team_and_type.sort_values()

# Ekip, arıza tipi ve lokasyon bazında ortalama tamir sürelerini hesapla
avg_repair_time_by_team_type_and_location = df_kesinti.groupby(['Resource ID (O)', 'Type (M)', 'Latitude(M)', 'Longitude(M)'])['Repair Time (Seconds)'].mean()


avg_repair_time_by_team_and_type_sorted.plot(kind='bar', figsize=(10, 6), color='skyblue')
plt.title('Ekip ve Arıza Tipine Göre Ortalama Tamir Süresi')
plt.xlabel('Ekip ve Arıza Tipi')
plt.ylabel('Ortalama Tamir Süresi (Saniye)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()



# DataFrame'i Excel dosyasına dönüştür
avg_repair_time_by_team_type_and_location_df = avg_repair_time_by_team_type_and_location.reset_index()  # Gruplama indekslerini sütunlara dönüştür

# Excel dosyasına yazdır
avg_repair_time_by_team_type_and_location_df.to_excel("regression_parameters.xlsx", index=False)  # index=False, DataFrame indekslerini Excel'e yazmaz
