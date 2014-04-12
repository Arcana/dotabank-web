from app import cache, steam
from flask import current_app, url_for
import json
import requests
from datetime import datetime, timedelta
from jinja2 import Markup

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


def timestamp_to_datestring(timestamp):
    """ Take a timestamp and output it in the format specified in the site's config. """
    # TODO: Allow method call to overwrite format, use config as default.
    return datetime.utcfromtimestamp(int(timestamp)).strftime(current_app.config["DATE_STRING_FORMAT"])


def datetime_to_datestring(_input):
    """ Take a datetime object and output it in the format specified in the site's config. """

    # TODO: Allow method call to overwrite format, use config as default.
    if isinstance(_input, datetime):
        return _input.strftime(current_app.config["DATE_STRING_FORMAT"])
    else:
        return None


def seconds_to_time(seconds):
    """ Take an integer of seconds and output it formatted as a time string (00:00:00) """
    return str(timedelta(seconds=seconds or 0))


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


# Generic API filters
@cache.memoize()
def get_steamid_from_accountid(account_id):
    """ Takes a single or many account IDs, and constructs the steam ID for those account ids.

    If `account_id` is a list, it is parsed recursively.

    Args:
        account_id: An Integer representing an account id, or an array of the same.

    Returns:
        A Long reprsenting a steam id, or an array of the same.

    Raises:
        TypeError: An error occured adding the given `account_id` and the integer required to form a Steam ID, because
        `account_id` is not an integer.
    """
    if isinstance(account_id, list):
        return [get_steamid_from_accountid(_account_id) for _account_id in account_id]
    else:
        return account_id + 76561197960265728


@cache.memoize(timeout=60 * 60)
def get_account_by_id(account_id):
    """ Takes a single or many account IDs, and returns a populated steam.user.profile object for each account id.app

    Gets the steam id for the given account id(s), and uses steamodd to create steam.user.profile objects for each
    account.  Accesses a property in each object to ensure steamodd loads external data, which we can then cache.

    Args:
        account_id: An integer representing an account id, or a list of the same.

    Returns:
        A list of steamodd.user.profile objects.
        None, if there was a problem fetching objects.
    """
    try:
        if isinstance(account_id, list):
            steam_ids = get_steamid_from_accountid(account_id)
            res = steam.user.profile_batch(steam_ids)
            for account in res:
                account.id64
        else:
            steam_id = get_steamid_from_accountid(account_id)
            res = steam.user.profile(steam_id)
            res.id64

        return res
    except steam.api.HTTPFileNotFoundError:
        current_app.logger.warning('Filter get_account_by_id threw HTTPFileNotFoundError', exc_info=True, extra={
            'extra': json.dumps({'account_id': account_id})
        })
        return None


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


@cache.cached(timeout=60 * 60, key_prefix="leagues")
@fs_fallback
def fetch_leagues():
    """ Fetch a list of leagues from the Dota 2 WebAPI.

    Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
    when interfacing with the WebAPI.

    Returns:
        A dict containing data on Dota 2 leagues, mapped by their league id..
        An empty dict if there was a HTTPError fetching the data and we did not have a file-system fallback.
    """
    try:
        res = steam.api.interface("IDOTA2Match_570").GetLeagueListing(language="en_US").get("result")
        return {x["leagueid"]: x for x in res.get("leagues")}

    except steam.api.HTTPError:
        current_app.logger.warning('Filter fetch_leagues returned with HTTPError', exc_info=True)

    # This will only return on errors / exceptions
    return {}


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
        return [fetch_items().get(int(x)) for x in item_id]
    except TypeError:
        return fetch_items().get(int(item_id))


@cache.memoize(timeout=60 * 60)
def get_league_by_id(league_id):
    """ Returns a league object for the given league id. """
    try:
        return [fetch_leagues().get(int(x)) for x in league_id]
    except TypeError:
        return fetch_leagues().get(int(league_id))


