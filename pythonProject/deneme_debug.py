from geopy.geocoders import Nominatim

# Initialize Nominatim API
geolocator = Nominatim(user_agent="geoapiExercises")

# Latitude & Longitude input
latitude = "51.5074"
longitude = "-0.1278"

# Get location with geocode
location = geolocator.reverse((latitude, longitude))

# Print the location
print(location.address)
