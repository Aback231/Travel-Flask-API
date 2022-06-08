import bcrypt
from flask_restful import Resource, reqparse
from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)
from models.user import UserModel
from blacklist import BLACKLIST

BLANK_FIELD = "This field can't be blank."

_user_parser_register = reqparse.RequestParser()
_user_parser_register.add_argument('first_name',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )
_user_parser_register.add_argument('last_name',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )
_user_parser_register.add_argument('email',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )                                              
_user_parser_register.add_argument('username',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )
_user_parser_register.add_argument('password',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )
_user_parser_register.add_argument('password_confirmation',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )
_user_parser_register.add_argument('acc_type',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )                      

_user_parser_login = reqparse.RequestParser()
_user_parser_login.add_argument('username',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )
_user_parser_login.add_argument('password',
                          type=str,
                          required=True,
                          help=BLANK_FIELD
                          )

class Register(Resource):
    def post(self):
        # Parse request args
        data = _user_parser_register.parse_args()

        # Check if user exists
        if UserModel.find_by_username(data['username']):
            return {"message": "User already exists!"}, 400

        # Validate password confirmation
        if not safe_str_cmp(data['password'], data['password_confirmation']):
            return {"message": "Passwords don't match!"}, 400

        # Encrypt password for DB storing
        data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())

        user = UserModel(**data)
        user.save_to_db()

        return {"message": "User created successfully."}, 201

class Login(Resource):
    def post(self):
        data = _user_parser_login.parse_args()
        user = UserModel.find_by_username(data['username'])

        # Hash provided pass and compare to the one stored in DB for givrn UserName
        if user and safe_str_cmp(bcrypt.hashpw(data['password'].encode('utf8'), user.password), user.password):
            access_token = create_access_token(identity=user.id, fresh=True) 
            refresh_token = create_refresh_token(user.id)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200

        return {"message": "Invalid Credentials!"}, 401

# LogOut, JWT access_token must be provided in Header
class Logout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLACKLIST.add(jti)
        return {"message": "Logout successful"}, 200

# Get a new refreshed access token without requiring username and password
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200
