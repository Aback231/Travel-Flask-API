import traceback
from flask_restful import Resource
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required

from helpers import date_parser
from libs.mailgun import MailGunException
from libs.mailgun import Mailgun
from libs.pagination_and_sorting import paginate_and_sort
from models.reservation import ReservationModel
from schemas.reservation import ReservationSchema
from models.arrangement import ArrangementModel
from models.user import UserModel
from decorators.roles import roles
from helpers.user_roles import UserRoles

from db import db


FAILED_TO_CREATE_RESERVATION = "Internal server error. Failed to create reservation."
RESERVATION_UPDATED = "Reservation updated."
RESERVATION_CREATION_SUCCESS = "Reservation created successfully."
RESERVATION_CREATION_FAIL = "Reservation failed, requested arrangement id does not exist."
RESERVATION_CREATION_FAIL_NO_PLACES = "Reservation failed, no available places left."
ARRANGEMENT_TIME_TO_START_ERROR = "Arrangement has less than 5 days to start! Can't be reserved."

MAILGUN_SUBJECT_RESERVATION = "Reservation confirmation"
MAILGUN_HTML_RESERVATION_SUCCESS = ("<html>Reservation created successfully. Price to pay <b>{}</b></html>")
MAILGUN_HTML_RESERVATION_FAIL = "<html>Reservation failed, requested arrangement id does not exist.</html>"
MAILGUN_HTML_RESERVATION_FAIL_NO_PLACES = "<html>Reservation failed, no available places left</html>"


DISCOUNT_RESERVATIONS_TRESHOLD = 3
DISCOUNT_PERCENTAGE = 10


reservation_schema = ReservationSchema()
reservation_list_schema = ReservationSchema(many=True)


def price_calculation(nr_reservations: int, price: float) -> float:
    """ Calculate price sum with discount for arrangement reservation """
    price_sum = nr_reservations * price
    if nr_reservations > DISCOUNT_RESERVATIONS_TRESHOLD:
        price_sum = price_sum - (nr_reservations - DISCOUNT_RESERVATIONS_TRESHOLD) * (price * DISCOUNT_PERCENTAGE/100)
    return price_sum


class ReservationCreate(Resource):
    """ TOURIST Arrangement reservation. If arrangement and reservation for given arrangement ID and current user ID 
        exist, reservation and arrangement availability will be updated if enough places exist """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.TOURIST.value])
    def post(cls):
        
        reservation_json = request.get_json()
        reservation = reservation_schema.load(reservation_json)

        reservation_query = ReservationModel.find_by_arrangement_id_and_reserver_user_id(reservation.arrangement_id, get_jwt_identity())
        arrangement = ArrangementModel.find_by_id(reservation.arrangement_id)
        user = UserModel.find_by_id(get_jwt_identity())

        try:
            if not arrangement:
                Mailgun.send_email([user.email], MAILGUN_SUBJECT_RESERVATION, MAILGUN_HTML_RESERVATION_FAIL)
                return {"message": RESERVATION_CREATION_FAIL}, 400

            if not date_parser.is_arrangement_reservable(arrangement.date_start):
                return {"message": ARRANGEMENT_TIME_TO_START_ERROR}, 400
            
            """ Update reservation places for arrangement and user reservation. """
            if reservation_query:
                arrangement_places_left = arrangement.nr_places_available - reservation.num_reservations
                if arrangement_places_left >= 0:
                    reservation_query.num_reservations += reservation.num_reservations
                    reservation_query.save_to_db()
                    arrangement.nr_places_available = arrangement_places_left
                    arrangement.save_to_db()

                    Mailgun.send_email([user.email], MAILGUN_SUBJECT_RESERVATION, MAILGUN_HTML_RESERVATION_SUCCESS.format(price_calculation(reservation.num_reservations, arrangement.price)))
                    return {"message": RESERVATION_UPDATED}, 200

                Mailgun.send_email([user.email], MAILGUN_SUBJECT_RESERVATION, MAILGUN_HTML_RESERVATION_FAIL_NO_PLACES)
                return {"message": RESERVATION_CREATION_FAIL_NO_PLACES}, 400

            """ Create new reservation for user and deduct reservation places.  """
            arrangement_places_left = arrangement.nr_places_available - reservation.num_reservations

            if arrangement_places_left >= 0:
                arrangement.nr_places_available = arrangement_places_left
                arrangement.save_to_db()

                reservation.reserver_user_id = get_jwt_identity()
                reservation.save_to_db()

                Mailgun.send_email([user.email], MAILGUN_SUBJECT_RESERVATION, MAILGUN_HTML_RESERVATION_SUCCESS.format(price_calculation(reservation.num_reservations, arrangement.price)))
                return {"message": RESERVATION_CREATION_SUCCESS}, 201

            Mailgun.send_email([user.email], MAILGUN_SUBJECT_RESERVATION, MAILGUN_HTML_RESERVATION_FAIL_NO_PLACES)
            return {"message": RESERVATION_CREATION_FAIL_NO_PLACES}, 400
        except MailGunException as e:
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            return {"message": FAILED_TO_CREATE_RESERVATION}, 500


class ReservationListPerUser(Resource):
    """ Get all reservations for user by ID """
    @classmethod
    @jwt_required()
    def get(cls):
        return paginate_and_sort(request, ReservationModel, reservation_list_schema, "reservations", {"id": get_jwt_identity()})


class ReservationListBasic(Resource):
    """ Get list of all reservations in reservation table """
    @classmethod
    @jwt_required()
    @roles.role_auth([UserRoles.ADMIN.value])
    def get(cls):
        return paginate_and_sort(request, ReservationModel, reservation_list_schema, "reservation_items")
