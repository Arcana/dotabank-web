from app import db
import datetime


class GCWorker(db.Model):
    __tablename__ = "gc_workers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.BLOB, nullable=False)
    display_name = db.Column(db.String(32), nullable=False)
    auth_code = db.Column(db.String(32))
    sentry = db.Column(db.BLOB)

    jobs = db.relationship('GCJob', backref='worker', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, username=None, password=None, display_name=None, auth_code=None):
        self.username = username,
        self.password = password,
        self.display_name = display_name
        self.auth_code = auth_code

    def __repr__(self):
        return "<GCWorker {}>".format(self.id)


class GCJob(db.Model):
    __tablename__ = "gc_jobs"
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("gc_workers.id", ondelete="CASCADE"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<GCJob {}>".format(self.id)
