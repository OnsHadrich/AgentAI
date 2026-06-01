# test_mongodb.py
from database.mongodb import MongoDB


try:
    MongoDB.connect()
    db = MongoDB.get_db()
    client = MongoDB.get_client()

    client.server_info()
    print("MongoDB connected successfully")
    print(f"Database: {db.name}")
    print(f"Collections: {db.list_collection_names()}")
except Exception as e:
    print(f"Connection failed: {e}")
finally:
    MongoDB.close()
