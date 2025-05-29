from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask import Flask
from urllib.parse import quote
from sqlalchemy import text

load_dotenv()

# URL-encode the password to handle special characters
password = os.environ.get('MYSQL_PASSWORD', 'Beki123')
encoded_password = quote(password)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'root')}:{encoded_password}@"
    f"{os.environ.get('MYSQL_HOST', 'localhost')}/{os.environ.get('MYSQL_DATABASE', 'server_management')}"
)

db = SQLAlchemy(app)

with app.app_context():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # Wrap query in text()
            print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
