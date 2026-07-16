from app.domain.geography import City, Coordinates, Region, Zone


region = Region(name="Bulgaria")

sofia = City(
    name="Sofia",
    country="Bulgaria",
)

airport_zone = Zone(
    name="Sofia Airport",
    city="Sofia",
    country="Bulgaria",
    coordinates=Coordinates(
        latitude=42.6967,
        longitude=23.4114,
    ),
)

sofia.add_zone(airport_zone)
region.add_city(sofia)

print("Region:", region.name)
print("Cities:", region.city_count())
print("City:", region.get_city("Sofia").name)
print("Zones in Sofia:", region.get_city("Sofia").zone_count())
print("First zone:", region.get_city("Sofia").get_zone("Sofia Airport").name)
