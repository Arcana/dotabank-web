from datetime import datetime, timedelta
from sqlalchemy import text
from app import app, db, sentry, dotabank_bucket
from app.replays.models import Replay, ReplayPlayer, ReplayAutoFix


def should_fix_be_attempted(replay_id, error, extra=None):
    """
    Checks whether we've hit the limit for auto fix attempts for the given replay_id and error.  If not, return true
    and log add log this new fix attempt in the DB.  If we have hit the limit return false and log the beef to Sentry
    :param replay_id: How many faces Void has lost.
    :param error: Error type
    :param extra: Any extra data (will be JSON encoded)
    :return: Boolean
    """
    fix_attempts = ReplayAutoFix.query.filter(
        ReplayAutoFix.replay_id == replay_id,
        ReplayAutoFix.error == error
    ).all()

    if len(fix_attempts) <= app.config['MAX_REPLAY_FIX_ATTEMPTS']:
        fix_attempt = ReplayAutoFix(replay_id, error, extra)
        db.session.add(fix_attempt)
        db.session.commit()
        return True
    else:
        sentry.captureMessage("Replay {} with error {} has exceeded auto-fix attempts.".format(
            replay_id,
            error
        ), extra=extra)
        return False


def fix_incorrect_player_counts():
    """ Finds and attempts to fix all replays where `Replay.human_players` does not match the quantity of `ReplayPlayer`
    objects we have in the database.

    Attempts to fix by deleting all ReplayPlayer objects and re-adding the replay to the job queue.
    """
    _error = "PLAYER_COUNT_MISMATCH"

    human_players_discrepancy = [x for x in db.engine.execute(
        text("""
            SELECT
                r.id,
                r.human_players,
                count(rp.id) as player_count
            FROM {replay_table} r
            LEFT JOIN {player_table} rp ON rp.replay_id = r.id
            WHERE
                r.state != "GC_ERROR" and
                (rp.id is NULL or
                rp.account_id is not NULL)  # Exclude bots from count (though there's the chance we have duplicate entries for bots? fack)
            GROUP BY r.id
        """.format(
            replay_table=Replay.__tablename__,
            player_table=ReplayPlayer.__tablename__)
        )
    ) if x.player_count != x.human_players]

    for replay_id, human_count, player_count in human_players_discrepancy:
        if not should_fix_be_attempted(replay_id, _error, {'human_count': human_count, 'player_count': player_count}):
            continue

        print("Replay {} has a human_count of {}, but we have {} player objects for this replay.".format(
            replay_id,
            human_count,
            player_count
        ))
        replay = Replay.query.filter(Replay.id == replay_id).one()
        print("\tDeleting ReplayPlayer objects")
        for player in replay.players:
            db.session.delete(player)
        db.session.commit()

        print("\tRe-adding replay to GC queue")
        Replay.add_gc_job(replay)


def fix_small_replays():
    """ Finds replays with a tiny filesize and re-adds them to the GC queue (we probably downloaded a error page.
    """
    _error = "SMALL_REPLAY"

    small_replay_files = {replay_file.key[8:-8]: replay_file.size for replay_file in dotabank_bucket.list()
                          if replay_file.key[:8] == "replays/" and replay_file.size < (1024 * 1024)}
    small_replays = Replay.query.filter(Replay.state == "ARCHIVED", Replay.id.in_(small_replay_files.keys())).all()

    for replay in small_replays:
        if not should_fix_be_attempted(replay.id, _error, extra={
            'file_size': small_replay_files[unicode(replay.id)]
        }):
            continue

        print ("Replay {} has a small file stored on s3 ({} bytes).  Re-adding to GC queue.".format(
            replay.id,
            small_replay_files[unicode(replay.id)]
        ))
        replay.state = "WAITING_GC"  # Switch state back to WAITING_GC.
        Replay.add_dl_job(replay)


def fix_missing_files():
    """ Finds replays set as "ARCHIVED" that are missing a corresponding file stored in S3. Re-adds them
        to GC queue. """
    _error = "MISSING_S3_FILE"

    all_s3_replay_ids = [replay_file.key[8:-8] for replay_file in dotabank_bucket.list() if replay_file.key[:8] == "replays/"]
    archived_replays_no_file = Replay.query.filter(Replay.state == 'ARCHIVED', Replay.id.notin_(all_s3_replay_ids)).all()

    for replay in archived_replays_no_file:
        if not should_fix_be_attempted(replay.id, _error):
            # Tag as "DOWNLOAD_ERROR" because we can't fix this - the problem is entirely in Valve (or their partners) domain.
            replay.state = "DOWNLOAD_ERROR"
            replay.local_uri = None
            replay.dl_done_time = None
            db.session.add(replay)
            db.session.commit()
            continue

        print ("Replay {} is \"ARCHIVED\" but does not have a file stored on S3. Re-adding to GC queue.".format(
            replay.id
        ))
        replay.state = "WAITING_GC"  # Switch state back to WAITING_GC.
        Replay.add_dl_job(replay)


def fix_long_waiting_download():
    """  Finds replays that have been "WAITING_DOWNLOAD" for over 24 hours, and re-adds them to the GC queue. """
    _error = "LONGEST_WAIT_OF_MY_LIFE"

    replay_waiting_download_over24hrs = Replay.query.filter(
        Replay.state == "WAITING_DOWNLOAD",
        Replay.gc_done_time <= (datetime.utcnow() - timedelta(hours=24))  # Over 24 hrs ago
    ).all()

    for replay in replay_waiting_download_over24hrs:
        if not should_fix_be_attempted(replay.id, _error):
            continue


        print ("Replay {} has been \"WAITING_DOWNLOAD\" for over 24 hours. Re-adding to GC queue.".format(
            replay.id
        ))
        replay.state = "WAITING_GC"  # Switch state back to WAITING_GC.
        Replay.add_dl_job(replay)