import os
import time
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity
from dotenv import load_dotenv
from sqlalchemy import exc

from db import db
from models import User

import logging
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

app = Flask(
    __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT (header-based)
app.config['JWT_SECRET_KEY']         = os.getenv('JWT_SECRET_KEY', 'jwt-secret')
app.config['JWT_TOKEN_LOCATION']     = ['cookies']        # <— look in cookies
app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token_cookie'
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SECURE']      = False              # HTTP in dev
app.config['JWT_COOKIE_SAMESITE']    = 'Lax'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

jwt = JWTManager(app)

# Init DB
db.init_app(app)
with app.app_context():
    # wait for DB
    engine = db.engine
    for _ in range(30):
        try:
            engine.connect().close()
            break
        except exc.OperationalError:
            time.sleep(1)
    db.create_all()

# Inject current_user into templates via JWT
@app.context_processor
def inject_user():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        user = User.query.get(uid) if uid else None
    except:
        user = None
    return dict(current_user=user)

# Register blueprints in this order
from blueprints.auth        import auth_bp
from blueprints.ui          import ui_bp
from blueprints.projects    import projects_bp
from blueprints.collections import collections_bp
from blueprints.requests    import requests_bp
from blueprints.environments import env_bp
from blueprints.mockrules   import mockrules_bp
from blueprints.mockserve   import mock_bp

app.register_blueprint(auth_bp)      # /auth/login
app.register_blueprint(ui_bp)        # /login, /
app.register_blueprint(projects_bp)  # /api/projects
app.register_blueprint(collections_bp)
app.register_blueprint(requests_bp)
app.register_blueprint(env_bp)
app.register_blueprint(mockrules_bp)
# catch-all last:
app.register_blueprint(mock_bp)

@app.route('/health')
def health():
    return jsonify(status='ok'), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
