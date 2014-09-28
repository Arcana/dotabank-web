#!/srv/www/dotabank.com/dotabank-web/bin/python
"""
Downoad and archive TI4 matches
"""

from app import steam, db  # .info
from app.replays.models import Replay, ReplayPlayer

THE_INTERNATIONAL_4_ID = 600
THE_INTERNATIONAL_4_ONE_PLAYER_FROM_EACH_TEAM = [  # Amazing variable naming.
    '76482434',  # Alliance; Bulldoge
    '89249333',   # Titan; Net
    '73562326',   # EG; Zai
    '19672354',  # Fnatic; BigDogey
    '89157606',  # Newbee; Mu
    '91698091',   # Vici; rotk
    '86723143',   # Na'Vi; Funn1k
    '89871557',   # DK; Mushi
    '88553213',   # iG; Chaun
    '19757254',   # Cloud 9; SingKongor
    '86802844',   # Empire; Mag
    '1185644',    # Na'Vi US; Korok
    '96429099',  # Arrow; Lance
    '136477860',  # LGD; Lin
    '87382579',   # mouz; Misery
    '85805514',   # Liquid; Pegasus
    '102525542',   # MVP; Reisen
    '21289303',   # CIS; Black
    '87586992'    # VP; G
]


def get_league_matches(league_id, all_pages=True):
    """
    Queries the WebAPI and fetches the list of matches for the given league ID.

    @param league_id: The league ID for which we want to find matches.
    @param all_pages: Whether or not to paginate through the results and return every match, or just the latest 100.
    """
    matches = []  # List of matches
    match_query = None  # Results of WebAPI query.

    while match_query is None or (match_query.get('results_remaining') > 0 and all_pages is True):
        # If we already have some matches, use the last one's match id as the beginning of our query.
        if len(matches) > 0:
            match_query = steam.api.interface("IDOTA2Match_570").GetMatchHistory(league_id=league_id, start_at_match_id=matches[-1].get("match_id")).get("result")
        # Otherwise get whatever
        else:
            match_query = steam.api.interface("IDOTA2Match_570").GetMatchHistory(league_id=league_id).get("result")

        # Add the new matches to our list of matches
        matches.extend(match_query.get('matches'))

    return matches


def get_league_matches_via_players(players, league_id):
    """ A workaround for certain leagues (The International 4) inexplicably excluding games from a GetMatchHistory call.
    Instead we call GetTournamentPlayerStats for a player from each team and get match id's that way, then filter out
    duplicates and return the final list of matches.

    Credit to GelioS of Dota 2 Statistics
    - http://dev.dota2.com/showthread.php?t=140705&p=1113005&viewfull=1#post1113005
    - http://dota2statistic.com/index.php/blog/7
    """
    matches = {}

    # Go through each player and get their matches played
    for player in players:
        player_stats_query = steam.api.interface("IDOTA2Match_570").GetTournamentPlayerStats(league_id=league_id, account_id=player).get("result")

        # Add the matches to the `matches` dict - filtering out dupes along the way.
        for match in player_stats_query.get("matches"):
            if match.get("match_id") not in matches.keys():
                matches[match.get("match_id")] = match

    # Return matches
    return matches.values()


def process_match_list(matches):
    """ Iterates through a list ofmatches and checks whether we already have them in our database. If we do not then
    this code will add the match to our database and create an associated GC job. """
    if len(matches) > 0:
        for match in matches:
            replay_exists = Replay.query.filter(Replay.id == match["match_id"]).count() > 0

            if not replay_exists:
                replay = Replay(match["match_id"])
                db.session.add(replay)
                db.session.commit()

                Replay.add_gc_job(replay)

                print "Added {} to database and job queue".format(match["match_id"])
            else:
                print "Match {} already in database, skipping.".format(match["match_id"])


def main():
    #matches = get_league_matches(THE_INTERNATIONAL_4_ID)
    matches = get_league_matches_via_players(THE_INTERNATIONAL_4_ONE_PLAYER_FROM_EACH_TEAM, THE_INTERNATIONAL_4_ID)
    process_match_list(matches)

if __name__ == "__main__":
    main()
