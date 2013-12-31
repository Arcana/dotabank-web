"""

Add archive jobs for the latest matches played by Dotabank premium subscribers.

Limit matches by either:
1) Subscription activation time
2) Latest match start time, so long as the match occured after subscription activation time.

Note: WebAPI doesn't handle timestamps exactly, so each request can a few older matches.

What do:
Run as a cron-job reguarly.  Doesn't handle the pagination of results, so as long as a user has not played >100 games
between runs we're good.

Improvements that can be made:
1) Handle result pagination.
2) Handle shit asyncronously; we're going to bottleneck with a lot of subs from waiting (WebAPI, DB, AWS queue)
3) Create ReplayPlayer entries from WebAPI data. (Note: Need to change dotabank-gc behaviour to check for existance of
ReplayPlayer entries before doing this, else we could get duplicate DB entries.  Maybe dotabank-gc already behaves. vOv)

"""

from app import steam, db  # .info
from app.users.models import Subscription
from app.replays.models import Replay, ReplayPlayer

subscriptions = Subscription.get_valid_subscriptions()

print "Found {} valid subscribers".format(len(subscriptions))
for subscription in subscriptions:
    webapi_params = {
        "account_id": subscription.user_id,
        "date_min": None,
        "matches_requested": 100  # 100 Max
    }

    latest_replay = Replay.query.\
        filter(Replay.id == ReplayPlayer.replay_id,
               ReplayPlayer.account_id == subscription.user_id).\
        order_by(Replay.start_time.desc()).first()

    if latest_replay.start_time >= subscription.created_at_timestamp:
        webapi_params["date_min"] = latest_replay.start_time
        # Can't use start_at_match_id because that filters out newer games, not older games.
    else:
        webapi_params["date_min"] = subscription.created_at_timestamp

    matches = steam.api.interface("IDOTA2Match_570").GetMatchHistory(**webapi_params).get("result")

    print "Found {} matches for {}".format(len(matches.get("matches")), subscription.user_id)
    for match in matches.get("matches"):
        replay_exists = Replay.query.filter(Replay.id == match["match_id"]).count() > 0

        if not replay_exists:
            replay = Replay(match["match_id"])
            replay.match_seq_num = match["match_seq_num"]
            replay.start_time = match["start_time"]
            replay.lobby_type = match["lobby_type"]
            db.session.add(replay)
            db.session.commit()

            Replay.add_gc_job(replay)

            print "Added {} to database and job queue".format(match["match_id"])
        else:
            print "Match {} already in database, skipping.".format(match["match_id"])
