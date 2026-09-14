import json


def load_stats(path):
    with open(path) as f:
        data = json.load(f)
    return data


def parse_stats_rows(data):
    """Returns rows ready for db.repository.insert_pokemon_stats:
    (number, name, stamina, attack, defense, form)
    """
    return [
        (
            entry["pokemon_id"],
            entry["pokemon_name"],
            entry["base_stamina"],
            entry["base_attack"],
            entry["base_defense"],
            entry["form"],
        )
        for entry in data
    ]


def load_evolutions(path):
    with open(path) as f:
        data = json.load(f)
    return data


# pokemon_evolutions.json and pokemon_stats.json disagree on form labels for
# these two species -- an inconsistency in pogoapi.net's own data between the
# two endpoints, not something derivable from either file alone. Hardcoded
# here since it's only 2 of 566 evolution edges:
#   - (866, "Rime_normal"): evolutions.json calls Mr. Rime's form
#     "Rime_normal", but stats.json has it under "Galarian" (inherited from
#     the Mr. Mime line) and has no "Rime_normal" entry at all.
#   - (964, "Normal"): evolutions.json expects Finizen to evolve into a
#     "Normal" form of Palafin, but stats.json only defines Palafin's two
#     battle forms, "Hero" and "Zero" -- no default/"Normal" form exists.
FORM_ALIASES = {
    (866, "Rime_normal"): (866, "Galarian"),
    (964, "Normal"): (964, "Zero"),
}


def parse_evolution_rows(data, id_lookup):
    """Resolves (pokemon_id, form) pairs against id_lookup (from
    db.repository.get_pokemon_lookup) into (from_id, to_id) rows.

    Returns (rows, unresolved) where unresolved lists any (pokemon_id, form)
    pairs that couldn't be found in id_lookup, for diagnostics.
    """
    rows = []
    unresolved = []
    for entry in data:
        from_key = FORM_ALIASES.get(
            (entry["pokemon_id"], entry["form"]), (entry["pokemon_id"], entry["form"])
        )
        from_id = id_lookup.get(from_key)
        if from_id is None:
            unresolved.append(from_key)
            continue
        for evolution in entry["evolutions"]:
            to_key = FORM_ALIASES.get(
                (evolution["pokemon_id"], evolution["form"]),
                (evolution["pokemon_id"], evolution["form"]),
            )
            to_id = id_lookup.get(to_key)
            if to_id is None:
                unresolved.append(to_key)
                continue
            rows.append((from_id, to_id))
    return rows, unresolved


def load_megas(path):
    with open(path) as f:
        data = json.load(f)
    return data


# mega_pokemon.json's "form" describes the mega variant, not the base pokemon --
# it is "Normal" for the 46 species with a single mega, and "X"/"Y" for
# charizard. Stored under distinct form labels so megas never collide with their
# base pokemon's own (number, form) key.
MEGA_FORM_LABELS = {"Normal": "Mega", "X": "Mega_x", "Y": "Mega_y"}


def mega_form_label(form):
    return MEGA_FORM_LABELS.get(form, f"Mega_{form.lower()}")


def parse_mega_rows(data):
    """Returns rows ready for db.repository.insert_pokemon_stats:
    (number, name, stamina, attack, defense, form)
    """
    return [
        (
            entry["pokemon_id"],
            entry["mega_name"],
            entry["stats"]["base_stamina"],
            entry["stats"]["base_attack"],
            entry["stats"]["base_defense"],
            mega_form_label(entry["form"]),
        )
        for entry in data
    ]


def parse_mega_evolution_rows(data, id_lookup):
    """Resolves (from_id, to_id) edges linking each base pokemon to its mega.

    Energy requirements are ignored -- the edge exists so the evolution walk can
    report a mega's potential stats, not to model whether it can be afforded.
    """
    rows = []
    unresolved = []
    for entry in data:
        from_id = id_lookup.get((entry["pokemon_id"], "Normal"))
        to_id = id_lookup.get((entry["pokemon_id"], mega_form_label(entry["form"])))
        if from_id is None or to_id is None:
            unresolved.append((entry["pokemon_id"], entry["mega_name"]))
            continue
        rows.append((from_id, to_id))
    return rows, unresolved


if __name__ == "__main__":
    data = load_stats("pokemon_stats.json")
    rows = parse_stats_rows(data)
    print(f"{len(rows)} rows parsed")
    print(rows[:5])
