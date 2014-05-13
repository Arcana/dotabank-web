#!/srv/www/dotabank.com/dotabank-web/bin/python
"""
Downoad and archive TI4 matches
"""

from app import steam, db  # .info
from app.replays.models import Replay, ReplayPlayer

THE_INTERNATIONAL_4_ID = 600

matches = steam.api.interface("IDOTA2Match_570").GetMatchHistory(league_id=THE_INTERNATIONAL_4_ID).get("result")

if matches:
    for match in matches.get("matches"):
        replay_exists = Replay.query.filter(Replay.id == match["match_id"]).count() > 0

        if not replay_exists:
            replay = Replay(match["match_id"])
            db.session.add(replay)
            db.session.commit()

            Replay.add_gc_job(replay)

            print "Added {} to database and job queue".format(match["match_id"])
        else:
            print "Match {} already in database, skipping.".format(match["match_id"])