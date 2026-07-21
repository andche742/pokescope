import bisect
import math

from db.repository import get_cpm, get_cpm_table, get_pokemon

def calc_cp(id, level, attack_iv, defense_iv, stamina_iv):
    cpm = get_cpm(level)
    pokemon = get_pokemon(id)

    cp = max(10, math.floor((pokemon.attack + attack_iv) * (pokemon.defense + defense_iv)**0.5 * (pokemon.stamina + stamina_iv)**0.5 * (cpm)**2 / 10))

    return cp

def calc_level(id, cp, attack_iv, defense_iv, stamina_iv):
    pokemon = get_pokemon(id)
    attack = pokemon.attack + attack_iv
    defense = pokemon.defense + defense_iv
    stamina = pokemon.stamina + stamina_iv

    levels, multipliers = get_cpm_table()
    cps = [max(10, math.floor(attack * defense**0.5 * stamina**0.5 * m**2 / 10)) for m in multipliers]

    idx = bisect.bisect_left(cps, cp)
    if idx == len(cps) or cps[idx] != cp:
        return None

    return levels[idx]