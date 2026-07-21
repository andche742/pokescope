import json

import pandas as pd

XSSI_PREFIX = ";for(;;);"


def load_raw(path):
    with open(path) as f:
        text = f.read().strip()
    if text.startswith(XSSI_PREFIX):
        text = text[len(XSSI_PREFIX):]
    if text.endswith(";"):
        text = text[:-1]
    return json.loads(text)


def parse_entries(raw, limit=None):
    types = raw["dict"]["types"]
    entries = list(raw["data"].items())
    if limit is not None:
        entries = entries[:limit]

    rows = []
    for key, value in entries:
        name, slug, _coords, _unknown, type_ids, stats, number, form_id, is_variant = value
        stamina, attack, defense = stats
        rows.append({
            "number": number,
            "form_id": form_id,
            "name": name,
            "slug": slug,
            "types": [types[i - 1] for i in type_ids],
            "hp": stamina,
            "attack": attack,
            "defense": defense,
            "is_variant": bool(is_variant),
        })
    df = pd.DataFrame(rows)
    df.reset_index(inplace=True)
    return df


if __name__ == "__main__":
    raw = load_raw("pokemon.json")
    df = parse_entries(raw, limit=None)
