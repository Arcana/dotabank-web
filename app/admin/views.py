from flask import Blueprint, g, current_app, redirect, request, flash, url_for, jsonify
from flask.ext.admin import Admin, expose, AdminIndexView, BaseView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from sqlalchemy.sql import text
from datetime import datetime, timedelta
from math import ceil

from app import db, steam, dotabank_bucket
from app.models import Log
from app.gc.models import GCJob, GCWorker
from app.replays.models import Replay, ReplayPlayer

# Create blueprint
mod = Blueprint("dotabank_admin", __name__)


class AuthMixin(object):
    """ Mixin for admin views to restrict access to only admin users. """
    def is_accessible(self):
        return current_user.is_admin()


class AdminModelView(AuthMixin, ModelView):
    """ Used for setting up admin-only model views """
    pass


class AdminIndex(AuthMixin, AdminIndexView):
    """ Flask-admin index view """

    @expose("/")
    def index(self):
        """ Reports the GCWorker utilization for the past 24 hrs. """

        gc_workers = GCWorker.query.all()

        stats = []
        for worker in gc_workers:

            stats.append({
                "id": worker.id,
                "display_name": worker.display_name,
                "match_requests_past_24hrs": GCJob.query.filter(
                    GCJob.worker_id == worker.id,
                    GCJob.type == "MATCH_REQUEST",
                    GCJob.timestamp >= (datetime.utcnow() - timedelta(hours=24))
                ).count(),
                "match_requests_capacity": current_app.config['GC_MATCH_REQUSTS_RATE_LIMIT']
            })

        return self.render('admin/index.html',
                           stats=stats)


class AtypicalReplays(AuthMixin, BaseView):
    """ Views for atypical-replay reports """

    @expose('/')
    def index(self):
        """ Renders a list of replays which are atypical.

        human_players_discrepancy: Replays where their human_player property doesn't match the count of ReplayPlayer
        objects we have in our database.

        replay_available_download_error: Replays which are available to download, but that our download script failed to
        retrieve.

        replay_waiting_download_over24hrs: Replays which have been waiting to be downloaded for over 24 hrs.
        """
        human_players_discrepancy = [x for x in db.engine.execute(
            text("""
                SELECT
                    r.id,
                    r.human_players,
                    count(*) as player_count
                FROM {replay_table} r
                LEFT JOIN {player_table} rp ON rp.replay_id = r.id
                WHERE
                    rp.account_id is not NULL  # Exclude bots from count (though there's the chance we have duplicate entries for bots? fack)
                GROUP BY rp.replay_id
            """.format(
                replay_table=Replay.__tablename__,
                player_table=ReplayPlayer.__tablename__)
            )
        ) if x.player_count != x.human_players]

        replay_available_download_error = Replay.query.filter(
            Replay.replay_state == "REPLAY_AVAILABLE",
            Replay.state == "DOWNLOAD_ERROR"
        ).all()

        replay_waiting_download_over24hrs = Replay.query.filter(
            Replay.state == "WAITING_DOWNLOAD",
            Replay.gc_done_time <= (datetime.utcnow() - timedelta(hours=24))  # Over 24 hrs ago
        ).all()

        small_replay_files = {replay_file.key[8:-8]: replay_file.size for replay_file in dotabank_bucket.list() if replay_file.key[:8] == "replays/" and replay_file.size < (1024 * 1024)}
        small_replays = Replay.query.filter(Replay.id.in_(small_replay_files.keys())).all()

        return self.render(
            'admin/atypical_replays.html',
            human_players_discrepancy=human_players_discrepancy,
            replay_available_download_error=replay_available_download_error,
            replay_waiting_download_over24hrs=replay_waiting_download_over24hrs,
            small_replays=small_replays,
            small_replay_files=small_replay_files
        )


