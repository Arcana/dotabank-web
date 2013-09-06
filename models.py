from app import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='dynamic')

    def __init__(self, _id=None, name=None):
        self.id = _id
        self.name = name

    def __repr__(self):
        return self.name


class Replay(db.Model):
    __tablename__ = "replays"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    state = db.Column(db.Enum("REPLAY_AVAILABLE", "REPLAY_NOT_RECORDED", "REPLAY_EXPIRED"))
    parsed = db.Column(db.Boolean)

    ratings = db.relationship('ReplayRating', backref='replay', lazy='select')

    def __init__(self, _id=None, url=None, state=None, parsed=False):
        self.id = _id
        self.url = url
        self.state = state
        self.parsed = parsed

    def __repr__(self):
        return "<Replay {}>".format(self.id)


class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    rating = db.Column(db.Integer)

    def __init__(self, replay_id=None, user_id=None, rating=None):
        self.replay_id = replay_id
        self.user_id = user_id
        self.rating = rating

    def __repr__(self):
        return "<Rating {}/{}>".format(self.replay_id, self.user_id)
