from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager  # ✅ Add this
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# ✅ LoginManager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirects to 'login' route if not logged in

from app.models import User  # Import User model

# ✅ user loader for login system
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from app import routes, models
