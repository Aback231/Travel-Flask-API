from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required

from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangemenSchema
from decorators.roles import roles
from helpers.user_roles import UserRoles

NAME_ALREADY_EXISTS = "An arrangement with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the arrangement."
ARRANGEMENT_NOT_FOUND = "Arrangement not found."
ARRANGEMENT_DELETED = "Arrangement deleted."

arrangement_schema = ArrangemenSchema()
arrangement_list_schema = ArrangemenSchema(many=True)

class Arrangement(Resource):
    @classmethod
    def get(cls, name: str):
        arrangement = ArrangementModel.find_by_name(name)
        if arrangement:
            return arrangement_schema.dump(arrangement), 200
        return {"message": ARRANGEMENT_NOT_FOUND}, 404

    @classmethod
    @jwt_required(fresh=True)
    def post(cls, name: str):
        if ArrangementModel.find_by_name(name):
            return {"message": NAME_ALREADY_EXISTS.format(name)}, 400

        arrangement_json = request.get_json()
        arrangement_json["name"] = name

        arrangement = arrangement_schema.load(arrangement_json)

        try:
            arrangement.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return arrangement_schema.dump(arrangement), 201

    @classmethod
    @jwt_required
    def delete(cls, name: str):
        arrangement = ArrangementModel.find_by_name(name)
        if arrangement:
            arrangement.delete_from_db()
            return {"message": ARRANGEMENT_DELETED}, 200
        return {"message": ARRANGEMENT_NOT_FOUND}, 404

    @classmethod
    def put(cls, name: str):
        arrangement_json = request.get_json()
        arrangement = ArrangementModel.find_by_name(name)

        if arrangement:
            arrangement.price = arrangement_json["price"]
        else:
            arrangement_json["name"] = name
            arrangement = arrangement_schema.load(arrangement_json)

        arrangement.save_to_db()

        return arrangement_schema.dump(arrangement), 200

# Get List of all Arrangements
class ArrangementList(Resource):
    @classmethod
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return {"items": arrangement_list_schema.dump(ArrangementModel.find_all())}, 200
