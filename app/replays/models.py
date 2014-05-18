from app import db, sqs_gc_queue, sqs_dl_queue
from flask.ext.login import current_user
import datetime
from boto.sqs.message import RawMessage as sqsMessage
from app import steam
from app.leagues.models import League


# noinspection PyShadowingBuiltins
class Replay(db.Model):
    __tablename__ = "replays"

    #################
    # Table columns #
    #################

    id = db.Column(db.Integer, primary_key=True)  # optional uint32 match_id = 6;
    local_uri = db.Column(db.String(128))
    state = db.Column(db.Enum(
        "WAITING_GC",
        "WAITING_DOWNLOAD",
        "DOWNLOAD_IN_PROGRESS",
        "ARCHIVED",
        "GC_ERROR",
        "DOWNLOAD_ERROR"
    ), default="WAITING_GC")
    gc_fails = db.Column(db.Integer, default=0)
    dl_fails = db.Column(db.Integer, default=0)

    # Timestamps for progress tracker
    added_to_site_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    gc_done_time = db.Column(db.DateTime)
    dl_done_time = db.Column(db.DateTime)

    # Match data
    replay_state = db.Column(db.Enum(
        "REPLAY_AVAILABLE",
        "REPLAY_NOT_RECORDED",
        "REPLAY_EXPIRED",
        "UNKNOWN"
    ), default="UNKNOWN")  # optional .CMsgDOTAMatch.ReplayState replay_state = 34 [default = REPLAY_AVAILABLE];
    replay_cluster = db.Column(db.Integer())  # optional uint32 cluster = 10;
    replay_salt = db.Column(db.Integer())  # optional fixed32 replay_salt = 13;

    game_mode = db.Column(db.SmallInteger())  # optional .DOTA_GameMode game_mode = 31 [default = DOTA_GAMEMODE_NONE];
    match_seq_num = db.Column(db.Integer())  # optional uint64 match_seq_num = 33;
    lobby_type = db.Column(db.SmallInteger())  # optional uint32 lobby_type = 16;
    league_id = db.Column(db.Integer())  # optional uint32 leagueid = 22;
    series_id = db.Column(db.Integer())  # optional uint32 series_id = 39;
    series_type = db.Column(db.Integer())  # optional uint32 series_type = 40;

    good_guys_win = db.Column(db.Boolean())  # optional bool good_guys_win = 2;
    duration = db.Column(db.Integer())  # optional uint32 duration = 3;
    start_time = db.Column(db.Integer())  # optional fixed32 startTime = 4;
    first_blood_time = db.Column(db.Integer())  # optional uint32 first_blood_time = 12;
    human_players = db.Column(db.Integer())  # optional uint32 human_players = 17;

    radiant_tower_status = db.Column(db.Integer())  # repeated uint32 tower_status = 8;
    dire_tower_status = db.Column(db.Integer())
    radiant_barracks_status = db.Column(db.Integer())  # repeated uint32 barracks_status = 9;
    dire_barracks_status = db.Column(db.Integer())

    radiant_team_id = db.Column(db.Integer())  # optional uint32 radiant_team_id = 20;
    radiant_team_name = db.Column(db.String(80))  # optional string radiant_team_name = 23;
    radiant_team_logo = db.Column(db.BigInteger())  # optional uint64 radiant_team_logo = 25;
    radiant_team_tag = db.Column(db.String(80))  # optional string radiant_team_tag = 37;
    radiant_team_complete = db.Column(db.Boolean())  # optional uint32 radiant_team_complete = 27;

    dire_team_id = db.Column(db.Integer())  # optional uint32 dire_team_id = 21;
    dire_team_name = db.Column(db.String(80))  # optional string dire_team_name = 24;
    dire_team_logo = db.Column(db.BigInteger())  # optional uint64 dire_team_logo = 26;
    dire_team_tag = db.Column(db.String(80))  # optional string dire_team_tag = 38;
    dire_team_complete = db.Column(db.Boolean())  # optional uint32 dire_team_complete = 28;

    radiant_guild_id = db.Column(db.Integer())  # optional uint32 radiant_guild_id = 35;
    dire_guild_id = db.Column(db.Integer())  # optional uint32 dire_guild_id = 36;

    # Not implementing
    # optional fixed32 server_ip = 14;  # Not exposed to client
    # optional uint32 server_port = 15;  # Not exposed to client
    # optional uint32 average_skill = 18;  # Not exposed to client
    # optional float game_balance = 19;  # Not exposed to client
    # optional uint32 positive_votes = 29;  # Variable, not worth serializing to DB.  Perhaps memcached with websockets GC reqs
    # optional uint32 negative_votes = 30;  # Variable, not worth serializing to DB.

    #################
    # Relationships #
    #################

    # GC relationships
    players = db.relationship('ReplayPlayer', backref="replay", lazy="dynamic", cascade="all, delete-orphan")  # repeated .CMsgDOTAMatch.Player players = 5;
    # repeated .CMatchHeroSelectEvent picks_bans = 32;  # TODO

    # Site relationships
    ratings = db.relationship('ReplayRating', backref='replay', lazy='joined', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='replay', lazy='joined', cascade="all, delete-orphan")
    downloads = db.relationship('ReplayDownload', backref="replay", lazy="dynamic", cascade="all, delete-orphan")

    ###############
    # Static data #
    ###############

    # Game mode data interpreted from the game's protobufs:
    # https://github.com/SteamRE/SteamKit/blob/master/Resources/Protobufs/dota/dota_gcmessages_common.proto#L407
    game_mode_strings = [
        "Invalid (0)",              # DOTA_GAMEMODE_NONE = 0;
        "All Pick",                 # DOTA_GAMEMODE_AP = 1;
        "Captain's Mode",           # DOTA_GAMEMODE_CM = 2;
        "Random Draft",             # DOTA_GAMEMODE_RD = 3;
        "Standard Draft",           # DOTA_GAMEMODE_SD = 4;
        "All Random",               # DOTA_GAMEM ODE_AR = 5;
        "Invalid (6)",              # DOTA_GAMEMODE_INTRO = 6;
        "Diretide",                 # DOTA_GAMEMODE_HW = 7;
        "Reverse Captains Mode",    # DOTA_GAMEMODE_REVERSE_CM = 8;
        "The Greeviling",           # DOTA_GAMEMODE_XMAS = 9;
        "Tutorial",                 # DOTA_GAMEMODE_TUTORIAL = 10;
        "Mid Only",                 # DOTA_GAMEMODE_MO = 11;
        "Least Played",             # DOTA_GAMEMODE_LP = 12;
        "Limited Heroes",           # DOTA_GAMEMODE_POOL1 = 13;
        "Compendium",               # DOTA_GAMEMODE_FH = 14;
        "Invalid (15)",             # DOTA_GAMEMODE_CUSTOM = 15;
        "Captains Draft",           # DOTA_GAMEMODE_CD = 16;
        "Balanced Draft",           # DOTA_GAMEMODE_BD = 17;
        "Ability Draft",            # DOTA_GAMEMODE_ABILITY_DRAFT = 18;
        "Invalid (19)"              # DOTA_GAMEMODE_EVENT = 19;
    ]

    # Lobby data interpreted from the game's protobufs:
    # https://github.com/SteamRE/SteamKit/blob/master/Resources/Protobufs/dota/dota_gcmessages_common.proto#L803
    lobby_type_strings = [
        "Public Matchmaking",
         "Practice Game",
         "Tournament Game",
         "Tutorial",
         "Co-op Bot",
         "Team Matchmaking",
         "Solo Matchmaking",
         "Ranked Match"
    ]

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.desc(added_to_site_time)]
    }

    def __init__(self, id=None, replay_state="UNKNOWN", state="WAITING_GC", skip_webapi=False):
        self.id = id
        self.replay_state = replay_state
        self.state = state

        if not skip_webapi:
            self._populate_from_webapi()

    def __repr__(self):
        return "<Replay {}>".format(self.id)

    def _populate_from_webapi(self, match_data=None):
        """ Populates a new replay object with data from WebAPI.
        """
        try:
            if not match_data:
                match_data = steam.api.interface("IDOTA2Match_570").GetMatchDetails(match_id=self.id).get("result")

            if match_data:
                self.good_guys_win = match_data.get('radiant_win')
                self.duration = match_data.get('duration')
                self.start_time = match_data.get('start_time')
                self.match_seq_num = match_data.get('match_seq_num')
                self.radiant_tower_status = match_data.get('tower_status_radiant')
                self.dire_tower_status = match_data.get('tower_status_dire')
                self.radiant_barracks_status = match_data.get('barracks_status_radiant')
                self.dire_barracks_status = match_data.get('barracks_status_dire')
                self.replay_cluster = match_data.get('cluster')
                self.first_blood_time = match_data.get('first_blood_time')
                self.lobby_type = match_data.get('lobby_type')
                self.human_players = match_data.get('human_players')
                self.league_id = match_data.get('leagueid')
                self.game_mode = match_data.get('game_mode')
        except steam.api.HTTPError:
            pass

    @property
    def url(self):
        return "http://replay{}.valve.net/570/{}_{}.dem.bz2".format(
            self.replay_cluster,
            self.id,
            self.replay_salt
        )

    @property
    def lobby_type_string(self):
        """ Returns a human-friendly string for the replay's lobby type. """
        try:
            return Replay.lobby_type_strings[self.lobby_type]
        except (IndexError, TypeError):
            return "Invalid ({})".format(self.lobby_type)

    @property
    def game_mode_string(self):
        """ Returns a human-friendly string for the replay's game mode. """
        try:
            return Replay.game_mode_strings[self.game_mode]
        except IndexError:
            return "Invalid ({})".format(self.game_mode)

    @property
    def team_players(self):
        """ Returns a tuple (radiant, dire) after splitting the replays players into teams. """
        # Sort players by their in-game slot
        players = sorted(self.players, key=lambda x: x.player_slot)

        # Split players into teams
        radiant = [p for p in players if p.team == "Radiant"]  # 8th bit false
        dire = [p for p in players if p.team == "Dire"]  # 8th bit true

        return radiant, dire

    @property
    def league(self):
        if self.league_id:
            return League.get_by_id(self.league_id)
        return None

    # TODO: What is this?
    def user_rating(self):
        if current_user.is_authenticated():
            return next((rating for rating in self.ratings if rating.user_id == current_user.id), None)
        else:
            return None

    # TODO: What is this?
    def user_favourite(self):
        if current_user.is_authenticated():
            return next((favourite for favourite in self.favourites if favourite.user_id == current_user.id), False)
        else:
            return False

    @classmethod
    def get_or_create(cls, **kwargs):
        # Get instance, filter skip_webapi from kwargs as that's the only non-database argument __init__ can take.
        instance = cls.query.filter_by(**{k: v for k,v in kwargs.iteritems() if k is not "skip_webapi"}).first()
        if instance:
            return instance, False
        else:
            instance = cls(**kwargs)
            return instance, True

    @staticmethod
    def add_gc_job(_replay):
        # Reset gc fails
        _replay.gc_fails = 0
        db.session.add(_replay)
        db.session.commit()

        # Write to SQS
        msg = sqsMessage()
        msg.set_body(str(_replay.id))
        return sqs_gc_queue.write(msg)

    @staticmethod
    def add_dl_job(_replay):
        # Reset dl fails
        _replay.dl_fails = 0
        db.session.add(_replay)
        db.session.commit()

        # Write to SQS
        msg = sqsMessage()
        msg.set_body(str(_replay.id))
        return sqs_dl_queue.write(msg)


