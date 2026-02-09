from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    login_manager.init_app(app)
    login_manager.login_view = 'views.login'
    
    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
