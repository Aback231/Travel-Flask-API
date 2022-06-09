from flask_restful import Resource

from models.agency import AgencyModel
from schemas.agency import AgencySchema
from decorators.roles import roles
from helpers.user_roles import UserRoles

NAME_ALREADY_EXISTS = "Agency with name '{}' already exists."
ERROR_INSERTING = "An error occurred while inserting the agency."
AGENCY_NOT_FOUND = "Agency not found."
AGENCY_DELETED = "Agency deleted."

agency_schema = AgencySchema()
agency_list_schema = AgencySchema(many=True)


class Agency(Resource):
    @classmethod
    def get(cls, name: str):
        agency = AgencyModel.find_by_name(name)
        if agency:
            return agency_schema.dump(agency), 200

        return {"message": AGENCY_NOT_FOUND}, 404

    @classmethod
    def post(cls, name: str):
        if AgencyModel.find_by_name(name):
            return {"message": NAME_ALREADY_EXISTS.format(name)}, 400

        agency = AgencyModel(name=name)
        try:
            agency.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return agency_schema.dump(agency), 201

    @classmethod
    def delete(cls, name: str):
        agency = AgencyModel.find_by_name(name)
        if agency:
            agency.delete_from_db()
            return {"message": AGENCY_DELETED}, 200

        return {"message": AGENCY_NOT_FOUND}, 404

# Get List of all Agencies
class AgencyList(Resource):
    @classmethod
    def get(cls):
        return {"agencies": agency_list_schema.dump(AgencyModel.find_all())}, 200
