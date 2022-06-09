from ma import ma
from models.user import UserModel


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_only = ("password", "password_confirmation")
        dump_only = ("id",)
        load_instance = True

class LogInSchema(UserSchema):
    class Meta(UserSchema.Meta):
        exclude = ('id', "first_name", "last_name", "email", "acc_type", "acc_type_requested")