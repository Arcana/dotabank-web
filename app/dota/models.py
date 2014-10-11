from app import steam, fs_cache, sentry, db
from flask import current_app, url_for, g
import requests
import json
import sys

HERO_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/npc/npc_heroes.json"
ITEM_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/npc/items.json"
REGION_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/regions.json"
SCHEMA_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/items/items_game.json"
LOCALIZATION_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota/resource/dota_{}.json"


class Hero:
    """ Represents a Dota 2 hero. """

    id = None
    name = None
    token = None

    _heroes = None
    _CACHE_KEY = "heroes"  # Key for fscache of this file

    def __init__(self, _id, _token, **kwargs):
        self.id = _id
        self.token = _token
        self.name = _token.replace('npc_dota_hero_', '')

        # Populate all other parms via kwargs - consider them optional
        for key, arg in kwargs.items():
            self.__dict__[key] = arg

    def __repr__(self):
        return self.localized_name

    @property
    def localized_name(self):
        return g.localization.tokens.get(self.token) or self.token

    @property
    def image(self):
        return url_for('hero_image', hero_name=self.token.replace('npc_dota_hero_', ''))

    @property
    def replays(self):
        from app.replays.models import Replay, ReplayPlayer
        return Replay.query.filter(Replay.players.any(hero_id=self.id))

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix=_CACHE_KEY)
    def fetch_heroes(cls):
        """ Fetch a list of heroes via the game's npc_heroes.txt

        Fetches npc_heroes.txt as JSON via Dotabuff's d2vpk repository, and parses it for data.
        Falls back to data stored on the file-system in case of a HTTPError or KeyError.

        Only retrieves ID and token for now, but there's a ton more data available should we ever need it.

        Returns:
            An array of Hero objects.
        """
        try:
            req = requests.get(HERO_DATA_URL)

            # Raise HTTPError if we don't get HTTP OK
            if req.status_code != requests.codes.ok:
                raise requests.HTTPError("Response not HTTP OK")

            # Fetch relevant pieces of data from JSON data
            input_heroes = req.json()['DOTAHeroes']
            output_heroes = []

            # Iterate through heries, create an instance of this class for each.
            for key, hero in input_heroes.items():
                # Skip these keys - they're not hero definitions
                if key in ["Version", "npc_dota_hero_base"]:
                    continue

                output_heroes.append(
                    cls(
                        _id=int(hero.get('HeroID')),
                        _token=key
                    )
                )

            return output_heroes

        except (steam.api.HTTPError, KeyError):
            sentry.captureMessage('Hero.fetch_heroes failed', exc_info=sys.exc_info)

            # Try to get data from existing cache entry
            data = fs_cache.cache.get(cls._CACHE_KEY, ignore_expiry=True)

            # Return data if we have any, else return an empty list()
            return data or list()

    @classmethod
    def get_all(cls):
        if cls._heroes is None:
            cls._heroes = cls.fetch_heroes()

        return cls._heroes

    @classmethod
    def get_by_id(cls, _id):
        """ Returns a Hero object for the given hero id. """
        for hero in cls.get_all():
            if hero.id == _id:
                return hero

        return None

    @classmethod
    def get_by_token(cls, name):
        """ Returns a Hero object for the given hero token. """
        for hero in cls.get_all():
            if hero.token == name:
                return hero

        return None

    @classmethod
    def get_by_name(cls, name):
        """ Returns a Hero object for the given hero token. """
        for hero in cls.get_all():
            if hero.name == name:
                return hero

        return None


class Item:
    """ Represents a Dota 2 item """

    id = None
    token = None

    _items = None
    _CACHE_KEY = "items"

    def __init__(self, _id, token=None):
        self.id = _id
        self.token = token

    def __repr__(self):
        return self.localized_name

    @property
    def localized_name(self):
        return g.localization.tokens.get("DOTA_Tooltip_Ability_{}".format(self.token)) or self.token

    @property
    def icon(self):
        return url_for('item_icon', item_filename="{}_lg.png".format(self.token[5:]))

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix=_CACHE_KEY)
    def fetch_items(cls):
        """ Fetch a list of items via the game's npc_items.txt

        Fetches npc_items.txt as JSON via Dotabuff's d2vpk repository, and parses it for data.
        Falls back to data stored on the file-system in case of a HTTPError or KeyError.

        Only retrieves ID and token for now, but there's a ton more data available should we ever need it.

        Returns:
            An array of Item objects.
        """
        try:
            req = requests.get(ITEM_DATA_URL)

            # Raise HTTPError if we don't get HTTP OK
            if req.status_code != requests.codes.ok:
                raise requests.HTTPError("Response not HTTP OK")

            # Fetch relevant pieces of data from JSON data
            input_items = req.json()['DOTAAbilities']
            output_items = []

            # Iterate through heries, create an instance of this class for each.
            for key, item in input_items.items():
                # Skip these keys - they're not item definitions
                if key in ["Version"]:
                    continue

                output_items.append(
                    cls(
                        _id=int(item.get('ID')),
                        token=key
                    )
                )

            return output_items

        except (steam.api.HTTPError, KeyError):
            sentry.captureMessage('Item.fetch_items failed', exc_info=sys.exc_info)

            # Try to get data from existing cache entry
            data = fs_cache.cache.get(cls._CACHE_KEY, ignore_expiry=True)

            # Return data if we have any, else return an empty list()
            return data or list()

    @classmethod
    def get_all(cls):
        if cls._items is None:
            cls._items = cls.fetch_items()

        return cls._items

    @classmethod
    def get_by_id(cls, _id):
        """ Returns an Item object for the given item id. """
        for item in cls.get_all():
            if item.id == _id:
                return item

        return None

    @classmethod
    def get_by_token(cls, token):
        """ Returns an Item object for the given item name. """
        for item in cls.get_all():
            if item.token == token:
                return item

        return None


