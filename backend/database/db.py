import logging

from pymongo import ASCENDING, MongoClient


logger = logging.getLogger(__name__)


class MongoDatabase:
    def __init__(self):
        self.client = None
        self.database = None

    def init_app(self, app):
        # Return BSON datetimes as UTC-aware values so expiry checks stay consistent.
        self.client = MongoClient(app.config["MONGO_URI"], tz_aware=True)
        self.database = self.client[app.config["MONGO_DB_NAME"]]
        self._ensure_indexes()
        logger.info("MongoDB connected: %s", app.config["MONGO_DB_NAME"])

    def get_collection(self, name):
        if self.database is None:
            raise RuntimeError("Mongo database has not been initialized.")
        return self.database[name]

    def _ensure_indexes(self):
        self.get_collection("users").create_index(
            [("phone", ASCENDING)], unique=True, sparse=True
        )
        self.get_collection("users").create_index(
            [("userId", ASCENDING)], unique=True, sparse=True
        )
        self.get_collection("users").create_index([("role", ASCENDING)])

        self.get_collection("otps").create_index(
            [("phone", ASCENDING)], unique=True, sparse=True
        )
        self.get_collection("otps").create_index(
            [("expiresAt", ASCENDING)], expireAfterSeconds=0
        )
        self.get_collection("otp_rate_limits").create_index(
            [("phone", ASCENDING)], unique=True, sparse=True
        )
        self.get_collection("otp_rate_limits").create_index(
            [("windowExpiresAt", ASCENDING)], expireAfterSeconds=0
        )

        self.get_collection("products").create_index([("category", ASCENDING)])
        self.get_collection("products").create_index([("name", ASCENDING)])

        self.get_collection("orders").create_index([("status", ASCENDING)])
        self.get_collection("orders").create_index([("userId", ASCENDING)])
        self.get_collection("orders").create_index([("deliveryPersonId", ASCENDING)])


db = MongoDatabase()
