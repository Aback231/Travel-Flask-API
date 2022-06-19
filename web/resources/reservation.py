import traceback
from flask_restful import Resource
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required

from constants.http_status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from helpers import date_parser, price_parser
from libs.strings import get_text
from libs.mailgun import Mailgun, MailGunException
from helpers.pagination_and_sorting import paginate_and_sort
from models.reservation import ReservationModel
from schemas.reservation import ReservationSchema
from models.arrangement import ArrangementModel
from models.user import UserModel
from decorators.roles import roles
from constants.user_roles import UserRoles


reservation_schema = ReservationSchema()
reservation_list_schema = ReservationSchema(many=True)


class CreateReservation(Resource):
    """ TOURIST Arrangement reservation. If arrangement and reservation for given arrangement ID and current user ID 
        exist, reservation and arrangement availability will be updated if enough places exist """
    @classmethod
    @jwt_required(fresh=True)
    @roles.role_auth([UserRoles.TOURIST.value])
    def post(cls):
        reservation_json = request.get_json()
        reservation = reservation_schema.load(reservation_json)

        reservation_query = ReservationModel.find_by_arrangement_id_and_reserver_user_id(reservation.arrangement_id, get_jwt_identity())
        arrangement = ArrangementModel.find_by_id(reservation.arrangement_id)
        user = UserModel.find_by_id(get_jwt_identity())

        try:
            if not arrangement:
                Mailgun.send_email([user.email], get_text("RESERVATION_MAILGUN_SUBJECT"), get_text("RESERVATION_MAILGUN_HTML_FAIL"))
                return {"message": get_text("RESERVATION_CREATION_FAIL")}, HTTP_400_BAD_REQUEST

            if not date_parser.is_arrangement_reservable(arrangement.date_start):
                return {"message": get_text("RESERVATION_ARRANGEMENT_TIME_TO_START_ERROR")}, HTTP_400_BAD_REQUEST
            
            # Update reservation places for arrangement and user reservation.
            if reservation_query:
                arrangement_places_left = arrangement.nr_places_available - reservation.num_reservations
                if arrangement_places_left >= 0:
                    reservation_query.num_reservations += reservation.num_reservations
                    reservation_query.save_to_db()
                    arrangement.nr_places_available = arrangement_places_left
                    arrangement.save_to_db()

                    Mailgun.send_email([user.email], get_text("RESERVATION_MAILGUN_SUBJECT"), get_text("RESERVATION_MAILGUN_HTML_SUCCESS").format(price_parser.price_calculation(reservation.num_reservations, arrangement.price)))
                    return {"message": get_text("RESERVATION_UPDATED")}, HTTP_200_OK

                Mailgun.send_email([user.email], get_text("RESERVATION_MAILGUN_SUBJECT"), get_text("RESERVATION_MAILGUN_HTML_FAIL_NO_PLACES"))
                return {"message": get_text("RESERVATION_CREATION_FAIL_NO_PLACES")}, HTTP_400_BAD_REQUEST

            # Create new reservation for user and deduct reservation places.
            arrangement_places_left = arrangement.nr_places_available - reservation.num_reservations

            if arrangement_places_left >= 0:
                arrangement.nr_places_available = arrangement_places_left
                arrangement.save_to_db()

                reservation.reserver_user_id = get_jwt_identity()
                reservation.save_to_db()

                Mailgun.send_email([user.email], get_text("RESERVATION_MAILGUN_SUBJECT"), get_text("RESERVATION_MAILGUN_HTML_SUCCESS").format(price_parser.price_calculation(reservation.num_reservations, arrangement.price)))
                return {"message": get_text("RESERVATION_CREATION_SUCCESS")}, HTTP_201_CREATED

            Mailgun.send_email([user.email], get_text("RESERVATION_MAILGUN_SUBJECT"), get_text("RESERVATION_MAILGUN_HTML_FAIL_NO_PLACES"))
            return {"message": get_text("RESERVATION_CREATION_FAIL_NO_PLACES")}, HTTP_400_BAD_REQUEST
        except MailGunException as e:
            return {"message": str(e)}, HTTP_500_INTERNAL_SERVER_ERROR
        except:
            traceback.print_exc()
            return {"message": get_text("RESERVATION_FAILED_TO_CREATE")}, HTTP_500_INTERNAL_SERVER_ERROR


class ListPerUserReservation(Resource):
    """ Get all reservations for user by ID """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def get(cls):
        return paginate_and_sort(request, ReservationModel, reservation_list_schema, "reservations", {"reserver_user_id": get_jwt_identity()})


class BasicListReservation(Resource):
    """ Get list of all reservations in reservation table """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return paginate_and_sort(request, ReservationModel, reservation_list_schema, "reservations")
