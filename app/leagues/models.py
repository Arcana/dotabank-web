from app import app, steam, fs_cache, sentry, db
from app.dota.models import Schema
import sys
import datetime


class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)  # We'll set this from WebAPI data
    name = db.Column(db.String(80))
    description = db.Column(db.Text)
    tournament_url = db.Column(db.String(255))
    itemdef = db.Column(db.Integer)
    image_url = db.Column(db.String(255))
    image_url_large = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow)

    replays = db.relationship('Replay', backref=db.backref('league', lazy="joined"), lazy="dynamic")

    def __repr__(self):
        return "{} (league id: {})".format(self.name, self.id)

    def __init__(self, _id=None, name=None, description=None, tournament_url=None, itemdef=None, fetch_images=True):
        self.id = _id
        self.name = name
        self.description = description
        self.tournament_url = tournament_url
        self.itemdef = itemdef

        if fetch_images:
            self.image_url, self.image_url_large = League.fetch_images(self.itemdef)

    @property
    def icon(self):
        if self.image_url is None:
            self.image_url, self.image_url_large = League.fetch_images(self.itemdef)

        return self.image_url

    @property
    def image(self):
        if self.image_url_large is None:
            self.image_url, self.image_url_large = League.fetch_images(self.itemdef)

        return self.image_url_large

    @property
    def short_description(self):
        """ Trim down the league's description. """
        short_desc = self.description
        if len(short_desc) > app.config['SHORT_DESCRIPTION_LENGTH']:
            short_desc = short_desc[:app.config['SHORT_DESCRIPTION_LENGTH']] + "..."
        return short_desc

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix="leagues")
    def fetch_leagues_from_webapi(cls):
        """ Fetch a list of leagues from the Dota 2 WebAPI.

        Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
        when interfacing with the WebAPI.

        Returns:
            An array of League objects.
        """
        try:
            res = steam.api.interface("IDOTA2Match_570").GetLeagueListing(language="en_US").get("result")

            # Filter out extra entries with the same league id.
            leagues_by_id = {}
            for _league in res.get("leagues"):
                leagues_by_id[int(_league.get("leagueid"))] = _league

            return leagues_by_id.values()

        except steam.api.HTTPError:
            sentry.captureMessage('League.get_all returned with HTTPError', exc_info=sys.exc_info)

            # Try to get data from existing cache entry
            data = fs_cache.cache.get('leagues', ignore_expiry=True)

            # Return data if we have any, else return an empty list
            return data or list()

    @classmethod
    def update_leagues_from_webapi(cls):
        """ Loops over leagues from WebAPI inserting new data where appropriate. """
        for webapi_league in cls.fetch_leagues_from_webapi():

            # Valve a great programmers and have a league with the ID 0.
            # Valve also return {... "leagueid": 0 ...} on all GetMatchDetail requests
            # The league with the ID 0 and all of the other replays are NOT related.
            # Fuck you Valve.
            if int(webapi_league.get("leagueid")) == 0:
                continue

            # Check if we have a hero entry
            _league = cls.query.filter(cls.id == webapi_league.get('leagueid')).first()

            # If we don't have a hero entry, make a new one
            if not _league:
                _league = cls(
                    webapi_league.get("leagueid"),
                    webapi_league.get("name"),
                    webapi_league.get("description"),
                    webapi_league.get("tournament_url"),
                    webapi_league.get("itemdef")
                )

                # Tell database we want to save it
                db.session.add(_league)

        # Commit all changes to database
        db.session.commit()

    @staticmethod
    def fetch_images(itemdef=None):
        # FIXME: Disabled while Dota 2's item schema WebAPI doesn't work, else every /league page load is horribly slow.
        return None, None

        try:
            item_data = Schema.get_by_id(itemdef)
            return item_data.icon, item_data.image
        except KeyError:
            return None, None


class LeagueView(db.Model):
    """ Saved filters for a league view - allowing league replays to be broken down into sub-views """
    __tablename__ = "league_views"

    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)

    name = db.Column(db.String(80), nullable=False)
    menu_order = db.Column(db.Integer, nullable=False, default=0, index=True)

    filters = db.relationship('LeagueViewFilter', backref='league_view', lazy='joined', cascade="all, delete-orphan")

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(menu_order)]
    }

    def __init__(self, league_id=None, name=None):
        self.league_id = league_id
        self.name = name

    def get_filters(self):
        """ Iterate through this object's LeagueViewFilter items and construct an SQLAlchemy filter list. """
        sqlalchemy_filters = []

        from app.replays.models import Replay

        # Iterate through the filters
        for _filter in self.filters:
            if _filter.value == "__true__":
                _filter.value = True
            elif _filter.value == "__false__":
                _filter.value = False
            elif _filter.value == "__none__":
                _filter.value = None

            if _filter.operator == "greater_than_equals":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute) >= _filter.value)
            elif _filter.operator == "greater_than":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute) > _filter.value)
            elif _filter.operator == "less_than_equals":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute) <= _filter.value)
            elif _filter.operator == "less_than":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute) < _filter.value)
            elif _filter.operator == "equals":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute) == _filter.value)
            elif _filter.operator == "not_equals":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute) != _filter.value)
            elif _filter.operator == "in":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute).in_(_filter.value.split(',')))
            elif _filter.operator == "not_in":
                sqlalchemy_filters.append(getattr(Replay, _filter.attribute).not_in_(_filter.value.split(',')))

        return sqlalchemy_filters


class LeagueViewFilter(db.Model):
    """ The filters to apply to a full list of leagues to whittle them down to what you're wanting. """

    id = db.Column(db.Integer, primary_key=True)
    league_view_id = db.Column(db.ForeignKey('league_views.id'), nullable=False)

    attribute = db.Column(db.String(32), nullable=False)
    operator = db.Column(db.Enum(
        'greater_than_equals',
        'greater_than',
        'less_than_equals',
        'less_than',
        'equals',
        'not_equals',
        'in',
        'not_in'
    ), nullable=False, default="equals")
    value = db.Column(db.String(64), nullable=False)

    def __init__(self, attribute=None, operator=None, value=None):
        self.attribute = attribute
        self.operator = operator

        if value is True:
            self.value = "__true__"
        elif value is False:
            self.value = "__false__"
        elif value is None:
            self.value = "__none__"
        else:
            self.value = value
