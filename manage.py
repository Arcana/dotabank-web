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


@manager.command
def fix_incorrect_player_counts():
    from app.cron.fix_replay_errors import fix_incorrect_player_counts
    fix_incorrect_player_counts()


@manager.command
def fix_small_replays():
    from app.cron.fix_replay_errors import fix_small_replays
    fix_small_replays()


@manager.command
def fix_missing_files():
    from app.cron.fix_replay_errors import fix_missing_files
    fix_missing_files()


@manager.command
def fix_long_waiting_download():
    from app.cron.fix_replay_errors import fix_long_waiting_download
    fix_long_waiting_download()


@manager.command
def fetch_league_matches(league_id):
    from app.cron.fetch_league_matches import fetch_league_matches
    fetch_league_matches(league_id)


if __name__ == "__main__":
    manager.run()