from app import db, mem_cache
from app.replays.models import Replay, ReplayDownload
from calendar import monthrange
from datetime import datetime
from time import mktime

class MonthlyCost(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    month = db.Column(db.Date)
    cost = db.Column(db.Integer())  # USD Cents

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(month)]
    }

    @mem_cache.memoize()
    def replay_count(self, state_filter=None):
        """ The amount of replays processed in this month.
        :param state_filter: Pass a state to only count replays with this state
        :return: Count of replays (integer)
        """
        # Last day of the given month
        end_day = monthrange(self.month.year, self.month.month)[1]

        start_timestamp = mktime(datetime(
            year=self.month.year, month=self.month.month, day=1,
            hour=0, minute=0, second=0).timetuple())
        end_timestamp = mktime(datetime(
            year=self.month.year, month=self.month.month, day=end_day,
            hour=23, minute=59, second=59).timetuple())

        # Construct filters to only query replays in the given month
        filters = [
            Replay.start_time >= start_timestamp,  # Start of month
            Replay.start_time <= end_timestamp  # End of month
        ]

        # If any state filtering was provided, let's also filter with that
        if state_filter is not None:
            filters.append(
                Replay.state == state_filter
            )

        # Count replays matching filters
        return Replay.query.filter(
            *filters
        ).count()

    @mem_cache.memoize()
    def cost_per_replay(self, state_filter=None):
        """ The cost for this month broken down per replays procesed
        :param state_filter: Pass a state to only count replays with this state
        :return: Cost per replay in cents (float)
        """
        return float(self.cost) / (float(self.replay_count(state_filter)) or 1)

    @mem_cache.memoize()
    def download_count(self):
        """ The amount of replays downloads in this month.
        :return: Count of replay downloads (integer)
        """
        # Last day of the given month
        end_day = monthrange(self.month.year, self.month.month)[1]

        # Construct filters to only query replays in the given month
        filters = [
            ReplayDownload.created_at >= datetime(
                year=self.month.year, month=self.month.month, day=1,
                hour=0, minute=0, second=0),  # Start of month
            ReplayDownload.created_at <= datetime(
                year=self.month.year, month=self.month.month, day=end_day,
                hour=23, minute=59, second=59)  # End of month
        ]

        # Count replays matching filters
        return ReplayDownload.query.filter(
            *filters
        ).count()

    @mem_cache.memoize()
    def cost_per_download(self):
        """ The cost for this month broken down per download
        :return: Cost of replay download in cents (float)
        """
        return float(self.cost) / (float(self.download_count()) or 1)