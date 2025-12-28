#!/usr/bin/env python3
"""
Study Tracker Backend (development/demo)

- Serves static/index.html at '/'
- API endpoints under /api/*
"""
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import logging
import sys

USERS_FILE = "users.json"
STATIC_DIR = "static"

app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/api/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("study-tracker-backend")


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        try:
            os.rename(USERS_FILE, USERS_FILE + ".corrupt")
            log.warning("Corrupt users.json renamed to users.json.corrupt")
        except Exception:
            log.exception("Could not rename corrupt users file.")
        return {}
    except Exception:
        log.exception("Failed to load users.json")
        return {}


def save_users(users):
    try:
        tmp = USERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        os.replace(tmp, USERS_FILE)
    except Exception:
        log.exception("Failed to save users.json")


def is_valid_email(email: str) -> bool:
    return isinstance(email, str) and "@" in email and len(email) >= 5


def is_valid_password(password: str) -> bool:
    return isinstance(password, str) and len(password) >= 6


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "Backend is running!"}), 200


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not is_valid_email(email) or not is_valid_password(password):
        return jsonify({"message": "Invalid email or password (min length 6)."}), 400

    users = load_users()
    if email in users:
        return jsonify({"message": "Email already exists"}), 409

    pw_hash = generate_password_hash(password)
    users[email] = {
        "password_hash": pw_hash,
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    save_users(users)
    return jsonify({"message": "Account created successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    users = load_users()
    user = users.get(email)
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    stored_hash = user.get("password_hash")
    if not stored_hash or not check_password_hash(stored_hash, password):
        return jsonify({"message": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "user": {"email": email, "created_at": user.get("created_at")}}), 200


# Serve index.html from static directory
@app.route("/", methods=["GET"])
def root_index():
    here = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(here, STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(os.path.join(here, STATIC_DIR), "index.html")
    return (
        "<html><body><h3>index.html not found</h3><p>Put index.html inside the 'static' folder.</p></body></html>",
        404,
    )


# Serve other static files if they exist
@app.route("/<path:filename>", methods=["GET"])
def serve_static_file(filename: str):
    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, STATIC_DIR, filename)
    if os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(os.path.join(here, STATIC_DIR), filename)
    return abort(404)


def main():
    default_port = int(os.environ.get("PORT", "5000"))
    port = default_port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            log.warning("Invalid port arg, using default %d", default_port)
    log.info("Starting Study Tracker Backend on http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=True)


if __name__ == "__main__":
    main()
