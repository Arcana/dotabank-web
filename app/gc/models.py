from app import db
import datetime

# noinspection PyShadowingBuiltins
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

    def job_count(self, hours=24):
        """ Returns the amount of jobs this worker has processed in the past `hours` hours.
        :param hours:
        :return: Int
        """
        return GCJob.query.filter(
            GCJob.worker_id == self.id,
            GCJob.type == "MATCH_REQUEST",
            GCJob.timestamp >= (datetime.datetime.utcnow() - datetime.timedelta(hours=hours))
        ).count()


# noinspection PyShadowingBuiltins
class GCJob(db.Model):
    __tablename__ = "gc_jobs"
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey("gc_workers.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Enum(
        "SHITS_BROKE",
        "MATCH_REQUEST",
        "PROFILE_REQUEST"
    ), default='SHITS_BROKE', index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def __repr__(self):
        return "<GCJob {}>".format(self.id)
