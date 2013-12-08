from app import cache, steam


# General filters
def escape_every_character(text):
    """ Used primarily for obfuscating email addresses
    """
    return "".join("&#{};".format(ord(x)) for x in text)


# Generic API filters
@cache.memoize(timeout=60 * 60)
def get_account_by_id(account_id):
    if isinstance(account_id, list):
        steam_ids = [_account_id + 76561197960265728 for _account_id in account_id]
        res = steam.user.profile_batch(steam_ids)
    else:
        steam_id = account_id + 76561197960265728
        res = steam.user.profile(steam_id)
    return res

# Dota 2 API filters
@cache.cached(timeout=60 * 60, key_prefix="heroes")
def fetch_heroes():
    res = steam.api.interface("IEconDOTA2_570").GetHeroes(language="en_US").get("result")
    return res.get("heroes")


@cache.cached(timeout=60 * 60, key_prefix="heroes_by_id")
def fetch_heroes_by_id():
    return {x["id"]: x for x in fetch_heroes()}


@cache.cached(timeout=60 * 60, key_prefix="heroes_by_name")
def fetch_heroes_by_name():
    return {x["name"]: x for x in fetch_heroes()}


@cache.memoize(timeout=60 * 60)
def get_hero_by_id(hero_id):
    if isinstance(hero_id, list):
        hero = [fetch_heroes_by_id().get(x) for x in hero_id]
    else:
        hero = fetch_heroes_by_id().get(hero_id)

    # Return dummy object if no match is found.
    return hero or {"name": hero_id, "localized_name": hero_id, "id": hero_id}


@cache.memoize(timeout=60 * 60)
def get_hero_by_name(hero_name):
    if isinstance(hero_name, list):
        hero = [fetch_heroes_by_name().get(x) for x in hero_name]
    else:
        hero = fetch_heroes_by_name().get(hero_name)

    # Return dummy object if no match is found.
    return hero or {"name": hero_name, "localized_name": hero_name, "id": -1}
