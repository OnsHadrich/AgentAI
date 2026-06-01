from pymongo import MongoClient
from pymongo.database import Database
from core.config import Configs

configs = Configs()


class MongoDB:
    client: MongoClient | None = None
    db: Database | None = None

    @classmethod
    def connect(cls):
        cls.client = MongoClient(configs.MONGODB_URI)
        cls.db = cls.client[configs.MONGODB_DB]
        print(f"MongoDB connected ✓ (db: {configs.MONGODB_DB})")

    @classmethod
    def close(cls):
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed ✓")

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            raise RuntimeError("MongoDB client was not initialized")
        return cls.client

    @classmethod
    def get_db(cls) -> Database:
        if cls.db is None:
            cls.connect()
        if cls.db is None:
            raise RuntimeError("MongoDB connection was not initialized")
        return cls.db
