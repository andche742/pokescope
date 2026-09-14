import bisect
import math

from db.repository import get_cpm, get_cpm_table, get_pokemon

def calc_stats(attack_iv, defense_iv, stamina_iv, pokemon=None, id=None, level=None, cpm=None):
    if pokemon == None:
        if id == None:
            return None
        pokemon = get_pokemon(id)

    if cpm == None:
        if level == None:
            return None
        cpm = get_cpm(level)

    attack = (pokemon.attack + attack_iv) * cpm
    defense = (pokemon.defense + defense_iv) * cpm
    stamina = (pokemon.stamina + stamina_iv) * cpm
    cp = max(10, math.floor(attack * defense**0.5 * stamina**0.5 / 10))

    return cp, attack, defense, math.floor(stamina)

def calc_level(cp, attack_iv, defense_iv, stamina_iv, pokemon=None, id=None):
    if pokemon == None:
        if id == None:
            return None
        pokemon = get_pokemon(id)

    if cp == 10:
        # max(10, ...) clamp means many levels can produce this CP -- just
        # assume the lowest level for now (could disambiguate with an HP
        # reading later on)
        return 1

    attack = pokemon.attack + attack_iv
    defense = pokemon.defense + defense_iv
    stamina = pokemon.stamina + stamina_iv

    cpm_approx = math.sqrt(10 * cp / (attack * defense**0.5 * stamina**0.5))

    levels, multipliers = get_cpm_table()
    idx = bisect.bisect_left(multipliers, cpm_approx)
    if idx == len(levels) or calc_stats(attack_iv, defense_iv, stamina_iv, pokemon=pokemon, cpm=multipliers[idx])[0] != cp:
        return None

    return levels[idx]

def calc_max_level(cp_limit, attack_iv, defense_iv, stamina_iv, pokemon=None, id=None, cpm_table=None):
    if pokemon == None:
        if id == None:
            return None
        pokemon = get_pokemon(id)

    if cpm_table == None:
        cpm_table = get_cpm_table()
    levels, multipliers = cpm_table

    # cp is monotonic in the multiplier, so bisect on a computed cp instead of
    # building all ~101 of them -- ~8 calc_stats calls per spread rather than 101,
    # which matters when the pvp ranker sweeps 4096 spreads per species
    idx = bisect.bisect_right(
        multipliers,
        cp_limit,
        key=lambda m: calc_stats(attack_iv, defense_iv, stamina_iv, pokemon=pokemon, cpm=m)[0],
    ) - 1
    if idx < 0:
        return None

    cp, attack, defense, stamina = calc_stats(
        attack_iv, defense_iv, stamina_iv, pokemon=pokemon, cpm=multipliers[idx]
    )
    product = attack * defense * stamina
    return levels[idx], cp, attack, defense, stamina, product
