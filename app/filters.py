from app import cache, steam
from flask import current_app
import json
import requests
from datetime import datetime, timedelta
from app.fs_fallback import fs_fallback


# General filters
def escape_every_character(text):
    """ Returns the string provided encoded as html-entities.

    Sets up a generator iterating through `text`, formatting the ordinal of each character as a HTML entity.
    This generator is then passed to the str.join function to construct a new string of these encoded entities.

    Args:
        text: A string to be encoded.
    Returns:
        A string of html-entities representing the given `text`.
    """
    return "".join("&#{};".format(ord(x)) for x in text)


def timestamp_to_datestring(timestamp, _format=None):
    """ Take a timestamp and output it in the format specified in the site's config. """
    _format = _format or current_app.config["DATE_STRING_FORMAT"]
    return datetime.utcfromtimestamp(int(timestamp)).strftime(_format)


def datetime_to_datestring(_input, _format=None):
    """ Take a datetime object and output it in the format specified in the site's config. """
    _format = _format or current_app.config["DATE_STRING_FORMAT"]
    if isinstance(_input, datetime):
        return _input.strftime(_format)
    else:
        return None


def seconds_to_time(seconds):
    """ Take an integer of seconds and output it formatted as a time string (00:00:00) """
    return str(timedelta(seconds=seconds or 0))


# TODO: Make macros
def dota_wiki_link(text):
    """ Returns a Dota 2 Wiki link to the articled titled `text`. """
    return "http://dota2.gamepedia.com/{}".format(text.replace(" ", "_"))


def dotabuff_hero_link(text):
    """ Returns a Dotabuff hero link, to the name specificed in `text` """
    return "http://dotabuff.com/heroes/{}".format(text.replace(" ", "-").lower())


def dotabuff_item_link(text):
    """ Returns a Dotabuff item link, to the name specified in `text` """
    return "http://dotabuff.com/items/{}".format(text.replace(" ", "-").lower())


def dotabuff_match_link(matchid):
    """ Returns a Dotabuff match link, to the match id specified """
    return "http://dotabuff.com/matches/{}".format(matchid)





# Dota 2 API filters
@cache.cached(timeout=60 * 60, key_prefix="heroes")
@fs_fallback
def fetch_heroes():
    """ Fetch a list of heroes from the Dota 2 WebAPI.

    Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
    when interfacing with the WebAPI.

    Returns:
        A dict containing data on Dota 2 heroes.
        An empty dict if there was a HTTPError fetching the data and we did not have a file-system fallback.
    """
    try:
        res = steam.api.interface("IEconDOTA2_570").GetHeroes(language="en_US").get("result")
        return res.get("heroes")
    except steam.api.HTTPError:
        current_app.logger.warning('Filter fetch_heroes returned with HTTPError', exc_info=True)

    # This will only return on errors / exceptions
    return {}


@cache.cached(timeout=60 * 60, key_prefix="heroes_by_id")
def fetch_heroes_by_id():
    """ Returns a dict of heroes, mapped to their hero IDs. """
    return {x["id"]: x for x in fetch_heroes()}


@cache.cached(timeout=60 * 60, key_prefix="heroes_by_name")
def fetch_heroes_by_name():
    """ Returns a dict of heroes, mapped to their hero (non-localized) names. """
    return {x["name"]: x for x in fetch_heroes()}


@cache.cached(timeout=60 * 60, key_prefix="items")
@fs_fallback
def fetch_items():
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
                return {data[k]["id"]: data[k] for k in data}
            except (KeyError, ValueError):
                current_app.logger.warning('Filter fetch_items threw exception', exc_info=True, extra={
                    'extra': json.dumps({
                        'url': request.url,
                        'text': request.text,
                        'status_code': request.status_code,
                    })
                })

        else:
            current_app.logger.warning('Filter fetch_items returned with non-OK status', extra={
                'extra': json.dumps({
                    'url': request.url,
                    'text': request.text,
                    'status_code': request.status_code,
                })
            })

    except requests.exceptions.RequestException:
        current_app.logger.warning('Filter fetch_items returned with RequestException', exc_info=True)

    # This will only return on errors / exceptions
    return {}


