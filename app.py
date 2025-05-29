from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from dotenv import load_dotenv # type: ignore
import os
import bcrypt # type: ignore
import pymysql # type: ignore
from urllib.parse import quote_plus
import subprocess

import logging
from sqlalchemy import text # type: ignore

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure the app using the Config class
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "2e5dc5d30af1e18ca586c304490423a7")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'root')}:{quote_plus(os.environ.get('MYSQL_PASSWORD', 'Beki123'))}@"
        f"{os.environ.get('MYSQL_HOST', 'localhost')}/{os.environ.get('MYSQL_DATABASE', 'server_management')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Apply the configuration to the Flask app
app.config.from_object(Config)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define Models
class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'name': self.name,
            'port': self.port
        }


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# Initialize the database
def init_db():
    with app.app_context():
        logger.info("Attempting to connect to the database...")
        try:
            # Verify the database exists by querying the database session
            db.session.execute(text('SELECT 1'))  # Use the text() function for raw SQL query
            db.session.commit()  # Ensure the connection is established properly
            logger.info("Database connection successful!")

            # Create tables if they don't exist
            logger.info("Attempting to create tables...")
            db.create_all()
            logger.info("Tables created successfully.")

            # Add default admin user if not exists
            admin = Admin.query.filter_by(username="admin").first()
            if not admin:
                logger.info("Adding default admin user...")
                hashed_password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
                new_admin = Admin(username="admin", password=hashed_password.decode("utf-8"))
                db.session.add(new_admin)
                db.session.commit()
                logger.info("Default admin user added successfully.")
            else:
                logger.info("Default admin user already exists.")

        except Exception as e:
            db.session.rollback()  # Rollback in case of errors
            logger.error(f"Error initializing database: {e}")
            raise Exception("An unexpected error occurred during database initialization.")


# Call init_db() to initialize the database
try:
    init_db()
except Exception as e:
    logger.error(f"Initialization failed: {e}")
    exit(1)  # Exit the application if initialization fails


# Validate IP address
def validate_ip(ip):
    try:
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True
    except Exception as e:
        logger.error(f"Error in IP validation: {e}")
        return False


# Routes
@app.route("/")
def index():
    if "logged_in" in session:
        return render_template("admin.html")
    return render_template("guest.html")


@app.route("/list")
def get_servers():
    try:
        servers = Server.query.all()
        return jsonify([server.to_dict() for server in servers])
    except Exception as e:
        logger.error(f"Error fetching servers: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route("/add", methods=["POST"])
def add_server():
    if "logged_in" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    ip = data.get("ip")
    name = data.get("name")
    port = data.get("port")

    if not ip or not name or not port:
        return jsonify({"error": "IP, name, and port are required"}), 400

    if not validate_ip(ip):
        return jsonify({"error": "Invalid IP address"}), 400

    try:
        port = int(port)
        if port <= 0:
            return jsonify({"error": "Port must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "Invalid port number"}), 400

    try:
        new_server = Server(ip=ip, name=name, port=port)
        db.session.add(new_server)
        db.session.commit()
        logger.info(f"Server added: IP={ip}, Name={name}, Port={port}")
        return jsonify({"message": "Server added successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding server: {e}")
        return jsonify({"error": "Failed to add server to the database"}), 500


@app.route("/update/<int:id>", methods=["PUT"])
def update_server(id):
    if "logged_in" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    ip = data.get("ip")
    name = data.get("name")
    port = data.get("port")

    if not ip or not name or not port:
        return jsonify({"error": "IP, name, and port are required"}), 400

    if not validate_ip(ip):
        return jsonify({"error": "Invalid IP address"}), 400

    try:
        port = int(port)
        if port <= 0:
            return jsonify({"error": "Port must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "Invalid port number"}), 400

    server = Server.query.get(id)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    try:
        server.ip = ip
        server.name = name
        server.port = port
        db.session.commit()
        logger.info(f"Server updated: ID={id}, IP={ip}, Name={name}, Port={port}")
        return jsonify({"message": "Server updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating server: {e}")
        return jsonify({"error": "Failed to update server in the database"}), 500


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_server(id):
    if "logged_in" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    server = Server.query.get(id)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    try:
        db.session.delete(server)
        db.session.commit()
        logger.info(f"Server deleted: ID={id}")
        return jsonify({"message": "Server deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting server: {e}")
        return jsonify({"error": "Failed to delete server from the database"}), 500


# Ping functionality
@app.route("/ping/<string:ip>", methods=["GET"])
def ping_server(ip):
    if not validate_ip(ip):
        return jsonify({"error": "Invalid IP address"}), 400

    try:
        # Execute the ping command (cross-platform support)
        if os.name == "nt":  # Windows
            result = subprocess.run(
                ["ping", "-n", "4", ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
        else:  # Linux/macOS
            result = subprocess.run(
                ["ping", "-c", "4", ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

        if result.returncode == 0:
            return jsonify({"message": "Ping successful", "output": result.stdout}), 200
        else:
            return jsonify({"error": "Ping failed", "output": result.stderr}), 400

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Ping timed out"}), 408
    except Exception as e:
        logger.error(f"Ping error: {e}")
        return jsonify({"error": f"Ping error: {e}"}), 500


# Telnet functionality
@app.route("/telnet/<string:ip>/<int:port>", methods=["GET"])
def telnet_server(ip, port):
    if not validate_ip(ip):
        return jsonify({"error": "Invalid IP address"}), 400

    try:
        # Attempt to establish a telnet connection
        telnet = telnetlib.Telnet(ip, port, timeout=5)  # type: ignore # Timeout after 5 seconds
        telnet.close()
        return jsonify({"message": f"Telnet successful to {ip}:{port}"}), 200

    except ConnectionRefusedError:
        return jsonify({"error": f"Connection refused to {ip}:{port}"}), 400
    except OSError as e:
        return jsonify({"error": f"Telnet error: {e}"}), 500
    except Exception as e:
        logger.error(f"Telnet error: {e}")
        return jsonify({"error": f"Unexpected error: {e}"}), 500


# Login/Logout Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error_message = "Username and password are required."
        else:
            admin = Admin.query.filter_by(username=username).first()
            if admin and bcrypt.checkpw(password.encode("utf-8"), admin.password.encode("utf-8")):
                session["logged_in"] = True
                logger.info(f"User logged in: {username}")
                return redirect(url_for("index"))
            else:
                error_message = "Invalid credentials"

    return render_template("login.html", error=error_message)


@app.route("/logout")
def logout():
    if "logged_in" in session:
        logger.info(f"User logged out: {session['logged_in']}")
    session.pop("logged_in", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)