from collections import namedtuple

from calc.cp_formula import calc_max_level
from db.repository import get_cpm_table, get_pokemon

IV_RANGE = range(16)

Spread = namedtuple("Spread", ["stat_product", "attack_iv", "defense_iv", "stamina_iv", "level", "cp"])

def rank_spreads(cp_limit, pokemon=None, id=None, cpm_table=None):
    """Sweeps all 4096 iv spreads and returns them sorted by stat product, best first.

    Stat product uses unfloored attack/defense and floored stamina, matching how
    the game itself calculates: only hp is discrete.
    """
    if pokemon == None:
        if id == None:
            return None
        pokemon = get_pokemon(id)

    if cpm_table == None:
        cpm_table = get_cpm_table()

    spreads = []
    for attack_iv in IV_RANGE:
        for defense_iv in IV_RANGE:
            for stamina_iv in IV_RANGE:
                result = calc_max_level(
                    cp_limit, attack_iv, defense_iv, stamina_iv, pokemon=pokemon, cpm_table=cpm_table
                )
                if result == None:
                    continue

                level, cp, attack, defense, stamina, stat_product = result
                spreads.append(Spread(stat_product, attack_iv, defense_iv, stamina_iv, level, cp))

    spreads.sort(reverse=True)
    return spreads

def rank_spread(attack_iv, defense_iv, stamina_iv, cp_limit, pokemon=None, id=None, cpm_table=None):
    """Returns (rank, spread) for one iv spread, where rank is 1-indexed against
    every other spread for the same pokemon and cp limit."""
    spreads = rank_spreads(cp_limit, pokemon=pokemon, id=id, cpm_table=cpm_table)
    if spreads == None:
        return None

    for rank, spread in enumerate(spreads, start=1):
        if (spread.attack_iv, spread.defense_iv, spread.stamina_iv) == (attack_iv, defense_iv, stamina_iv):
            return rank, spread

    return None
