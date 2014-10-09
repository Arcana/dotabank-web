#!/srv/www/dotabank.com/dotabank-web/bin/python
"""
Downoad and archive league matches
"""

from app import steam, db  # .info
from app.replays.models import Replay, ReplayPlayer


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


def fetch_league_matches(league_id):
    matches = get_league_matches(league_id)
    process_match_list(matches)

if __name__ == "__main__":
    fetch_league_matches()
