import os
import time

import pymysql
from flask import Flask, jsonify

app = Flask(__name__)


DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def wait_for_database():
    for attempt in range(30):
        try:
            connection = get_connection()
            connection.close()
            print("Database is ready.")
            return
        except pymysql.MySQLError as exc:
            print(f"Database not ready, attempt {attempt + 1}/30: {exc}")
            time.sleep(2)

    raise RuntimeError("Database did not become ready within 60 seconds.")


def initialize_database():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS visits (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message VARCHAR(255) NOT NULL
                )
                """
            )

            cursor.execute(
                "INSERT INTO visits (message) VALUES (%s)",
                ("Dhwani DevOps Assignment",),
            )
    finally:
        connection.close()


@app.get("/health")
def health():
    try:
        connection = get_connection()
        connection.close()
        return jsonify(status="healthy", database="connected"), 200
    except pymysql.MySQLError:
        return jsonify(status="unhealthy", database="unavailable"), 503


@app.get("/")
def home():
    return jsonify(
        application="Dhwani DevOps Assignment",
        message="Application is running",
    )


if __name__ == "__main__":
    wait_for_database()
    initialize_database()

    app.run(
        host="0.0.0.0",
        port=8000,
    )