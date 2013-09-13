from app import db
from flask.ext.login import AnonymousUserMixin
import datetime


class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    first_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='select', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='user', lazy='select', cascade="all, delete-orphan")

    def __init__(self, _id=None, name=None, enabled=True, first_seen=datetime.datetime.utcnow(), last_seen=datetime.datetime.utcnow()):
        self.id = _id
        self.name = name
        self.enabled = enabled
        self.first_seen = first_seen
        self.last_seen = last_seen

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

    def is_admin(self):
        return self.admin

    def update_last_seen(self):
        # Called every page load for current_user
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()
