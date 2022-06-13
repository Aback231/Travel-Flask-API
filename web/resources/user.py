import bcrypt
import traceback
from flask_restful import Resource
from flask import request
from marshmallow import INCLUDE
from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)

from constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from models.user import UserModel
from schemas.user import UserSchema, LogInSchema, ProfileSchema
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangementSchema
from blacklist import BLACKLIST
from decorators.roles import roles
from constants.user_roles import UserRoles
from libs.mailgun import Mailgun, MailGunException
from helpers.pagination_and_sorting import paginate_and_sort, paginate_sort_filter_user_profiles


USER_ALREADY_EXISTS = "A user with that username already exists."
EMAIL_ALREADY_EXISTS = "A user with that email already exists."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "Logout successful."
FAILED_TO_CREATE = "Internal server error. Failed to create user."
REGISTER_SUCCESS_MESSAGE = "Account created successfully."
PASSWORD_MISMATCH = "Passwords don't match!"
PASSWORD_CONFIRMATION = "Passwords confirmation is required!"
USER_ACC_CHANGED = ("User Account type changed successfully from <{}> to <{}>.")
USER_ACC_CHANGED_ALREADY = ("User Account type was already changed.")
USER_ACC_CHANGE_VALIDATION = "JSON parameters username and is_approved are required"
USER_ACC_CHANGE_FAILED = "User Account type changed failed."
MAILGUN_SUBJECT_ACC_CHANGE = "Account type change confirmation"
MAILGUN_SUBJECT_REGISTER = "Registration Confirmation"
MAILGUN_HTML_ACC_CHANGE_SUCCESS = ("<html>Account type change from <b>{}</b> to <b>{}</b> successful.</html>")
MAILGUN_HTML_ACC_CHANGE_DENIED = ("<html>Account type change from <b>{}</b> to <b>{}</b> was denied with comment: {}.</html>")
MAILGUN_HTML_REGISTER = ("<html>Registration successful. Username: <b>{}</b></html>")
USER_ACC_CHANGE_REQUEST_VALIDATION = "JSON parameter acc_type_requested is required"
USER_ACC_CHANGE_REQUEST_SUCCESS = ("Account type change request to {} successful.")
USER_ACC_CHANGE_REQUEST_DENIED = "Account type change request was denied."
USER_ACC_CHANGE_REQUEST_ROLE_VALIDATION = ("Only <{}> and <{}> account types are allowed as acc_type_requested JSON parameters!")
USER_ID_PARAM = "User <id> is required JSON parameter."
USER_PROFILE_UPDATE_SUCCESS = "User profile successfully updated."

user_schema = UserSchema(unknown=INCLUDE)
user_list_schema = UserSchema(many=True)
login_schema = LogInSchema()
user_profile_schema = ProfileSchema(unknown=INCLUDE)

arrangement_schema = ArrangementSchema()
arrangement_list_schema = ArrangementSchema(many=True)


class UserRegister(Resource):
    """ User registration. UserModel defines required params. """
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user = user_schema.load(user_json)
        
        if UserModel.find_by_username(user.username):
            return {"message": USER_ALREADY_EXISTS}, HTTP_400_BAD_REQUEST

        if UserModel.find_by_email(user.email):
            return {"message": EMAIL_ALREADY_EXISTS}, HTTP_400_BAD_REQUEST

        """ Validate password confirmation """
        if "password_confirmation" not in user_json.keys():
            return {"message": PASSWORD_CONFIRMATION}, HTTP_400_BAD_REQUEST
        if not safe_str_cmp(user.password, user_json["password_confirmation"]):
            return {"message": PASSWORD_MISMATCH}, HTTP_400_BAD_REQUEST

        try:
            """ Encrypt password for DB storing """
            user.password = bcrypt.hashpw(user.password.encode('utf8'), bcrypt.gensalt()).decode()
            user.acc_type = UserRoles.DEFAULT_ROLE.value
            user.save_to_db()
            Mailgun.send_email([user.email], MAILGUN_SUBJECT_REGISTER, MAILGUN_HTML_REGISTER.format(user.username))
            return {"message": REGISTER_SUCCESS_MESSAGE}, HTTP_201_CREATED
        except MailGunException as e:
            return {"message": str(e)}, HTTP_500_INTERNAL_SERVER_ERROR
        except:
            traceback.print_exc()
            return {"message": FAILED_TO_CREATE}, HTTP_500_INTERNAL_SERVER_ERROR


