from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'

    from app.routes import auth, campaign, dashboard, tracking
    app.register_blueprint(auth.bp)
    app.register_blueprint(campaign.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(tracking.bp)

    # Initialize SmartLead API
    from app.smartlead_api import SmartleadAPI
    app.smartlead = SmartleadAPI(app.config.get('SMARTLEAD_API_KEY'))

    return app 