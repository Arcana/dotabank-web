from app import steam, fs_cache, sentry
from flask import current_app, url_for
import requests
import json
import sys

HERO_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/npc/npc_heroes.json"
ITEM_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/npc/items.json"
REGION_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/regions.json"
SCHEMA_DATA_URL = "https://raw.githubusercontent.com/dotabuff/d2vpk/master/json/dota_pak01/scripts/items/items_game.json"


class Hero:
    """ Represents a Dota 2 hero. """

    id = None
    token = None

    _heroes = None
    _CACHE_KEY = "heroes"  # Key for fscache of this file

    def __init__(self, _id, **kwargs):
        self.id = _id

        # Populate all other parms via kwargs - consider them optional
        for key, arg in kwargs.items():
            self.__dict__[key] = arg

    def __repr__(self):
        return self.localized_name

    @property
    def localized_name(self):  # TODO
        return self.token

    @property
    def image(self):
        return url_for('hero_image', hero_name=self.token.replace('npc_dota_hero_', ''))

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
                print(key)

                # Skip these keys - they're not hero definitions
                if key in ["Version", "npc_dota_hero_base"]:
                    continue

                output_heroes.append(
                    cls(
                        _id=int(hero.get('HeroID')),
                        token=key
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
    def get_by_name(cls, name):
        """ Returns a Hero object for the given hero name. """
        for hero in cls.get_all():
            if hero.token == name:
                return hero

        return None


class Item:
    """ Represents a Dota 2 item """

    id = None
    name = None
    localized_name = None
    image_filename = None
    quality = None
    cost = None
    description = None
    notes = None
    attribute_html = None
    manacost = None
    cooldown = None
    lore = None
    _components = None  # List of component names
    created = None      # Whether or not this item is built from components

    _items = None

    def __init__(
            self,
            _id,
            name,
            localized_name,
            image_filename,
            quality,
            cost,
            description,
            notes,
            attribute_html,
            manacost,
            cooldown,
            lore,
            components,
            created
    ):
        self.id = _id
        self.name = name
        self.localized_name = localized_name
        self.image_filename = image_filename
        self.quality = quality
        self.cost = cost
        self.description = description
        self.notes = notes
        self.attribute_html = attribute_html
        self.manacost = manacost
        self.cooldown = cooldown
        self.lore = lore
        self._components = components
        self.created = created

    @property
    def icon(self):
        return url_for('item_icon', item_filename=self.image_filename)

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix="items")
    def fetch_items(cls):
        """ Fetch a list of items from a non-public JSON feed.

        Falls back to data stored on the file-system in case of any problems fetching the data.

        Returns:
            A dict containing data on Dota 2 items, mapped by their item IDs.
            An empty dict if there was any errors fetching the data and we did not have a file-system fallback.
        """
        try:
            request = requests.get("http://www.dota2.com/jsfeed/itemdata")

            if request.status_code == requests.codes.ok:
                try:
                    data = request.json()["itemdata"]
                    return list(
                        cls(
                            v.get('id'),
                            k,
                            v.get('dname'),
                            v.get('img'),
                            v.get('qual'),
                            v.get('cost'),
                            v.get('desc'),
                            v.get('notes'),
                            v.get('attrib'),
                            v.get('mc'),
                            v.get('cd'),
                            v.get('lore'),
                            v.get('components'),
                            v.get('created')
                        ) for k, v in data.iteritems()
                    )
                except (KeyError, ValueError) as e:
                    if current_app.debug:
                        raise e
                    current_app.logger.warning('Item.get_all threw exception', exc_info=True, extra={
                        'extra': json.dumps({
                            'url': request.url,
                            'text': request.text,
                            'status_code': request.status_code,
                        })
                    })

            else:
                current_app.logger.warning('Item.get_all returned with non-OK status', extra={
                    'extra': json.dumps({
                        'url': request.url,
                        'text': request.text,
                        'status_code': request.status_code,
                    })
                })

        except requests.exceptions.RequestException:
            sentry.captureMessage('Item.get_all returned with RequestException', exc_info=sys.exc_info)

            # Try to get data from existing cache entry
            data = fs_cache.cache.get('items', ignore_expiry=True)

            # Return data if we have any, else return an empty list
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
    def get_by_name(cls, name):
        """ Returns an Item object for the given item name. """
        for item in cls.get_all():
            if item.name == name:
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
    def localized_name(self):   # TODO
        return self.display_name_token

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
                        display_name_token=region.get('display_name'),
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
