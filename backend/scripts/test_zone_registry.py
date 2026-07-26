from app.domain.geography import City, Coordinates, Zone


city = City(
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

city.add_zone(airport_zone)

print("City:", city.name)
print("Zone count:", city.zone_count())
print("Airport exists:", city.zone_registry.exists("Sofia Airport"))
print("Unknown exists:", city.zone_registry.exists("Unknown"))
print("Zone:", city.get_zone("Sofia Airport").name)
