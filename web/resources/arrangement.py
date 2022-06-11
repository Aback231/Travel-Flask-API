from flask_restful import Resource
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required

from helpers import date_parser
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangementSchema, ArrangementSchemaBasic
from decorators.roles import roles
from helpers.user_roles import UserRoles


NAME_ALREADY_EXISTS = "An arrangement with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the arrangement."
ARRANGEMENT_NOT_FOUND = "Arrangement not found."
ARRANGEMENT_DELETED = "Arrangement deleted."
ARRANGEMENT_ALREADY_EXISTS = "Arrangement already exists."
ARRANGEMENT_CREATION_SUCCESS = "Arrangement created successfully."
ARRANGEMENT_TIME_TO_START_ERROR = "Arrangement has less than 5 days to start!"
ARRANGEMENT_DEACTIVATED_SECCESS = "Arrangement was deactivated successfully."
ARRANGEMENT_DEACTIVATED_ALREADY = "Arrangement was already deactivated."


arrangement_schema = ArrangementSchema()
arrangement_list_schema = ArrangementSchema(many=True)
arrangement_list_schema_basic = ArrangementSchemaBasic(many=True)


class Arrangement(Resource):
    """ Create Arrangement """
    """ @classmethod
    def get(cls, destination: str):
        arrangement = ArrangementModel.find_by_name(destination)
        if arrangement:
            return arrangement_schema.dump(arrangement), 200
        return {"message": ARRANGEMENT_NOT_FOUND}, 404 """


    ## FIND ARRANGEMENTS CREATED BY USER BY ID
    """ @classmethod
    @jwt_required()
    def get(cls, user_id: int):
        arrangement = ArrangementModel.find_by_id(user_id)
        if arrangement:
            return arrangement_schema.dump(arrangement), 200
        return {"message": ARRANGEMENT_NOT_FOUND}, 404 """


    """ @classmethod
    @jwt_required()
    def post(cls, name: str):
        if ArrangementModel.find_by_name(name):
            return {"message": NAME_ALREADY_EXISTS.format(name)}, 400

        arrangement_json = request.get_json()
        arrangement = arrangement_schema.load(arrangement_json)

        try:
            arrangement.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return arrangement_schema.dump(arrangement), 201 """


    """ Delete Arrangement """
    """ @classmethod
    @jwt_required()
    def delete(cls, name: str):
        arrangement = ArrangementModel.find_by_name(name)
        if arrangement:
            arrangement.delete_from_db()
            return {"message": ARRANGEMENT_DELETED}, 200
        return {"message": ARRANGEMENT_NOT_FOUND}, 404 """






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


class ArrangementDeactivate(Resource):
    """ Admin can deactivate an Arrangement at latest 5 days before it starts """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def put(cls, id: int):
        arrangement = ArrangementModel.find_by_id(id)

        if not date_parser.has_arrangement_5_days_to_start(arrangement.date_start):
            return {"message": ARRANGEMENT_TIME_TO_START_ERROR}, 400
        
        if not arrangement.is_active:
            return {"message": ARRANGEMENT_DEACTIVATED_ALREADY}, 200

        arrangement.is_active = False
        arrangement.save_to_db()

        return {"message": ARRANGEMENT_DEACTIVATED_SECCESS}, 200


class ArrangementListBasic(Resource):
    """ Get Basic List of all Arrangements, no need for login """
    @classmethod
    def get(cls):
        return {"items": arrangement_list_schema_basic.dump(ArrangementModel.find_all())}, 200


class ArrangementList(Resource):
    """ Get Detailed List of all Arrangements, login required """
    @classmethod
    @jwt_required()
    def get(cls):
        return {"items": arrangement_list_schema.dump(ArrangementModel.find_all())}, 200


class ArrangementListByCreator(Resource):
    """ Get Detailed List of all Arrangements created by an Admin, login required """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return {"items": arrangement_list_schema.dump(ArrangementModel.find_all_by_creator_id(get_jwt_identity()))}, 200