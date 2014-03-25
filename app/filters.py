from app import cache, steam
from flask import current_app, url_for
import json
import urllib2
from datetime import datetime, timedelta
from jinja2 import Markup


# General filters
def escape_every_character(text):
    """ Used primarily for obfuscating email addresses
    """
    return "".join("&#{};".format(ord(x)) for x in text)


def timestamp_to_datestring(timestamp):
    return datetime.utcfromtimestamp(int(timestamp)).strftime(current_app.config["DATE_STRING_FORMAT"])

def datetime_to_datestring(input):
    if isinstance(input, datetime):
        return input.strftime(current_app.config["DATE_STRING_FORMAT"])
    else:
        return None


def seconds_to_time(seconds):
    return str(timedelta(seconds=seconds or 0))


def dota_wiki_link(text):
    return "http://dota2.gamepedia.com/{}".format(text.replace(" ", "_"))


def dotabuff_hero_link(text):
    return "http://dotabuff.com/heroes/{}".format(text.replace(" ", "-").lower())


def dotabuff_item_link(text):
    return "http://dotabuff.com/items/{}".format(text.replace(" ", "-").lower())


def dotabuff_match_link(matchid):
    return "http://dotabuff.com/matches/{}".format(matchid)


# Generic API filters
@cache.memoize()
def get_steamid_from_accountid(account_id):
    if isinstance(account_id, list):
        return [get_steamid_from_accountid(_account_id) for _account_id in account_id]
    else:
        return account_id + 76561197960265728


@cache.memoize(timeout=60 * 60)
def get_account_by_id(account_id):
    try:
        if isinstance(account_id, list):
            steam_ids = get_steamid_from_accountid(account_id)
            res = steam.user.profile_batch(steam_ids)
        else:
            steam_id = get_steamid_from_accountid(account_id)
            res = steam.user.profile(steam_id)
            res.id64

        return res
    except steam.api.HTTPFileNotFoundError:
        return None


# Dota 2 API filters
@cache.cached(timeout=60 * 60, key_prefix="heroes")
def fetch_heroes():
    res = steam.api.interface("IEconDOTA2_570").GetHeroes(language="en_US").get("result")
    return res.get("heroes")


@cache.cached(timeout=60 * 60, key_prefix="heroes_by_id")
def fetch_heroes_by_id():
    try:
        return {x["id"]: x for x in fetch_heroes()}
    except steam.api.HTTPError:
        return {}


@cache.cached(timeout=60 * 60, key_prefix="heroes_by_name")
def fetch_heroes_by_name():
    try:
        return {x["name"]: x for x in fetch_heroes()}
    except steam.api.HTTPError:
        return {}

@cache.cached(timeout=60 * 60, key_prefix="items")
def fetch_items():
    try:
        data = json.loads(urllib2.urlopen("http://www.dota2.com/jsfeed/itemdata").read())["itemdata"]
        return {data[k]["id"]: data[k] for k in data}
    except urllib2.URLError:
        return {}


@cache.cached(timeout=60 * 60, key_prefix="leagues")
def fetch_leagues():
    try:
        res = steam.api.interface("IDOTA2Match_570").GetLeagueListing(language="en_US").get("result")
        return {x["leagueid"]: x for x in res.get("leagues")}
    except steam.api.HTTPError:
        return {}


@cache.memoize(timeout=60 * 60)
def get_hero_by_id(hero_id):
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
    try:
        return [fetch_items().get(item(x)) for x in item_id]
    except TypeError:
        return fetch_items().get(int(item_id))


@cache.memoize(timeout=60 * 60)
def get_league_by_id(league_id):
    try:
        return [fetch_leagues().get(int(x)) for x in league_id]
    except TypeError:
        return fetch_leagues().get(int(league_id))


@cache.memoize(timeout=60 * 60)
def get_file_by_ugcid(ugcid):
    try:
        file_info = steam.remote_storage.ugc_file(570, ugcid)
        file_info.url
        return file_info
    except (steam.remote_storage.FileNotFoundError, steam.api.HTTPError):
        return None


def lobby_type(value):
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
    if not value or value == 0:
        return "Unknown"
    else:
        try:
            return ["Invalid (0)",
                    "All Pick",
                    "Captain's Mode",
                    "Random Draft",
                    "Standard Draft",
                    "All Random",
                    "Invalid (6)",
                    "Diretide",
                    "Reverse Captains Mode",
                    "The Greeviling",
                    "Tutorial",
                    "Mid Only",
                    "Least Played",
                    "Limited Heroes",
                    "Compendium",
                    "Captains Draft",
                    "Balanced Draft",
                    "Invalid (17)",
                    "Ability Draft"][value]
        except IndexError:
            return "Invalid ({})".format(value)


def building_status(value):
    try:
        if not value or value == "0":
            return " destroyed"
        else:
            return ""
    except IndexError:
        return " destroyed"


def players_to_teams(players):
    # Sort players by their in-game slot
    players = sorted(players, key=lambda x: x.player_slot)

    # Split players into teams
    radiant = [p for p in players if p.team == "Radiant"]  # 8th bit false
    dire = [p for p in players if p.team == "Dire"]  # 8th bit true

    return radiant, dire


def pagination(pagination_obj, endpoint, endpoint_values={}, size="sm"):
    if pagination_obj.pages > 1:
        paginated = '<ul class="pagination pagination-{size}">'.format(size=size)
        if pagination_obj.has_prev:
            paginated += '<li><a class="prev" href="{url}">&#9664;</a></li>'.format(url=url_for(endpoint, page=pagination_obj.prev_num, **endpoint_values))
        else:
            paginated += '<li class="disabled"><a class="prev">&#9664;</a></li>'
        if pagination_obj.has_next:
            paginated += '<li><a class="next" href="{url}">&#9654;</a></li>'.format(url=url_for(endpoint, page=pagination_obj.next_num, **endpoint_values))
        else:
            paginated += '<li class="disabled"><a class="next">&#9654;</a></li>'
        for page in pagination_obj.iter_pages():
            if page:
                if page is not pagination_obj.page:
                    paginated += '<li><a href="{url}">{page}</a></li>'.format(url=url_for(endpoint, page=page, **endpoint_values), page=page)
                else:
                    paginated += '<li class="active"><a>{page}</a></li>'.format(page=page)
            else:
                paginated += '<li class="disabled"><a>&hellip;</a></li>'
        paginated += '</ul>'
        return Markup(paginated)
    else:
        return ""
