from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from marshmallow import ValidationError

from db import db
from ma import ma
from blacklist import BLACKLIST
from resources.user import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    UserLogout,
    UserAccountChangeRequest,
    UserAccountChange,
    User,
    UserRegisterAdmin,
)
from resources.arrangement import Arrangement, ArrangementList, ArrangementListBasic, ArrangementListByCreator, ArrangementCreate, ArrangementDeactivate


app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://user:pass@postgres_db_container/db"  # PostgreDB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"    # Local Sqlite for quick testing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.secret_key = 'secret'
api = Api(app)

# Disable both when docker-compose up
#db.init_app(app)
#ma.init_app(app)

# Create DB
@app.before_first_request
def create_tables():
    db.create_all()

@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400

jwt = JWTManager(app)

# Check if Token is blacklisted
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(arg, decrypted_token):
    return decrypted_token["jti"] in BLACKLIST


api.add_resource(UserRegister, "/register")
api.add_resource(UserLogin, "/login")
api.add_resource(TokenRefresh, "/refresh")
api.add_resource(UserLogout, "/logout")
api.add_resource(UserAccountChangeRequest, "/acc_change_request")
api.add_resource(UserAccountChange, "/acc_change")
api.add_resource(User, "/user/<int:user_id>")   # endpoint for testing
api.add_resource(UserRegisterAdmin, "/register_admin")   # endpoint for testing

api.add_resource(Arrangement, "/arrangement/<int:id>")
api.add_resource(ArrangementCreate, "/arrangement_create")
api.add_resource(ArrangementDeactivate, "/arrangement_deactivate/<int:id>")
api.add_resource(ArrangementList, "/arrangements")
api.add_resource(ArrangementListBasic, "/arrangements_basic")
api.add_resource(ArrangementListByCreator, "/arrangements_by_creator")


if __name__ == "__main__":
    # Disable both when flask run
    db.init_app(app)
    ma.init_app(app)
    app.run(host='0.0.0.0', debug=True)
