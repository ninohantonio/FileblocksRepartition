from flask import Flask
from config import Config
from routes import register_routes
from models import init_db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Créer les dossiers nécessaires
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    
    # Initialiser la base de données
    init_db(app.config['DATABASE_PATH'])
    
    # Enregistrer les routes
    register_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=3000)