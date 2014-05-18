from app import steam, fs_cache, db
from flask import current_app
import requests
import json


class Hero:
    """ Represents a Dota 2 hero. """

    id = None
    name = None
    localized_name = None

    _heroes = None

    def __init__(self, _id, name, localized_name=None):
        self.id = _id
        self.name = name
        self.localized_name = localized_name

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix="heroes")
    def fetch_heroes(cls):
        """ Fetch a list of heroes from the Dota 2 WebAPI.

        Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
        when interfacing with the WebAPI.

        Returns:
            An array of Hero objects.
        """
        try:
            res = steam.api.interface("IEconDOTA2_570").GetHeroes(language="en_US").get("result")
            return list(
                cls(
                    hero.get("id"),
                    hero.get("name"),
                    hero.get("localized_name")
                ) for hero in res.get("heroes"))

        except steam.api.HTTPError:
            current_app.logger.warning('Hero.get_all returned with HTTPError', exc_info=True)
            return list()

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
            if hero.name == name:
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
        return "http://media.steampowered.com/apps/dota2/images/items/{}".format(self.image_filename)

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
            current_app.logger.warning('Item.get_all returned with RequestException', exc_info=True)

        # This will only return on errors / exceptions
        return list()

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
            current_app.logger.warning('Schema.fetch_schema returned with HTTPError', exc_info=True)

        # This will only return on errors / exceptions
        return None

    @classmethod
    def get_schema(cls):
        if cls._schema is None:
            cls._schema = cls.fetch_schema()

        return cls._schema

    @classmethod
    def get_by_id(cls, _id):
        return cls.get_schema()[_id]
