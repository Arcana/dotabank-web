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

    _schema = fetch_schema()

    def __init__(self, _id=None, name=None, description=None, tournament_url=None, itemdef=None, fetch_images=True):
        self.id = _id
        self.name = name
        self.description = description
        self.tournament_url = tournament_url
        self.itemdef = itemdef

        if fetch_images:
            self.fetch_images()

    def fetch_images(self):
        if self.itemdef is None:
            return False

        try:
            item_data = League._schema[self.itemdef]
            self.image_url = item_data.icon
            self.image_url_large = item_data.image
            return True
        except KeyError:
            return False


    @property
    def icon(self):
        if self.image_url is None:
            if self.fetch_images() is False:
                return None

        return self.image_url

    @property
    def image(self):
        if self.image_url_large is None:
            if self.fetch_images() is False:
                return None

        return self.image_url_large

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
