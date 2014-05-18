from app import cache, steam
from flask import current_app
from datetime import datetime, timedelta


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