@cache.cached(timeout=60 * 60, key_prefix="schema")
def fetch_schema():
    """ Fetches the Dota 2 item schema

    Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
    when interfacing with the WebAPI.

    Returns:
        A steam.items.schema object.
        None if there was a HTTPError fetching the data and we did not have a file-system fallback.
    """
    try:
        schema = steam.items.schema(570, lang='en_US')  # TODO: Remove lang when steamodd is fixed (lang should be optional, but throws exception on some systems)
        schema.client_url  # Touch things so steamdeeb caching actually loads data
        return schema

    except steam.api.HTTPError:
        current_app.logger.warning('Filter fetch_leagues returned with HTTPError', exc_info=True)

    # This will only return on errors / exceptions
    return None


@cache.memoize(timeout=60 * 60)
def get_hero_by_id(hero_id):
    """ Returns a hero object for the given hero ID.

    If `hero_id` is a list, it is parsed recursively.

    Args:
        hero_id: An integer representing a hero.

    Returns:
        A hero object.
        A dummy hero object if we do not have a hero object for the `hero_id` given. The dummy object is a dict
        containing `name`, `localized_name`, and `id`.
    """
    if isinstance(hero_id, list):
        hero = [fetch_heroes_by_id().get(int(x)) for x in hero_id]
    else:
        hero = fetch_heroes_by_id().get(int(hero_id))

    # Return dummy object if no match is found.
    return hero or {
        "name": str(hero_id),
        "localized_name": str(hero_id),
        "id": hero_id
    }


@cache.memoize(timeout=60 * 60)
def get_hero_by_name(hero_name):
    """ Returns a hero object for the given hero name.

    If `hero_name` is a list, it is parsed recursively.

    Args:
        hero_name: An integer representing a hero.

    Returns:
        A hero object.
        A dummy hero object if we do not have a hero object for the `hero_name` given. The dummy object is a dict
        containing `name`, `localized_name`, and `id`.
    """
    if isinstance(hero_name, list):
        hero = [fetch_heroes_by_name().get(x) for x in hero_name]
    else:
        hero = fetch_heroes_by_name().get(hero_name)

    # Return dummy object if no match is found.
    return hero or {
        "name": str(hero_name),
        "localized_name": str(hero_name),
        "id": -1
    }


@cache.memoize(timeout=60 * 60)
def get_item_by_id(item_id):
    """ Returns an item object for the given item id. """
    try:
        item = [fetch_items().get(int(x)) for x in item_id]
    except TypeError:
        item = fetch_items().get(int(item_id))
        
    # Return dummy ofjbect if no match is found.
    return item or {
        "id": item_id,
        "img": None,
        "dname": str(item_id),
        "qual": None,
        "cost": None,
        "desc": None,
        "notes": None,
        "attrib": None,
        "mc": None,
        "cd": None,
        "lore": None,
        "components": None,
        "created": None
    }


@cache.memoize(timeout=60 * 60)
def get_file_by_ugcid(ugcid):
    """ Returns a steam remote-storage file matching the given ugcid.

    Uses steamodd to interface with the WebAPI. Accesses a property in the returned object to ensure steamodd loads
    the object's data, so we can cache it properly.

    Args:
        ugcid: A unique id representing a file stored in Steam's remote storage

    Returns:
        A steam.remote_storage.ugc_file object.
        None if there was an error retrieving the file (steam.api.Exception).
    """
    try:
        file_info = steam.remote_storage.ugc_file(570, ugcid)
        file_info.url  # Access an object so steamodd actually grabs data that we can cache
        return file_info
    except steam.api.SteamError:
        pass

    # This will only return on errors / exceptions
    return None
