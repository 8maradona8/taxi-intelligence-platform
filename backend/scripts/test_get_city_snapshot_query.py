from app.application.queries import GetCitySnapshotQuery


query = GetCitySnapshotQuery(
    city_name="Sofia",
)

print("Query city:", query.city_name)