import sys

from calc.pvp_ranker import rank_spreads
from db.repository import (
    get_all_pokemon,
    get_cpm_table,
    get_pokemon_lookup,
    insert_cpm_rows,
    insert_evolution_rows,
    insert_pokemon_stats,
    insert_ranking_rows,
)
from scrape.cpm_scraper import fetch_html, parse_cpm_table
from scrape.pogoapi_scraper import (
    load_evolutions,
    load_megas,
    load_stats,
    parse_evolution_rows,
    parse_mega_evolution_rows,
    parse_mega_rows,
    parse_stats_rows,
)

POKEMON_STATS_JSON_PATH = "pokemon_stats.json"
POKEMON_EVOLUTIONS_JSON_PATH = "pokemon_evolutions.json"
MEGA_POKEMON_JSON_PATH = "mega_pokemon.json"

GREAT_LEAGUE_CP = 1500
ULTRA_LEAGUE_CP = 2500
LEAGUE_CP_LIMITS = (GREAT_LEAGUE_CP, ULTRA_LEAGUE_CP)
TOP_N = 100


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


def populate_megas():
    """Adds mega forms to the pokemon table, then links each to its base pokemon
    in evolutions so the evolution walk reports mega stats as a potential.

    Like populate_pokemon, there is no unique key on (number, form), so running
    this a second time inserts duplicate rows.
    """
    data = load_megas(MEGA_POKEMON_JSON_PATH)
    inserted = insert_pokemon_stats(parse_mega_rows(data))

    rows, unresolved = parse_mega_evolution_rows(data, get_pokemon_lookup())
    if unresolved:
        print(f"warning: {len(unresolved)} megas had no matching base pokemon row")
        print(unresolved[:10])

    return len(inserted), insert_evolution_rows(rows)


def populate_rankings(cp_limits=LEAGUE_CP_LIMITS, top_n=TOP_N):
    """Sweeps every pokemon's 4096 iv spreads per league and stores the top n.

    This is a batch job measured in minutes, not a per-request call -- the whole
    point of storing the top n is that displaying them needs no sweep at all.
    Ranking an arbitrary spread still sweeps live via calc.pvp_ranker.
    """
    cpm_table = get_cpm_table()
    all_pokemon = get_all_pokemon(distinct_stats=True)
    inserted = 0

    for count, pokemon in enumerate(all_pokemon, start=1):
        rows = []
        for cp_limit in cp_limits:
            spreads = rank_spreads(cp_limit, pokemon=pokemon, cpm_table=cpm_table)
            rows.extend(
                (
                    pokemon.form_id,
                    cp_limit,
                    ranking,
                    spread.attack_iv,
                    spread.defense_iv,
                    spread.stamina_iv,
                    spread.level,
                    spread.cp,
                    spread.stat_product,
                )
                for ranking, spread in enumerate(spreads[:top_n], start=1)
            )

        if rows:
            inserted += insert_ranking_rows(rows)

        if count % 50 == 0:
            print(f"  {count}/{len(all_pokemon)} pokemon ranked")

    return inserted


if __name__ == "__main__":
    if "--rankings" in sys.argv:
        print("ranking rows inserted:", populate_rankings())
    elif "--megas" in sys.argv:
        mega_rows, edge_rows = populate_megas()
        print("mega rows inserted:", mega_rows)
        print("mega evolution edges inserted:", edge_rows)
    else:
        print("cpm rows inserted:", populate_cpm())
        id_lookup = populate_pokemon()
        print("pokemon rows inserted:", len(id_lookup))
        print("evolution rows inserted:", populate_evolutions(id_lookup))
