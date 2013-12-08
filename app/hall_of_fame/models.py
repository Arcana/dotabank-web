from app import db


# noinspection PyShadowingBuiltins
class HallOfFame(db.Model):
    __tablename__ = "hall_of_fame"
    week = db.Column(db.Integer, primary_key=True)

    players = db.relationship('FeaturedPlayer', backref="hall_of_fame", lazy="join", cascade="all, delete-orphan")
    farmers = db.relationship('FeaturedFarmer', backref="hall_of_fame", lazy="join", cascade="all, delete-orphan")

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(week)]
    }

    def __init__(self, week=None):
        self.week = week

    @property
    def farmer(self):
        return self.farmers[0]

    @property
    def adjusted_week(self):
        return self.week - 2232  # Weeks begin at 2233, so take 2231 to make the first = 1.

    def __repr__(self):
        return "<HallOfFame {}>".format(self.week)


# noinspection PyShadowingBuiltins
class FeaturedPlayer(db.Model):
    __tablename__ = "hall_of_fame_players"

    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, db.ForeignKey("hall_of_fame.week", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    average_scaled_metric = db.Column(db.Float, default=False, nullable=False)
    hero_id = db.Column(db.Integer, default=False, nullable=False)
    num_games = db.Column(db.Integer, default=False, nullable=False)

    def __init__(self, week=None, user_id=None, average_scaled_metric=None, hero_id=None, num_games=None):
        self.week = week
        self.user_id = user_id

        self.average_scaled_metric = average_scaled_metric
        self.hero_id = hero_id
        self.num_games = num_games

    @property
    def account_id(self):
        return int(self.user_id)

    def __repr__(self):
        return "<FeaturedPlayer {} (wk: {})>".format(self.user_id, self.week)


# noinspection PyShadowingBuiltins
class FeaturedFarmer(db.Model):
    __tablename__ = "hall_of_fame_farmers"

    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, db.ForeignKey("hall_of_fame.week", ondelete="CASCADE"), nullable=False)
    replay_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)

    hero_id = db.Column(db.Integer, default=False, nullable=False)
    gold_per_min = db.Column(db.Integer, default=False, nullable=False)

    def __init__(self, week=None, user_id=None, replay_id=None, hero_id=None, gold_per_min=None):
        self.week = week
        self.user_id = user_id

        self.replay_id = replay_id
        self.hero_id = hero_id
        self.gold_per_min = gold_per_min

    @property
    def account_id(self):
        return int(self.user_id)

    def __repr__(self):
        return "<FeaturedFarmer {} (wk: {})>".format(self.user_id, self.week)
