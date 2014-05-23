from app import mem_cache, fs_cache, steam
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
    return u"http://dota2.gamepedia.com/{}".format(text.replace(" ", "_"))


def dotabuff_hero_link(text):
    """ Returns a Dotabuff hero link, to the name specificed in `text` """
    return u"http://dotabuff.com/heroes/{}".format(text.replace(" ", "-").lower())


def dotabuff_item_link(text):
    """ Returns a Dotabuff item link, to the name specified in `text` """
    return u"http://dotabuff.com/items/{}".format(text.replace(" ", "-").lower())


def dotabuff_match_link(matchid):
    """ Returns a Dotabuff match link, to the match id specified """
    return u"http://dotabuff.com/matches/{}".format(matchid)
