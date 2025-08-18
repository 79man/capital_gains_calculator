from flask import Flask
from flask_cors import CORS
from api.routes import api_bp


def create_app():
    app = Flask(__name__)
    CORS(app, origins='*')  # Allow all origins

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    return app


# Create the app instance at module level - this is what Waitress needs
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
