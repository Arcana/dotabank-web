from app import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    enabled = db.Column(db.Boolean, default=True)

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='dynamic')

    def __init__(self, _id=None, name=None, enabled=True):
        self.id = _id
        self.name = name
        self.enabled = enabled

    def __repr__(self):
        return self.name

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True


class Replay(db.Model):
    __tablename__ = "replays"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    replay_state = db.Column(db.Enum(
        "REPLAY_AVAILABLE",
        "REPLAY_NOT_RECORDED",
        "REPLAY_EXPIRED",
        "UNKNOWN"
    ), default="UNKNOWN")
    state = db.Column(db.Enum(
        "WAITING_GC",
        "WAITING_DOWNLOAD",
        "DOWNLOAD_IN_PROGRESS",
        "WAITING_PARSE",
        "PARSE_IN_PROGRESS",
        "PARSED",
        "GC_ERROR",
        "PARSE_ERROR"
    ), default="WAITING_GC")

    ratings = db.relationship('ReplayRating', backref='replay', lazy='dynamic')

    def __init__(self, _id=None, url=None, state="UNKNOWN", parse_state="WAITING_GC"):
        self.id = _id
        self.url = url
        self.state = state
        self.parse_state = parse_state

    def __repr__(self):
        return "<Replay {}>".format(self.id)


class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    positive = db.Column(db.Boolean)

    def __init__(self, replay_id=None, user_id=None, positive=None):
        self.replay_id = replay_id
        self.user_id = user_id
        self.positive = positive

    def __repr__(self):
        return "<Rating {}/{}>".format(self.replay_id, self.user_id)