@cache.memoize(timeout=60 * 60)
def get_file_by_ugcid(ugcid):
    """ Returns a steam remote-storage file matching the given ugcid.

    Uses steamodd to interface with the WebAPI. Accesses a property in the returned object to ensure steamodd loads
    the object's data, so we can cache it properly.

    Args:
        ugcid: A unique id representing a file stored in Steam's remote storage

    Returns:
        A steam.remote_storage.ugc_file object.
        None if there was an error retrieving the file (FileNotFoundError or HTTPError).
    """
    try:
        file_info = steam.remote_storage.ugc_file(570, ugcid)
        file_info.url  # Access an object so steamodd actually grabs data that we can cache
        return file_info
    except (steam.remote_storage.FileNotFoundError, steam.api.HTTPError):
        current_app.logger.warning('Filter get_file_by_ugcid threw exception', exc_info=True)

    # This will only return on errors / exceptions
    return None


def lobby_type(value):
    """ Returns a human-friendly string for the lobby type id given.

    Lobby data interpreted from the game's protobufs:
        https://github.com/SteamRE/SteamKit/blob/master/Resources/Protobufs/dota/dota_gcmessages_common.proto#L803
    """
    try:
        return ["Public Matchmaking",
         "Practice Game",
         "Tournament Game",
         "Tutorial",
         "Co-op Bot",
         "Team Matchmaking",
         "Solo Matchmaking",
         "Ranked Match"][value]
    except (IndexError, TypeError):
        return "Invalid ({})".format(value)


def game_mode(value):
    """ Returns a human-friendly string for the game mode id given.

    Game mode data interpreted from the game's protobufs:
        https://github.com/SteamRE/SteamKit/blob/master/Resources/Protobufs/dota/dota_gcmessages_common.proto#L407
    """
    if not value or value == 0:
        return "Unknown"
    else:
        try:
            return ["Invalid (0)",              # DOTA_GAMEMODE_NONE = 0;
                    "All Pick",                 # DOTA_GAMEMODE_AP = 1;
                    "Captain's Mode",           # DOTA_GAMEMODE_CM = 2;
                    "Random Draft",             # DOTA_GAMEMODE_RD = 3;
                    "Standard Draft",           # DOTA_GAMEMODE_SD = 4;
                    "All Random",               # DOTA_GAMEM ODE_AR = 5;
                    "Invalid (6)",              # DOTA_GAMEMODE_INTRO = 6;
                    "Diretide",                 # DOTA_GAMEMODE_HW = 7;
                    "Reverse Captains Mode",    # DOTA_GAMEMODE_REVERSE_CM = 8;
                    "The Greeviling",           # DOTA_GAMEMODE_XMAS = 9;
                    "Tutorial",                 # DOTA_GAMEMODE_TUTORIAL = 10;
                    "Mid Only",                 # DOTA_GAMEMODE_MO = 11;
                    "Least Played",             # DOTA_GAMEMODE_LP = 12;
                    "Limited Heroes",           # DOTA_GAMEMODE_POOL1 = 13;
                    "Compendium",               # DOTA_GAMEMODE_FH = 14;
                    "Invalid (15)",             # DOTA_GAMEMODE_CUSTOM = 15;
                    "Captains Draft",           # DOTA_GAMEMODE_CD = 16;
                    "Balanced Draft",           # DOTA_GAMEMODE_BD = 17;
                    "Ability Draft",            # DOTA_GAMEMODE_ABILITY_DRAFT = 18;
                    "Invalid (19)"              # DOTA_GAMEMODE_EVENT = 19;
                    ][value]
        except IndexError:
            return "Invalid ({})".format(value)


def players_to_teams(players):
    """ Takes a list of players and returns a tuple (radiant, dire) after splitting them into teams. """
    # Sort players by their in-game slot
    players = sorted(players, key=lambda x: x.player_slot)

    # Split players into teams
    radiant = [p for p in players if p.team == "Radiant"]  # 8th bit false
    dire = [p for p in players if p.team == "Dire"]  # 8th bit true

    return radiant, dire
