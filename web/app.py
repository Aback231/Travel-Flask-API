from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from marshmallow import ValidationError

from constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from helpers.docker_id import get_docker_id
from blacklist_redis import jwt_redis_blocklist
from blacklist import BLACKLIST
from resources.user import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    UserLogout,
    UserAccountChangeRequest,
    UserAccountChange,
    UserProfileView,
    UserProfileList,
    UserProfileUpdate,
    ListAccountChangeRequests,
)
from resources.arrangement import (
    Arrangement,
    DetailedListArrangement,
    ReservationsListArrangement,
    BasicListArrangement,
    ListByCreatorArrangement,
    ListByDestinationOrTimeArrangement,
    PickTourGuideArrangement,
    DetailedListTourGuideArrangement,
)
from resources.reservation import (
    CreateReservation,
    ListPerUserReservation,
    BasicListReservation
)


app = Flask(__name__)
app.config.from_prefixed_env()
api = Api(app)


# App level 404 error handling
@app.errorhandler(HTTP_404_NOT_FOUND)
def page_not_found(err):
    return {"error": str(err)}, HTTP_404_NOT_FOUND


# App level 500 error handling
@app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
def page_not_found(err):
    return {"error": str(err)}, HTTP_500_INTERNAL_SERVER_ERROR


# App level Validation error handling
@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), HTTP_400_BAD_REQUEST


jwt = JWTManager(app)


# Check if Token is blacklisted in Memory, not working when scaling
""" @jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(arg, decrypted_token):
    return decrypted_token["jti"] in BLACKLIST """


# Callback function to check if JWT exists in the Redis blacklist
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None


@app.route("/docker_id")
def home():
    return f"App instance: {get_docker_id()}"


api.add_resource(UserRegister, "/register")
api.add_resource(UserLogin, "/login")
api.add_resource(TokenRefresh, "/refresh")
api.add_resource(UserLogout, "/logout")
api.add_resource(UserProfileView, "/user_profile_view")
api.add_resource(UserProfileList, "/user_profile_list/")
api.add_resource(UserProfileUpdate, "/user_profile_update")
api.add_resource(UserAccountChangeRequest, "/acc_change_request")
api.add_resource(UserAccountChange, "/acc_change")
api.add_resource(ListAccountChangeRequests, "/list_acc_change_requests")

api.add_resource(Arrangement, "/arrangement")
api.add_resource(ReservationsListArrangement, "/reserved_arrangements/")
api.add_resource(PickTourGuideArrangement, "/pick_tour_guide/")
api.add_resource(DetailedListArrangement, "/arrangements/")
api.add_resource(BasicListArrangement, "/arrangements_basic/")
api.add_resource(ListByDestinationOrTimeArrangement, "/arrangements_dest_time/<string:key>/<string:value>")
api.add_resource(ListByCreatorArrangement, "/arrangements_by_creator/")
api.add_resource(DetailedListTourGuideArrangement, "/arrangements_by_tour_guide_booking/")

api.add_resource(CreateReservation, "/reservation_create")
api.add_resource(ListPerUserReservation, "/reservations")
api.add_resource(BasicListReservation, "/reservations_basic/")


if __name__ == "__main__":
    app.run(host=app.config["RUN_HOST"])
