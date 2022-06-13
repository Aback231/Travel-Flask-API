import string
from typing import Text
from flask_restful import Resource
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import safe_str_cmp

from constants.http_status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from helpers import date_parser
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangementSchema, ArrangementSchemaBasic
from models.user import UserModel
from decorators.roles import roles
from constants.user_roles import UserRoles
from libs.mailgun import Mailgun, MailGunException
from helpers.pagination_and_sorting import paginate_and_sort


NAME_ALREADY_EXISTS = "An arrangement with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the arrangement."
ARRANGEMENT_ID_PARAM = ("Arrangement <{}> is a required parameter.")
ARRANGEMENT_NOT_FOUND = "Arrangement not found."
ARRANGEMENT_DELETED = "Arrangement deleted."
ARRANGEMENT_ALREADY_EXISTS = "Arrangement already exists."
ARRANGEMENT_CREATION_SUCCESS = "Arrangement created successfully."
ARRANGEMENT_UPDATE_SUCCESS = "Arrangement updated successfully."
ARRANGEMENT_TIME_TO_START_ERROR = "Arrangement has less than 5 days to start!"
ARRANGEMENT_DEACTIVATED_SECCESS = "Arrangement was deactivated successfully."
ARRANGEMENT_DEACTIVATED_ALREADY = "Arrangement was already deactivated."
ARRANGEMENT_RESERVATIONS_LIST_PARAM_ERROR = "Please use correct endpoint </reserved_arrangements/?reserved=true> with integer at the end <0 or 1>!"
ARRANGEMENT_LIST_DEST_TIME_KEY_ERROR = "Only <destination> and <date_start> keys are allowed!"
ARRANGEMENT_ROLES_ERROR = ("Only <{}> account type(s) are allowed to be selected as tour guides!")
ARRANGEMENT_TOUR_GUIDE_ASSIGNMENT_SUCCESS = ("Travel Guide <{}> successfully assigned to this arrangement!")
ARRANGEMENT_TOUR_GUIDE_ASSIGNMENT_FAIL = ("Travel Guide <{}> not assigned, they are already booked for that date range!")
ARRANGEMENT_TOUR_GUIDE_ASSIGNMENT_FAIL_ALREADY_BOOKED_FOR_THIS_ONE = ("Travel Guide <{}> not assigned, they are already booked for this arrangement!")

MAILGUN_SUBJECT_ARRANGEMENT_DEACTIVATED = "Arrangement deactivated"
MAILGUN_HTML_ARRANGEMENT_DEACTIVATED = ("<html>Arrangement You have a reservation for was deactivated.</html>")

arrangement_schema = ArrangementSchema()
arrangement_list_schema = ArrangementSchema(many=True)
arrangement_list_schema_basic = ArrangementSchemaBasic(many=True)


class CreateArrangement(Resource):
    """ Arangement creation by Admin account type """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def post(cls):
        arrangement_json = request.get_json()
        arrangement = arrangement_schema.load(arrangement_json)

        if ArrangementModel.find_by_description(arrangement.description):
            return {"message": ARRANGEMENT_ALREADY_EXISTS}, HTTP_400_BAD_REQUEST

        arrangement.users_id = get_jwt_identity()
        arrangement.save_to_db()

        return {"message": ARRANGEMENT_CREATION_SUCCESS}, HTTP_201_CREATED


class UpdateArrangement(Resource):
    """ Arangement update at latest 5 days before it starts 
        Admin account type can Update all fields
        Travel Guide account type can Update only description """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value, UserRoles.TRAVEL_GUIDE.value])
    def post(cls):
        is_admin = safe_str_cmp(UserModel.find_by_id(get_jwt_identity()).acc_type, UserRoles.ADMIN.value)
        arrangement_json = request.get_json()

        # Validation for full Arrangement Model
        if is_admin:
            schema = arrangement_schema.load(arrangement_json)

        # Validate id present in JSON, it's not in Model Validation
        if "id" not in arrangement_json.keys():
            return {"message": ARRANGEMENT_ID_PARAM.format("id")}, HTTP_400_BAD_REQUEST
        
        arrangement = ArrangementModel.find_by_id(arrangement_json["id"])

        if not arrangement:
            return {"message": ARRANGEMENT_NOT_FOUND}, HTTP_404_NOT_FOUND

        # Validate arrangement date
        if not date_parser.is_arrangement_reservable(arrangement.date_start):
            return {"message": ARRANGEMENT_TIME_TO_START_ERROR}, HTTP_400_BAD_REQUEST

        # Admin can update all fields, Travel Guide just description
        if is_admin:
            # Set arrangement key values from JSON payload passed in request by Admin
            for key in arrangement_json:
                if not safe_str_cmp(key, "id"):
                    arrangement.__setattr__(key, arrangement_json[key])
        else:
            # Set description key if it exists in JSON payload
            if "description" not in arrangement_json.keys():
                return {"message": ARRANGEMENT_ID_PARAM.format("description")}, HTTP_400_BAD_REQUEST
            arrangement.description = arrangement_json["description"]

        arrangement.save_to_db()

        return {"message": ARRANGEMENT_UPDATE_SUCCESS}, HTTP_201_CREATED


