from app import db
from app.models import Log

import json
import logging
import traceback


class SQLAlchemyHandler(logging.Handler):
    """ Logging handler which commits log entries to the database. """

    def emit(self, record):  # TODO: Store IP and endpoint accessed.
        """ Catch the log entry, grab any traceback data and any extra data if provided. """
        trace = traceback.format_exc(record.__dict__['exc_info']) if record.__dict__['exc_info'] else None
        extra = json.dumps(record.__dict__['extra']) if "extra" in record.__dict__ else None

        log = Log(
            logger=record.__dict__['name'],
            level=record.__dict__['levelname'],
            trace=trace,
            msg=record.__dict__['msg'],
            extra=extra)

        # If we hit an error we need to ROLL THE FUCK BACK so we can save to database.
        if log.level >= logging.ERROR:
            db.session.rollback()

        db.session.add(log)
        db.session.commit()

