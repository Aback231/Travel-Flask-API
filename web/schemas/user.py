from ma import ma
from models.user import UserModel
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangementSchema


class UserSchema(ma.SQLAlchemyAutoSchema):
    users_id = ma.Nested(ArrangementSchema, many=True)
    class Meta:
        model = UserModel
        ordered = True
        load_only = ("password", "password_confirmation")
        dump_only = ("id",)
        load_instance = True


class LogInSchema(UserSchema):
    class Meta(UserSchema.Meta):
        exclude = ('id', "first_name", "last_name", "email", "acc_type", "acc_type_requested")