# noinspection PyShadowingBuiltins
class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    positive = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, replay_id=None, user_id=None, positive=None):
        self.replay_id = replay_id
        self.user_id = user_id
        self.positive = positive

    def __repr__(self):
        return "<Rating {}/{}>".format(self.replay_id, self.user_id)


# noinspection PyShadowingBuiltins
class ReplayFavourite(db.Model):
    __tablename__ = "replay_favs"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, replay_id=None, user_id=None):
        self.replay_id = replay_id
        self.user_id = user_id

    def __repr__(self):
        return "<Favourite {}/{}>".format(self.replay_id, self.user_id)


# noinspection PyShadowingBuiltins
class ReplayDownload(db.Model):
    __tablename__ = "replay_downloads"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, replay_id=None, user_id=None):
        self.replay_id = replay_id
        self.user_id = user_id

    def __repr__(self):
        return "<Download {}/{}>".format(self.replay_id, self.user_id)


class ReplayPlayer(db.Model):
    __tablename__ = "replay_players"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)

    # GC data
    account_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # optional uint32 account_id = 1;
    player_slot = db.Column(db.Integer)  # optional uint32 player_slot = 2;
    hero_id = db.Column(db.Integer)  # optional uint32 hero_id = 3;
    item_0 = db.Column(db.Integer)  # optional uint32 item_0 = 4;
    item_1 = db.Column(db.Integer)  # optional uint32 item_1 = 5;
    item_2 = db.Column(db.Integer)  # optional uint32 item_2 = 6;
    item_3 = db.Column(db.Integer)  # optional uint32 item_3 = 7;
    item_4 = db.Column(db.Integer)  # optional uint32 item_4 = 8;
    item_5 = db.Column(db.Integer)  # optional uint32 item_5 = 9;
    kills = db.Column(db.Integer)  # optional uint32 kills = 14;
    deaths = db.Column(db.Integer)  # optional uint32 deaths = 15;
    assists = db.Column(db.Integer)  # optional uint32 assists = 16;
    leaver_status = db.Column(db.SmallInteger)  # optional uint32 leaver_status = 17;
    gold = db.Column(db.Integer)  # optional uint32 gold = 18;
    last_hits = db.Column(db.Integer)  # optional uint32 last_hits = 19;
    denies = db.Column(db.Integer)  # optional uint32 denies = 20;
    gold_per_min = db.Column(db.Integer)  # optional uint32 gold_per_min = 21;
    xp_per_min = db.Column(db.Integer)  # optional uint32 XP_per_min = 22;
    gold_spent = db.Column(db.Integer)  # optional uint32 gold_spent = 23;
    hero_damage = db.Column(db.Integer)  # optional uint32 hero_damage = 24;
    tower_damage = db.Column(db.Integer)  # optional uint32 tower_damage = 25;
    hero_healing = db.Column(db.Integer)  # optional uint32 hero_healing = 26;
    level = db.Column(db.SmallInteger)  # optional uint32 level = 27;

    # Not exposed to client (as far as I can tell)
    # optional float expected_team_contribution = 10;
    # optional float scaled_metric = 11;
    # optional uint32 previous_rank = 12;
    # optional uint32 rank_change = 13;
    # optional uint32 time_last_seen = 28;
    # optional string player_name = 29;
    # optional uint32 support_ability_value = 30;
    # optional bool feeding_detected = 32;
    # optional uint32 search_rank = 34;
    # optional uint32 search_rank_uncertainty = 35;
    # optional int32 rank_uncertainty_change = 36;
    # optional uint32 hero_play_count = 37;
    # optional fixed64 party_id = 38;
    # optional float scaled_kills = 39;
    # optional float scaled_deaths = 40;
    # optional float scaled_assists = 41;
    # optional uint32 claimed_farm_gold = 42;
    # optional uint32 support_gold = 43;
    # optional uint32 claimed_denies = 44;
    # optional uint32 claimed_misses = 45;
    # optional uint32 misses = 46;

    # TODO: Add models for these objects
    # repeated .CMatchPlayerAbilityUpgrade ability_upgrades = 47;
    # repeated .CMatchAdditionalUnitInventory additional_units_inventory = 48;

    def __init__(self, replay_id):
        self.replay_id = replay_id

    @property
    def team(self):
        if self.player_slot < 128:
            return "Radiant"
        else:
            return "Dire"

    @property
    def items(self):
        return [
            self.item_0,
            self.item_1,
            self.item_2,
            self.item_3,
            self.item_4,
            self.item_5
        ]

    def __repr__(self):
        return "<ReplayPlayer {}>".format(self.id)


class Search(db.Model):
    """ Track matchids users search for. """
    __tablename__ = "searches"

    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    success = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    replay = db.relationship('Replay', backref='search', lazy='joined', cascade="all")

    def __init__(self, user_id=None, search_query=None, ip_address=None, success=None, replay_id=None):
        self.search_query = search_query
        self.user_id = user_id
        self.ip_address = ip_address
        self.success = success
        self.replay_id = replay_id

    def __repr__(self):
        return "<Search {}/{}>".format(self.replay_id, self.user_id)

