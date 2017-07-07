from ranking import Ranking


def sort_and_rank(items, key):
    return Ranking(sorted(items, key=key, reverse=True), key=key, start=1)