class UserLogin(Resource):
    """ User login. Exchange username and password for JWT token. """
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = login_schema.load(user_json, partial=("email",))

        user = UserModel.find_by_username(user_data.username)        

        # Hash provided pass and compare to the one stored in DB for givrn UserName
        if user and safe_str_cmp(bcrypt.hashpw(user_data.password.encode('utf8'), user.password.encode()), user.password):
            access_token = create_access_token(identity=user.id, fresh=True, additional_claims={"acc_type": user.acc_type})
            refresh_token = create_refresh_token(user.id)
            return (
                {"access_token": access_token, "refresh_token": refresh_token, "username": user.username, "acc_type": user.acc_type},
                HTTP_200_OK,
            )

        return {"message": INVALID_CREDENTIALS}, HTTP_401_UNAUTHORIZED


class UserLogout(Resource):
    """ JWT access_token must be provided in Header. Will be blacklisted after logging out. """
    @classmethod
    @jwt_required()
    def post(cls):
        jti = get_jwt()['jti']
        BLACKLIST.add(jti)
        return {"message": USER_LOGGED_OUT}, HTTP_200_OK


class ListAccountChangeRequests(Resource):
    """ ADMIN can list all users who requested account change. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def post(cls):
        tourist_users = UserModel.find_by_acc_type(UserRoles.TOURIST.value)
        tourist_users_filtered = []
        for item in tourist_users:
            if not safe_str_cmp(item.acc_type_requested, item.acc_type):
                tourist_users_filtered.append(item)

        travel_guide_users = UserModel.find_by_acc_type(UserRoles.TRAVEL_GUIDE.value)
        travel_guide_users_filtered = []
        for item in travel_guide_users:
            if not safe_str_cmp(item.acc_type_requested, item.acc_type):
                travel_guide_users_filtered.append(item)

        filtered_users = {
            "tourist_users": user_list_schema.dump(tourist_users_filtered),
            "travel_guide_users": user_list_schema.dump(travel_guide_users_filtered)
        }
        
        return {"list_acc_change_requests": filtered_users}, HTTP_200_OK


class UserAccountChangeRequest(Resource):
    """ Request account type change. Only TOURIST and TRAVEL_GUIDE are allowed to execute this endpoint. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value, UserRoles.TRAVEL_GUIDE.value])
    def post(cls):
        if "acc_type_requested" not in request.get_json().keys():
            return {"message": USER_ACC_CHANGE_REQUEST_VALIDATION}, HTTP_400_BAD_REQUEST

        acc_type_requested_new = request.get_json()["acc_type_requested"]

        if acc_type_requested_new not in [UserRoles.TRAVEL_GUIDE.value, UserRoles.ADMIN.value]:
            return {"message": USER_ACC_CHANGE_REQUEST_ROLE_VALIDATION.format(UserRoles.TRAVEL_GUIDE.value, UserRoles.ADMIN.value)}, HTTP_400_BAD_REQUEST

        user = UserModel.find_by_id(get_jwt_identity())

        user.acc_type_requested = acc_type_requested_new
        user.save_to_db()

        return {"message": USER_ACC_CHANGE_REQUEST_SUCCESS.format(acc_type_requested_new)}, HTTP_200_OK


