from app import steam, cache
from app.filters import fetch_leagues, get_league_by_id, fetch_schema


class League():
    id = None
    name = None
    description = None
    tournament_url = None
    itemdef = None
    image_url = None
    image_url_large = None

    def __init__(self, _id=None, name=None, description=None, tournament_url=None, itemdef=None):
        self.id = _id
        self.name = name
        self.description = description
        self.tournament_url = tournament_url
        self.itemdef = itemdef

    @property
    def icon(self):
        if self.itemdef is None:
            return None

        schema = fetch_schema()
        try:
            item_data = schema[self.itemdef]
            return item_data.icon
        except KeyError:
            return None

    @property
    def image(self):
        if self.itemdef is None:
            return None

        schema = fetch_schema()
        try:
            item_data = schema[self.itemdef]
            return item_data.image
        except KeyError:
            return None

    @staticmethod
    def get_all():
        _leagues = fetch_leagues()
        return list(
            League(
                k,
                v.get("name"),
                v.get("description"),
                v.get("tournament_url"),
                v.get("itemdef")
            ) for k, v in _leagues.iteritems())

    @staticmethod
    def get_by_id(_id):
        data = get_league_by_id(_id)
        if data:
            return League(
                data["leagueid"],
                data["name"],
                data["description"],
                data["tournament_url"],
                data["itemdef"],
            )
        else:
            return None
