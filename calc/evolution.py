from calc.cp_formula import calc_stats
from db.repository import get_evolutions, get_pokemon

def calc_evolution_stats(attack_iv, defense_iv, stamina_iv, level, pokemon=None, id=None):
    if pokemon == None:
        if id == None:
            return None
        pokemon = get_pokemon(id)

    results = []
    for evolution_id in get_evolutions(pokemon.form_id):
        evolution_pokemon = get_pokemon(evolution_id)
        stats = calc_stats(attack_iv, defense_iv, stamina_iv, pokemon=evolution_pokemon, level=level)
        results.append((evolution_id, stats))
        results.extend(
            calc_evolution_stats(attack_iv, defense_iv, stamina_iv, level, pokemon=evolution_pokemon)
        )

    return results
