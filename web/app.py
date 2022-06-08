from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager

from db import db
from blacklist import BLACKLIST
from resources.user import Register, Login, Logout, TokenRefresh

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://user:pass@postgres_db_container/db"  # PostgreDB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"    # Local Sqlite for quick testing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.secret_key = 'secret'
api = Api(app)

# Disable when docker-compose up
#db.init_app(app)

# Create DB
@app.before_first_request
def create_tables():
    db.create_all()

jwt = JWTManager(app)

# Check if a token is blacklisted
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(arg, decrypted_token):
    return decrypted_token['jti'] in BLACKLIST

# Customizing jwt response/error messages
@jwt.expired_token_loader
def expired_token_callback():
    return jsonify({
        'message': 'Token has expired.',
        'error': 'token_expired'
    }), 401

# Signature validation
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'message': 'Signature validation failed.',
        'error': 'invalid_token'
    }), 401

# No TOken
@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "description": "Request does not contain access token.",
        'error': 'authorization_required'
    }), 401

# Token not fresh
@jwt.needs_fresh_token_loader
def token_not_fresh_callback():
    return jsonify({
        "description": "Token is not fresh.",
        'error': 'fresh_token_required'
    }), 401

# TOken rewoked
@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({
        "description": "Token has been revoked.",
        'error': 'token_revoked'
    }), 401

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(TokenRefresh, '/refresh')

if __name__ == '__main__':
    # Disable when flask run
    db.init_app(app)
    app.run(host='0.0.0.0', debug=True)
