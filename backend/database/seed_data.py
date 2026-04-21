from pathlib import Path
import sys
import argparse

from flask import Flask


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import Config
from database.db import db
from models.product_model import ProductModel
from models.user_model import UserModel
from utils.hash_helper import hash_password


def bootstrap_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def database_has_existing_data():
    users = db.get_collection("users")
    products = db.get_collection("products")
    return users.count_documents({}, limit=1) > 0 or products.count_documents({}, limit=1) > 0


def seed_users():
    users = db.get_collection("users")

    user_documents = [
        UserModel.create_staff("ZestMart Admin", "admin001", hash_password("Admin@123"), "admin"),
        UserModel.create_staff(
            "Rapid Rider", "delivery001", hash_password("Delivery@123"), "delivery"
        ),
        UserModel.create_student(
            "Campus Shopper",
            "9876543210",
            "Boys Hostel Block A, Room 204, North Campus",
            hash_password("Student@123"),
        ),
    ]

    inserted_count = 0
    for document in user_documents:
        lookup = {"phone": document["phone"]} if document.get("phone") else {"userId": document["userId"]}
        if not users.find_one(lookup):
            users.insert_one(document)
            inserted_count += 1

    return inserted_count


def seed_products():
    products = db.get_collection("products")

    sample_products = [
        {"name": "Fresh Apples", "price": 120, "category": "Fruits", "stock": 40},
        {"name": "Whole Wheat Bread", "price": 55, "category": "Bakery", "stock": 30},
        {"name": "Organic Milk", "price": 68, "category": "Dairy", "stock": 25},
        {"name": "Energy Mix Nuts", "price": 180, "category": "Snacks", "stock": 18},
    ]

    inserted_count = 0
    for item in sample_products:
        product_document = ProductModel.create(item)
        if not products.find_one({"name": item["name"]}):
            products.insert_one(product_document)
            inserted_count += 1

    return inserted_count


def parse_args():
    parser = argparse.ArgumentParser(description="Seed sample ZestMart data into MongoDB.")
    parser.add_argument(
        "--only-if-empty",
        action="store_true",
        help="Skip seeding when the database already contains any users or products.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    Config.ensure_directories()
    app = bootstrap_app()
    with app.app_context():
        if args.only_if_empty and database_has_existing_data():
            print("Seed data skipped because the database already contains records.")
            sys.exit(0)

        inserted_users = seed_users()
        inserted_products = seed_products()
    print(
        f"Seed data completed. Inserted users: {inserted_users}. Inserted products: {inserted_products}."
    )
    print("Admin login: userId=admin001 password=Admin@123")
    print("Delivery login: userId=delivery001 password=Delivery@123")
    print("Student login: phone=9876543210 password=Student@123")
