from flask import Flask, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://user:pass@postgres_db_container/db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True
api = Api(app)

db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
class Register(Resource):
    def post(self):
        data = request.get_json()

        if User.find_by_username(data['username']):
            return {"message": "A user with that username already exists"}, 400

        user = User(**data)
        user.save_to_db()
        return {"message": f"User {data['username']} created successfully."}, 201

class FindUser(Resource):
    def post(self):
        data = request.get_json()
        print(data["username"])

        # test code
        user = User.find_by_username(data["username"])
        if user:
            return {"message": f"User {data['username']} found."}, 200
        else:
            return {"message": f"User {data['username']} not found."}, 401


api.add_resource(Register, '/register')
api.add_resource(FindUser, '/find_user')

if __name__=="__main__":
    app.run(host='0.0.0.0')
