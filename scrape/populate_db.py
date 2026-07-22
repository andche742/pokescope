from db.repository import (
    get_pokemon_lookup,
    insert_cpm_rows,
    insert_evolution_rows,
    insert_pokemon_stats,
)
from scrape.cpm_scraper import fetch_html, parse_cpm_table
from scrape.pogoapi_scraper import (
    load_evolutions,
    load_stats,
    parse_evolution_rows,
    parse_stats_rows,
)

POKEMON_STATS_JSON_PATH = "pokemon_stats.json"
POKEMON_EVOLUTIONS_JSON_PATH = "pokemon_evolutions.json"


def populate_cpm():
    df = parse_cpm_table(fetch_html())
    rows = list(df[["level", "value"]].itertuples(index=False, name=None))
    return insert_cpm_rows(rows)


def populate_pokemon():
    """Returns a (number, form) -> form_id lookup, needed to resolve
    evolutions.from_id/to_id against the freshly generated form_ids."""
    rows = parse_stats_rows(load_stats(POKEMON_STATS_JSON_PATH))
    return insert_pokemon_stats(rows)


def populate_evolutions(id_lookup=None):
    """id_lookup defaults to a fresh read from the pokemon table, so this can
    be run independently of populate_pokemon() in the same process."""
    if id_lookup is None:
        id_lookup = get_pokemon_lookup()

    data = load_evolutions(POKEMON_EVOLUTIONS_JSON_PATH)
    rows, unresolved = parse_evolution_rows(data, id_lookup)
    if unresolved:
        print(f"warning: {len(unresolved)} (number, form) pairs had no matching pokemon row")
        print(unresolved[:10])

    return insert_evolution_rows(rows)


if __name__ == "__main__":
    print("cpm rows inserted:", populate_cpm())
    id_lookup = populate_pokemon()
    print("pokemon rows inserted:", len(id_lookup))
    print("evolution rows inserted:", populate_evolutions(id_lookup))
