from app import db
from flask.ext.login import current_user


# noinspection PyShadowingBuiltins
class Replay(db.Model):
    # TODO: date_added for ordering by date added to site (latest repalys on index)
    __tablename__ = "replays"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    local_uri = db.Column(db.String(128))
    state = db.Column(db.Enum(
        "WAITING_GC",
        "WAITING_DOWNLOAD",
        "DOWNLOAD_IN_PROGRESS",
        "WAITING_PARSE",
        "PARSE_IN_PROGRESS",
        "PARSED",
        "GC_ERROR",
        "PARSE_ERROR"
    ), default="WAITING_GC")
    replay_state = db.Column(db.Enum(
        "REPLAY_AVAILABLE",
        "REPLAY_NOT_RECORDED",
        "REPLAY_EXPIRED",
        "UNKNOWN"
    ), default="UNKNOWN")
    gc_fails = db.Column(db.Integer, default=0)

    ratings = db.relationship('ReplayRating', backref='replay', lazy='joined', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='replay', lazy='joined', cascade="all, delete-orphan")
    combatlog = db.relationship('CombatLogMessage', order_by="asc(CombatLogMessage.timestamp)", backref='replay', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, _id=None, url="", replay_state="UNKNOWN", state="WAITING_GC"):
        self.id = _id
        self.url = url
        self.replay_state = replay_state
        self.state = state

    def __repr__(self):
        return "<Replay {}>".format(self.id)

    def user_rating(self):
        if current_user.is_authenticated():
            return next((rating for rating in self.ratings if rating.user_id == current_user.id), None)
        else:
            return None

    def user_favourite(self):
        if current_user.is_authenticated():
            return next((favourite for favourite in self.favourites if favourite.user_id == current_user.id), False)
        else:
            return False


# noinspection PyShadowingBuiltins
class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    positive = db.Column(db.Boolean, default=False, nullable=False)

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

    def __init__(self, replay_id=None, user_id=None):
        self.replay_id = replay_id
        self.user_id = user_id

    def __repr__(self):
        return "<Favourite {}/{}>".format(self.replay_id, self.user_id)


class CombatLogMessage(db.Model):
    __tablename__ = "combatlog_msgs"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)

    timestamp = db.Column(db.Float, nullable=False)
    tick = db.Column(db.Integer, nullable=False)

    type = db.Column(db.String(16), nullable=False)
    source_name = db.Column(db.String(80), nullable=False)
    target_name = db.Column(db.String(80), nullable=False)
    attacker_name = db.Column(db.String(80), nullable=False)
    inflictor_name = db.Column(db.String(80), nullable=False)
    attacker_illusion = db.Column(db.Boolean, nullable=False)
    target_illusion = db.Column(db.Boolean, nullable=False)
    target_source_name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Integer)
    health = db.Column(db.Integer)

    def __init__(self, replay_id, timestamp, tick, type, source_name, target_name, attacker_name, inflictor_name, attacker_illusion, target_illusion, value, health, target_source_name):
        self.replay_id = replay_id
        self.timestamp = timestamp
        self.tick = tick
        self.type = type
        self.source_name = source_name
        self.target_name = target_name
        self.attacker_name = attacker_name
        self.inflictor_name = inflictor_name
        self.attacker_illusion = attacker_illusion
        self.target_illusion = target_illusion
        self.target_source_name = target_source_name
        self.value = value
        self.health = health


class ReplayPlayer(db.Model):
    __tablename__ = "replay_players"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)

    # name = Column(String()) # Player name, we don't need to store this.
    steam_id = db.Column(db.BigInteger)
    team = db.Column(db.Enum("radiant", "dire", "spectator"))

    player_snapshots = db.relationship('PlayerSnapshot', backref='player', lazy='joined', cascade="all, delete-orphan")

    def __init__(self, replay_id, steam_id, team):
        self.replay_id = replay_id
        self.steam_id = steam_id
        self.team = team