class UserAccountChange(Resource):
    """ Admin approves or denies (with comment) user account change request. Email is sent in both cases.  """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def post(cls):
        if "username" not in request.get_json().keys() or "is_approved" not in request.get_json().keys():
            return {"message": USER_ACC_CHANGE_VALIDATION}, HTTP_400_BAD_REQUEST

        acc_change_json = request.get_json()

        username = acc_change_json["username"]
        is_approved = acc_change_json["is_approved"]
        rejection_comment = acc_change_json["rejection_comment"]

        user = UserModel.find_by_username(username)
        acc_type_old = user.acc_type
        acc_type_requested_old = user.acc_type_requested

        if not user:
            return {"message": USER_NOT_FOUND}, HTTP_404_NOT_FOUND

        # Request rejected, set acc_type_requested to current acc_type
        try:
            if not is_approved:
                user.acc_type_requested = user.acc_type
                user.save_to_db()

                Mailgun.send_email([user.email], MAILGUN_SUBJECT_ACC_CHANGE, MAILGUN_HTML_ACC_CHANGE_DENIED.format(user.acc_type_requested, acc_type_requested_old, rejection_comment))
                return {"message": USER_ACC_CHANGE_REQUEST_DENIED}, HTTP_200_OK

            # Request approved, set current acc_type to acc_type_requested
            user.acc_type = user.acc_type_requested
            user.save_to_db()

            Mailgun.send_email([user.email], MAILGUN_SUBJECT_ACC_CHANGE, MAILGUN_HTML_ACC_CHANGE_SUCCESS.format(acc_type_old, user.acc_type_requested))
            return {"message": USER_ACC_CHANGED.format(acc_type_old, user.acc_type_requested)}, HTTP_200_OK
        except MailGunException as e:
            return {"message": str(e)}, HTTP_500_INTERNAL_SERVER_ERROR
        except:
            traceback.print_exc()
            return {"message": USER_ACC_CHANGE_FAILED}, HTTP_500_INTERNAL_SERVER_ERROR


class UserProfileView(Resource):
    """ TOURIST can view their profile. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def post(cls):
        user = UserModel.find_by_id(get_jwt_identity())
        return {"user_profile": user_schema.dump(user)}, HTTP_200_OK


class UserProfileUpdate(Resource):
    """ TOURIST can update their profile. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def post(cls):
        user_json = request.get_json()
        user_profile_schema.load(user_json)

        if "id" not in user_json.keys():
            return {"message": USER_ID_PARAM}, HTTP_400_BAD_REQUEST
        
        arrangement = UserModel.find_by_id(user_json["id"])

        if not arrangement:
            return {"message": USER_NOT_FOUND}, HTTP_400_BAD_REQUEST

        for key in user_json:
            if not safe_str_cmp(key, "id"):
                arrangement.__setattr__(key, user_json[key])

        arrangement.save_to_db()

        return {"message": USER_PROFILE_UPDATE_SUCCESS}, HTTP_201_CREATED


class UserProfileList(Resource):
    """ ADMIN can view all user profiles and filter them. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def post(cls):
        return paginate_sort_filter_user_profiles(request, [UserModel, ArrangementModel], [user_list_schema, arrangement_list_schema], "users", [UserRoles.TOURIST.value, UserRoles.TRAVEL_GUIDE.value])


class TokenRefresh(Resource):
    """ Request Fresh Token  """
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, HTTP_200_OK


############################## Only for testing purposes ##############################
class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, HTTP_404_NOT_FOUND

        return user_schema.dump(user), HTTP_200_OK

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, HTTP_404_NOT_FOUND

        user.delete_from_db()
        return {"message": USER_DELETED}, HTTP_200_OK


class UserRegisterAdmin(Resource):
    """ Create initial Admin account. """
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user = user_schema.load(user_json)
        
        if UserModel.find_by_username(user.username):
            return {"message": USER_ALREADY_EXISTS}, HTTP_400_BAD_REQUEST

        if UserModel.find_by_email(user.email):
            return {"message": EMAIL_ALREADY_EXISTS}, HTTP_400_BAD_REQUEST

        # Validate password confirmation
        if "password_confirmation" not in user_json.keys():
            return {"message": PASSWORD_CONFIRMATION}, HTTP_400_BAD_REQUEST
        if not safe_str_cmp(user.password, user_json["password_confirmation"]):
            return {"message": PASSWORD_MISMATCH}, HTTP_400_BAD_REQUEST

        try:
            # Encrypt password for DB storing
            user.password = bcrypt.hashpw(user.password.encode('utf8'), bcrypt.gensalt()).decode()
            user.acc_type = UserRoles.ADMIN.value
            user.save_to_db()
            Mailgun.send_email([user.email], MAILGUN_SUBJECT_REGISTER, MAILGUN_HTML_REGISTER.format(user.username))
            return {"message": REGISTER_SUCCESS_MESSAGE}, HTTP_201_CREATED
        except MailGunException as e:
            return {"message": str(e)}, HTTP_500_INTERNAL_SERVER_ERROR
        except:  # failed to save user to db
            traceback.print_exc()
            return {"message": FAILED_TO_CREATE}, HTTP_500_INTERNAL_SERVER_ERROR