class Logs(AuthMixin, BaseView):
    """ Views for database-stored site logs. """

    @expose('/')
    def index(self):
        """ Renders a list of latest resolved and unresolved log entries, also renders how many entries are in each
        state - linking to views to see the full list. """

        unresolved_logs = Log.query.filter(Log.resolved_by_user_id == None).\
            order_by(Log.created_at.desc()).\
            limit(current_app.config['LOGS_PER_PAGE']).all()
        unresolved_count = Log.query.filter(Log.resolved_by_user_id == None).count()

        resolved_logs = Log.query.filter(Log.resolved_by_user_id != None).\
            order_by(Log.resolved_at.desc()).\
            limit(current_app.config['LOGS_PER_PAGE']).\
            all()
        resolved_count = Log.query.filter(Log.resolved_by_user_id != None).count()

        return self.render(
            'admin/logs/index.html',
            unresolved_logs=unresolved_logs,
            unresolved_count=unresolved_count,
            resolved_logs=resolved_logs,
            resolved_count=resolved_count
        )

    @expose('/unresolved')
    @expose('/unresolved/<int:page>')
    def unresolved(self, page=None):
        """ Paginated view for all unresolved log entries. """
        if not page:
            page = int(ceil(float(Log.query.filter(Log.resolved_by_user_id == None).count() or 1) / float(current_app.config["LOGS_PER_PAGE"])))  # Default to last page

        logs = Log.query.filter(Log.resolved_by_user_id == None).paginate(page, current_app.config["LOGS_PER_PAGE"], False)

        return self.render(
            'admin/logs/unresolved.html',
            logs=logs
        )

    @expose('/resolved')
    @expose('/resolved/<int:page>')
    def resolved(self, page=None):
        """ Paginated view for all resolved log entries. """
        if not page:
            page = int(ceil(float(Log.query.filter(Log.resolved_by_user_id != None).count() or 1) / float(current_app.config["LOGS_PER_PAGE"])))  # Default to last page

        logs = Log.query.filter(Log.resolved_by_user_id != None).\
            order_by(Log.resolved_at.asc())\
            .paginate(page, current_app.config["LOGS_PER_PAGE"], False)

        return self.render(
            'admin/logs/resolved.html',
            logs=logs
        )

    @expose('/view/<int:_id>')
    def view(self, _id):
        """ View a specific log entry. """
        log_entry = Log.query.filter(Log.id == _id).first_or_404()

        return self.render(
            'admin/logs/view.html',
            log=log_entry
        )

    @expose('/view/<int:_id>/resolve')
    def mark_resolved(self, _id):
        """ Mark a log entry as resolved. """
        log_entry = Log.query.filter(Log.id == _id).first_or_404()

        log_entry.resolve(current_user.id)
        db.session.add(log_entry)
        db.session.commit()

        if request.is_xhr:
            return jsonify(success=True, resolved_by=log_entry.resolved_by_user_id, resolved_at=log_entry.resolved_at)
        else:
            flash("Log entry {} marked as resolved.".format(log_entry.id), "success")
            return redirect(request.referrer or url_for("index"))


class Maintenance(AuthMixin, BaseView):
    """ Views for maintenance replated functions """
    @expose('/')
    def index(self):
        """ Renders a list of maintenance actions, and a button to execute each action. """
        return self.render('admin/maintenance/index.html')


    @expose('/replay_repopulate')
    def replay_repopulate(self):
        """ AJAX endpoint to repopulate WebAPI data for every replay on the site. """
        # TODO: Accept a list of replays, rather than executing for all replays.
        # TODO: Make asyncronous.
        # TODO: Send progress data back to caller.

        success = []
        failed = []

        # For each replay, try repopulate from WebAPI.
        for replay in Replay.query.all():
            try:
                replay._populate_from_webapi()
                db.session.add(replay)
                success.append(replay)
            except steam.api.HTTPError:
                failed.append(replay)

        db.session.commit()

        return jsonify(
            success=True,
            replays_updated=[replay.id for replay in success],
            replays_failed=[replay.id for replay in failed]
        )

    @expose('/small_replay_exodus')
    def small_replay_exodus(self):
        small_replay_files = {replay_file.key[8:-8]: replay_file.size for replay_file in dotabank_bucket.list() if replay_file.key[:8] == "replays/" and replay_file.size < (1024 * 1024)}
        small_replays = Replay.query.filter(Replay.id.in_(small_replay_files.keys())).all()

        replays_removed = []  # IDs of removed replays
        for replay in small_replays:
            # Save local URI so we can remove the file from S3 after we've changed the databose.
            local_uri = replay.local_uri

            # Clean up metadata associated with an archived replay.
            replay.dl_done_time = None
            replay.local_uri = None
            replay.state = "WAITING_DOWNLOAD"

            # Save ne state to database
            db.session.add(replay)
            db.session.commit()

            # Remove bad file from S3.
            dotabank_bucket.delete_key(local_uri or "replays/{}.dem.bz2".format(replay.id))

            # Add a new download job
            Replay.add_dl_job(replay)

            # Note that we've done things to this replay.
            replays_removed.append(replay.id)

        return jsonify(
            success=True,
            replays_removed=replays_removed
        )

    @expose('/requeue_waiting_downloads')
    def requeue_waiting_downloads(self):
        waiting_downloads = Replay.query.filter(Replay.state == "WAITING_DOWNLOAD").all()

        done = []
        for replay in waiting_downloads:
            if Replay.add_dl_job(replay):
                done.append(replay.id)

        return jsonify(
            success=True,
            readded=done
        )

# Set up flask-admin
admin = Admin(name="Dotabank", index_view=AdminIndex())
admin.add_view(AtypicalReplays(name="Atypical Replays", category='Reports'))
admin.add_view(Logs(name="Logs", category="Reports"))
admin.add_view(Maintenance(name="Maintenance"))


@mod.before_app_request
def before_request():
    """ If logged in user is an admin, add the flask-admin object to the global scope. """
    if current_user.is_admin():
        g.admin = admin  # Only utilized under is_admin condition


# TODO: Toolbar stuffs
# - DebugToolbar kinda things; cpu time, sql queries, cache speed (though we don't cache anything yet)
