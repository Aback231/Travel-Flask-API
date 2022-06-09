from ma import ma
from models.agency import AgencyModel
from models.arrangement import ArrangementModel
from schemas.arrangement import ArrangemenSchema


class AgencySchema(ma.SQLAlchemyAutoSchema):
    items = ma.Nested(ArrangemenSchema, many=True)

    class Meta:
        model = AgencyModel
        dump_only = ("id",)
        include_fk = True
        load_instance = True