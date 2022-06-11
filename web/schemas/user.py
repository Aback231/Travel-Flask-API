from ma import ma
from models.user import UserModel
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangementSchema
from models.reservation import ReservationModel
from schemas.reservation import ReservationSchema


class UserSchema(ma.SQLAlchemyAutoSchema):
    users_id = ma.Nested(ArrangementSchema, many=True)
    """ arrangements_id = ma.Nested(ReservationSchema, many=True) """
    class Meta:
        model = UserModel
        ordered = True
        load_only = ("password", "password_confirmation")
        dump_only = ("id",)
        load_instance = True


class LogInSchema(UserSchema):
    class Meta(UserSchema.Meta):
        exclude = ('id', "first_name", "last_name", "email", "acc_type", "acc_type_requested")