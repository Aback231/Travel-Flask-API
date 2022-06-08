from db import db

DEFAULT_ACC_TYPE = "Tourist"
acc_type = ["Tourist", "Travel Guide", "Admin"]

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    email = db.Column(db.String(200))
    username = db.Column(db.String(80))
    password = db.Column(db.String(300))
    acc_type = db.Column(db.String(50))
    acc_type_requested = db.Column(db.String(50))

    def __init__(self, first_name, last_name, email, username, password, password_confirmation, acc_type):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        self.acc_type = DEFAULT_ACC_TYPE
        self.acc_type_requested = acc_type

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()
