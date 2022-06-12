from flask_restful import Resource
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import safe_str_cmp

from helpers import date_parser
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangementSchema, ArrangementSchemaBasic
from models.user import UserModel
from decorators.roles import roles
from helpers.user_roles import UserRoles
from libs.mailgun import MailGunException
from libs.mailgun import Mailgun
from libs.pagination_and_sorting import paginate_and_sort


NAME_ALREADY_EXISTS = "An arrangement with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the arrangement."
ARRANGEMENT_ID_PARAM = "Arrangement <id> is a required parameter."
ARRANGEMENT_NOT_FOUND = "Arrangement not found."
ARRANGEMENT_DELETED = "Arrangement deleted."
ARRANGEMENT_ALREADY_EXISTS = "Arrangement already exists."
ARRANGEMENT_CREATION_SUCCESS = "Arrangement created successfully."
ARRANGEMENT_UPDATE_SUCCESS = "Arrangement updated successfully."
ARRANGEMENT_TIME_TO_START_ERROR = "Arrangement has less than 5 days to start!"
ARRANGEMENT_DEACTIVATED_SECCESS = "Arrangement was deactivated successfully."
ARRANGEMENT_DEACTIVATED_ALREADY = "Arrangement was already deactivated."
ARRANGEMENT_RESERVATIONS_LIST_PARAM_ERROR = "Please use correct endpoint </reserved_arrangements/0> with integer at the end <0 or 1>!"

MAILGUN_SUBJECT_ARRANGEMENT_DEACTIVATED = "Arrangement deactivated"
MAILGUN_HTML_ARRANGEMENT_DEACTIVATED = ("<html>Arrangement You have a reservation for was deactivated.</html>")

arrangement_schema = ArrangementSchema()
arrangement_list_schema = ArrangementSchema(many=True)
arrangement_list_schema_basic = ArrangementSchemaBasic(many=True)


class ArrangementCreate(Resource):
    """ Arangement creation by Admin account type """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def post(cls):
        arrangement_json = request.get_json()
        arrangement = arrangement_schema.load(arrangement_json)

        if ArrangementModel.find_by_description(arrangement.description):
            return {"message": ARRANGEMENT_ALREADY_EXISTS}, 400

        arrangement.users_id = get_jwt_identity()
        arrangement.save_to_db()

        return {"message": ARRANGEMENT_CREATION_SUCCESS}, 201


class ArrangementUpdate(Resource):
    """ Arangement update by Admin account type at latest 5 days before it starts """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def post(cls):
        arrangement_json = request.get_json()
        schema = arrangement_schema.load(arrangement_json)

        if "id" not in arrangement_json.keys():
            return {"message": ARRANGEMENT_ID_PARAM}, 400
        
        arrangement = ArrangementModel.find_by_id(arrangement_json["id"])

        if not arrangement:
            return {"message": ARRANGEMENT_NOT_FOUND}, 400

        for key in arrangement_json:
            if not safe_str_cmp(key, "id"):
                arrangement.__setattr__(key, arrangement_json[key])

        arrangement.save_to_db()

        return {"message": ARRANGEMENT_UPDATE_SUCCESS}, 201


class ArrangementDeactivate(Resource):
    """ Admin can deactivate an Arrangement at latest 5 days before it starts """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def put(cls, id: int):
        arrangement = ArrangementModel.find_by_id(id)
        users_reserved_emails = [x.email for x in arrangement.user_reservations]

        if not date_parser.is_arrangement_reservable(arrangement.date_start):
            return {"message": ARRANGEMENT_TIME_TO_START_ERROR}, 400
        
        if not arrangement.is_active:
            return {"message": ARRANGEMENT_DEACTIVATED_ALREADY}, 200

        arrangement.is_active = False
        arrangement.save_to_db()

        try:
            Mailgun.send_email(users_reserved_emails, MAILGUN_SUBJECT_ARRANGEMENT_DEACTIVATED, MAILGUN_HTML_ARRANGEMENT_DEACTIVATED)
        except MailGunException as e:
            return {"message": str(e)}, 500

        return {"message": ARRANGEMENT_DEACTIVATED_SECCESS}, 200


class ArrangementReservationsList(Resource):
    """ Get Detailed List of all reserved or not reserved Arrangements by user, login required.
        If 0 is passed in request reserved_arrangements are returned, else not_reserved_arrangements """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def get(cls, reverse: int):
        if reverse not in [0,1]:
            return {"message": ARRANGEMENT_RESERVATIONS_LIST_PARAM_ERROR}, 500

        user = UserModel.find_by_id(get_jwt_identity())
        if reverse == 0:
            return {"reserved_arrangements": arrangement_list_schema.dump(user.arrangements_reservations)}, 200

        user_arrangements_ids = [x.id for x in user.arrangements_reservations]
        user_arrangements_all = ArrangementModel.find_all()

        diff_list = []
        for item in user_arrangements_all:
            if item.id not in user_arrangements_ids and date_parser.is_arrangement_reservable(item.date_start):
                diff_list.append(item)

        return {"not_reserved_arrangements": arrangement_list_schema.dump(diff_list)}, 200


class ArrangementListBasic(Resource):
    """ Get Basic List of all Arrangements, no need for login """
    @classmethod
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema_basic, "arrangement_list")


class ArrangementList(Resource):
    """ Get Detailed List of all Arrangements, login required """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema, "arrangement_list")


class ArrangementListByCreator(Resource):
    """ Get Detailed List of all Arrangements created by an Admin, login required """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema, "arrangement_list", {"users_id": get_jwt_identity()})