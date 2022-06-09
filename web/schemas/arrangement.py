from ma import ma
from models.arrangement import ArrangementModel
from models.agency import AgencyModel


class ArrangemenSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArrangementModel
        load_only = ("agency",)
        dump_only = ("id",)
        include_fk = True
        load_instance = True