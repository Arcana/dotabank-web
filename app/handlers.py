from app import db
from app.models import Log

import json
import logging
import traceback


class SQLAlchemyHandler(logging.Handler):
    # A very basic logger that commits a LogRecord to the SQL Db
    def emit(self, record):

        trace = traceback.format_exc(record.__dict__['exc_info']) if record.__dict__['exc_info'] else None
        extra = json.dumps(record.__dict__['extra']) if "extra" in record.__dict__ else None

        log = Log(
            logger=record.__dict__['name'],
            level=record.__dict__['levelname'],
            trace=trace,
            msg=record.__dict__['msg'],
            extra=extra)
        db.session.add(log)
        db.session.commit()

