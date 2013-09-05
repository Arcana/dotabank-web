from dotabank import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __init__(self, id, name=None):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<User {}>".format(self.name)
