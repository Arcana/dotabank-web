from flask import current_app
from app import steam, cache
from app.filters import fetch_schema
from app.fs_fallback import fs_fallback

ITEM_SCHEMA = fetch_schema()  # TODO: Don't fetch at init-time.


class League():
    id = None
    name = None
    description = None
    tournament_url = None
    itemdef = None
    image_url = None
    image_url_large = None

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

    @classmethod
    @cache.cached(timeout=60 * 60, key_prefix="leagues")
    @fs_fallback
    def get_all(cls):
        """ Fetch a list of leagues from the Dota 2 WebAPI.

        Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
        when interfacing with the WebAPI.

        Returns:
            An array of League objects.
        """
        try:
            res = steam.api.interface("IDOTA2Match_570").GetLeagueListing(language="en_US").get("result")
            return list(
                cls(
                    _league.get("leagueid"),
                    _league.get("name"),
                    _league.get("description"),
                    _league.get("tournament_url"),
                    _league.get("itemdef")
                ) for _league in res.get("leagues"))

        except steam.api.HTTPError:
            current_app.logger.warning('League.get_all returned with HTTPError', exc_info=True)
            return list()

    @classmethod
    @cache.memoize(timeout=60 * 60)
    def get_by_id(cls, _id):
        """ Returns a league object for the given league id. """
        for league in cls.get_all():
            if league.id == _id:
                return league

        return None

    @staticmethod
    @cache.memoize(timeout=60 * 60)
    def fetch_images(itemdef=None):

        try:
            item_data = ITEM_SCHEMA[itemdef]
            return item_data.icon, item_data.image
        except KeyError:
            return None, None
