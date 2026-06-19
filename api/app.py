
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS
from api.routes import register_routes

def create_app():
    app = Flask(__name__)
    CORS(app)  # Allow dashboard to call the API
    register_routes(app)
    return app

if __name__ == "__main__":
    app = create_app()
    print("\n Attack Path Platform API running at http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)