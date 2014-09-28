#!/srv/www/dotabank.com/dotabank-web/bin/python

"""
Manager script :)
"""

from app import app as application, db
from flask.ext.script import Manager

manager = Manager(application)

@manager.command
def init_db():
    db.create_all()


@manager.command
def archive_subscriber_matches():
    from app.cron.archive_subscriber_matches import archive_subscriber_matches as _archive_subscriber_matches
    _archive_subscriber_matches()


@manager.command
def update_league_data():
    from app.leagues.models import League
    League.update_leagues_from_webapi()

if __name__ == "__main__":
    manager.run()