class Schema():
    """ Schema wrapper with added caching """

    _schema = None

    @staticmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix="schema")
    def fetch_schema():
        """ Fetches the Dota 2 item schema

        Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
        when interfacing with the WebAPI.

        Returns:
            A steam.items.schema object.
            None if there was a HTTPError fetching the data and we did not have a file-system fallback.
        """
        try:
            schema = steam.items.schema(570)
            schema.client_url  # Touch things so steamdeeb caching actually loads data
            return schema

        except steam.api.HTTPError:
            sentry.captureMessage('Schema.fetch_schema returned with HTTPError', exc_info=sys.exc_info)

            # Try to get data from existing cache entry
            data = fs_cache.cache.get('schema', ignore_expiry=True)

            # Return data if we have any, else return None
            return data or None

    @classmethod
    def get_schema(cls):
        if cls._schema is None:
            cls._schema = cls.fetch_schema()

        return cls._schema

    @classmethod
    def get_by_id(cls, _id):
        return cls.get_schema()[_id]


class Region():

    # Properties
    id = None
    matchgroup = None
    latitude = None
    longitude = None
    display_name_token = None
    proxy_allow = None
    division = None
    alert_at_capacity = None
    ip_range = None
    ip_relay_peers = None
    clusters = None

    _regions = None  # List of all regions
    _CACHE_KEY = "region"  # Key for fscache of this file

    @property
    def localized_name(self):
        return g.localization.tokens.get(self.display_name_token) or self.display_name_token

    def __init__(self, _id, **kwargs):
        self.id = _id

        # Populate all other parms via kwargs - consider them optional
        for key, arg in kwargs.items():
            self.__dict__[key] = arg

    def __repr__(self):
        return self.localized_name

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix=_CACHE_KEY)
    def fetch_regions(cls):
        """ Fetch a list of regions via the game's regions.txt

        Fetches regions.txt as JSON via Dotabuff's d2vpk repository, and parses it for data.
        Falls back to data stored on the file-system in case of a HTTPError.

        Returns:
            An array of Hero objects.
        """
        try:
            req = requests.get(REGION_DATA_URL)

            # Raise HTTPError if we dont' get HTTP OK
            if req.status_code != requests.codes.ok:
                raise requests.HTTPError("Response not HTTP OK")

            # Fetch relevant pieces of data from JSON data
            input_regions = req.json()['regions']
            output_regions = []

            # Iterate through regions, create an instance of this class for each.
            for key, region in input_regions.items():
                # Skip unspecified - we don't need it
                if key == "unspecified":
                    continue

                output_regions.append(
                    cls(
                        _id=int(region.get('region')),
                        matchgroup=int(region.get('matchgroup')) if region.get('matchgroup') else None,
                        latitude=float(region.get('latitude')) if region.get('latitude') else None,
                        longitude=float(region.get('longitude')) if region.get('longitude') else None,
                        display_name_token=region.get('display_name')[1:] if region.get('display_name')[0] == '#' else region.get('display_name'),
                        proxy_allow=region.get('proxy_allow'),
                        division=region.get('division'),
                        alert_at_capacity=bool(region.get('alert_at_capacity', True)),
                        ip_range=region.get('ip_range', []),
                        ip_relay_peers=region.get('ip_relay_peers', []),
                        clusters=map(int, region.get('clusters', []))
                    )
                )

            return output_regions

        except (requests.HTTPError, KeyError):
            sentry.captureMessage('Region.fetch_regions failed', exc_info=sys.exc_info)

            # Try to get data from existing cache entry
            data = fs_cache.cache.get(cls._CACHE_KEY, ignore_expiry=True)

            # Return data if we have any, else return an empty list()
            return data or list()

    @classmethod
    def get_all(cls):
        if cls._regions is None:
            cls._regions = cls.fetch_regions()

        return cls._regions

    @classmethod
    def get_by_id(cls, _id):
        """ Returns a Region object for the given region id. """
        for item in cls.get_all():
            if item.id == _id:
                return item

        return None

    @classmethod
    def get_by_cluster(cls, cluster_id):
        """ Returns a Region object for the given cluster id. """
        for item in cls.get_all():
            if cluster_id in item.clusters:
                return item

        return None


class Localization():
    # TODO: Figure out a better way to do this.  This feels wrong.

    language = None
    tokens = None

    _language_tokens = {}

    DEFAULT_LANGUAGE = "english"

    def __init__(self, language=None, tokens=None):
        self.language = language or self.DEFAULT_LANGUAGE
        self.tokens = tokens or self.get_tokens(self.language)

    def __repr__(self):
        return "<Localization {}>".format(self.language)

    @classmethod
    @fs_cache.memoize(timeout=60 * 60)
    def fetch_tokens(cls, language):
        """ Fetch a localization file from the game's files.

        Fetches dota_LANGUAGE.txt as JSON via Dotabuff's d2vpk repository, and parses it for data.

        Returns:
            An Localization object
        """
        try:
            req = requests.get(LOCALIZATION_DATA_URL.format(language))

            # Raise HTTPError if we don't get HTTP OK
            if req.status_code != requests.codes.ok:
                raise requests.HTTPError("Response not HTTP OK")

            # Fetch relevant pieces of data from JSON data
            input_data = req.json()['lang']

            return input_data.get('Tokens')

        except (requests.HTTPError, KeyError):
            sentry.captureMessage('Localization.fetch_tokens failed', exc_info=sys.exc_info)
            return []

    @classmethod
    def get_tokens(cls, language):
        if language not in cls._language_tokens.keys():
            cls._language_tokens[language] = cls.fetch_tokens(language)

        return cls._language_tokens.get(language)