class PickTourGuideArrangement(Resource):
    """ Admin can pick Tour Guide for specific arrangement """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        tour_guide_id = request.args.get('tour_guide_id', type=int)
        arrangement_id = request.args.get('arrangement_id', type=int)
        
        # Get requested user and arrangement
        arrangement = ArrangementModel.find_by_id(arrangement_id)
        user = UserModel.find_by_id(tour_guide_id)

        if not arrangement or not user:
            return {"message": ARRANGEMENT_NOT_FOUND}, HTTP_404_NOT_FOUND

        # Validate privilege
        if not safe_str_cmp(user.acc_type, UserRoles.TOURIST.value):
            return {"message": ARRANGEMENT_ROLES_ERROR.format(UserRoles.TOURIST.value)}, HTTP_403_FORBIDDEN
      
        # Validate user already booked for this arrangement
        if arrangement.tour_guide_id == user.id:
            return {"message": ARRANGEMENT_TOUR_GUIDE_ASSIGNMENT_FAIL_ALREADY_BOOKED_FOR_THIS_ONE.format(user.username)}, HTTP_400_BAD_REQUEST

        # Date occupied validation
        arrangements = ArrangementModel.find_all_by_tour_guide_id(tour_guide_id)
        for item in arrangements:
            if not date_parser.is_tour_guide_available(item.date_start, item.date_end, arrangement.date_start, arrangement.date_end):
                return {"message": ARRANGEMENT_TOUR_GUIDE_ASSIGNMENT_FAIL.format(user.username)}, HTTP_400_BAD_REQUEST
        
        arrangement.tour_guide_id = tour_guide_id
        arrangement.save_to_db()

        return {"message": ARRANGEMENT_TOUR_GUIDE_ASSIGNMENT_SUCCESS.format(user.username)}, HTTP_201_CREATED


class DeactivateArrangement(Resource):
    """ Admin can deactivate an Arrangement at latest 5 days before it starts """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def put(cls, id: int):
        arrangement = ArrangementModel.find_by_id(id)
        users_reserved_emails = [x.email for x in arrangement.user_reservations]

        # Validate arrangement date
        if not date_parser.is_arrangement_reservable(arrangement.date_start):
            return {"message": ARRANGEMENT_TIME_TO_START_ERROR}, HTTP_400_BAD_REQUEST
        
        if not arrangement.is_active:
            return {"message": ARRANGEMENT_DEACTIVATED_ALREADY}, HTTP_200_OK

        arrangement.is_active = False
        arrangement.save_to_db()

        try:
            Mailgun.send_email(users_reserved_emails, MAILGUN_SUBJECT_ARRANGEMENT_DEACTIVATED, MAILGUN_HTML_ARRANGEMENT_DEACTIVATED)
        except MailGunException as e:
            return {"message": str(e)}, HTTP_500_INTERNAL_SERVER_ERROR

        return {"message": ARRANGEMENT_DEACTIVATED_SECCESS}, HTTP_200_OK


class ReservationsListArrangement(Resource):
    """ Get Detailed List of all reserved or not reserved up from 5 days until start Arrangements by Tourist user. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def get(cls):

        is_filter_reserved = request.args.get('reserved') == 'true'

        user = UserModel.find_by_id(get_jwt_identity())

        if is_filter_reserved:
            return {"reserved_arrangements": arrangement_list_schema.dump(user.arrangements_reservations)}, HTTP_200_OK

        user_arrangements_ids = [x.id for x in user.arrangements_reservations]
        user_arrangements_all = ArrangementModel.find_all()

        diff_list = []
        for item in user_arrangements_all:
            if item.id not in user_arrangements_ids and date_parser.is_arrangement_reservable(item.date_start):
                diff_list.append(item)

        return {"not_reserved_arrangements": arrangement_list_schema.dump(diff_list)}, HTTP_200_OK


class BasicListArrangement(Resource):
    """ Get Basic List of all Arrangements, no need for login """
    @classmethod
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema_basic, "arrangements_list")


class ListByDestinationOrTimeArrangement(Resource):
    """ Get List of all Arrangements, by destination or time for Tourist acc type. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def get(cls, key: string, value: string):
        if key in ["destination", "date_start"]:
            return paginate_and_sort(request, ArrangementModel, arrangement_list_schema, "arrangements_list", {key: value})
        else:
            return {"message": ARRANGEMENT_LIST_DEST_TIME_KEY_ERROR}, HTTP_400_BAD_REQUEST


class DetailedListTourGuideArrangement(Resource):
    """ Get Detailed List of all Arrangements TRAVEL_GUIDE was/is booked for. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TRAVEL_GUIDE.value])
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema, "arrangements_list", {"tour_guide_id": get_jwt_identity()})


class DetailedListArrangement(Resource):
    """ Get Detailed List of all Arrangements. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value, UserRoles.TRAVEL_GUIDE.value])
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema, "arrangements_list")


class ListByCreatorArrangement(Resource):
    """ Get Detailed List of all Arrangements created by current Admin User. """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return paginate_and_sort(request, ArrangementModel, arrangement_list_schema, "arrangements_list", {"users_id": get_jwt_identity()})