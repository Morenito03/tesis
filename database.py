# database.py
from motor.motor_asyncio import AsyncIOMotorClient

# URL de conexión (ajústala a tu configuración)
MONGO_URI = "mongodb://localhost:27017"

# Nombre de la base de datos
DB_NAME = "smartwatch_db"

client = AsyncIOMotorClient(MONGO_URI)
database = client[DB_NAME]

# Colección para almacenar los resultados del sensor
sensor_collection = database["resultados_sensor"]