class PlayerSnapshot(db.Model):
    __tablename__ = "replay_player_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("replay_players.id", ondelete="CASCADE"), nullable=False)

    index = db.Column(db.Integer)
    tick = db.Column(db.Integer)

    kills = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    streak = db.Column(db.Integer)

    last_hits = db.Column(db.Integer)
    denies = db.Column(db.Integer)
    earned_gold = db.Column(db.Integer)
    reliable_gold = db.Column(db.Integer)
    unreliable_gold = db.Column(db.Integer)
    total_gold = db.Column(db.Integer)

    has_buyback = db.Column(db.Boolean)
    last_buyback_time = db.Column(db.Integer)
    buyback_cooldown_time = db.Column(db.Float)

    # BaseNPC
    # abilities  # Do we care?
    level = db.Column(db.Integer)
    life_state = db.Column(db.Enum(
        "alive",
        "dying"
        "dead",
        "respawnable",
        "discardbody"
    ))
    is_alive = db.Column(db.Boolean)
    health = db.Column(db.Integer)
    health_regen = db.Column(db.Float)
    max_health = db.Column(db.Integer)

    mana = db.Column(db.Float)
    mana_regen = db.Column(db.Float)
    max_mana = db.Column(db.Float)

    position_x = db.Column(db.Float)
    position_y = db.Column(db.Float)

    # Hero
    hero_name = db.Column(db.String(42))

    natural_agility = db.Column(db.Float)
    natural_intelligence = db.Column(db.Float)
    natural_strength = db.Column(db.Float)

    agility = db.Column(db.Float)
    intelligence = db.Column(db.Float)
    strength = db.Column(db.Float)

    ability_points = db.Column(db.Integer)

    recent_damage = db.Column(db.Integer)
    replicating_hero = db.Column(db.Boolean)
    respawn_time = db.Column(db.Float)
    spawned_at = db.Column(db.Float)
    xp = db.Column(db.Integer)

    def __init__(self,
                 player_id,
                 tick,
                 index,
                 kills,
                 deaths,
                 assists,
                 streak,
                 last_hits,
                 denies,
                 earned_gold,
                 reliable_gold,
                 unreliable_gold,
                 total_gold,
                 has_buyback,
                 last_buyback_time,
                 buyback_cooldown_time,
                 level=None,
                 life_state=None,
                 is_alive=None,
                 health=None,
                 health_regen=None,
                 max_health=None,
                 mana=None,
                 mana_regen=None,
                 max_mana=None,
                 position_x=None,
                 position_y=None,
                 hero_name=None,
                 natural_agility=None,
                 natural_intelligence=None,
                 natural_strength=None,
                 agility=None,
                 intelligence=None,
                 strength=None,
                 ability_points=None,
                 recent_damage=None,
                 replicating_hero=None,
                 respawn_time=None,
                 spawned_at=None,
                 xp=None
                 ):
        self.player_id = player_id
        self.tick = tick
        self.index = index
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
        self.streak = streak
        self.last_hits = last_hits
        self.denies = denies
        self.earned_gold = earned_gold
        self.reliable_gold = reliable_gold
        self.unreliable_gold = unreliable_gold
        self.total_gold = total_gold
        self.has_buyback = has_buyback
        self.last_buyback_time = last_buyback_time
        self.buyback_cooldown_time = buyback_cooldown_time
        self.level = level
        self.life_state = life_state
        self.is_alive = is_alive
        self.health = health
        self.health_regen = health_regen
        self.max_health = max_health
        self.mana = mana
        self.mana_regen = mana_regen
        self.max_mana = max_mana
        self.position_x = position_x
        self.position_y = position_y
        self.hero_name = hero_name
        self.natural_agility = natural_agility
        self.natural_intelligence = natural_intelligence
        self.natural_strength = natural_strength
        self.agility = agility
        self.intelligence = intelligence
        self.strength = strength
        self.ability_points = ability_points
        self.recent_damage = recent_damage
        self.replicating_hero = replicating_hero
        self.respawn_time = respawn_time
        self.spawned_at = spawned_at
        self.xp = xp
