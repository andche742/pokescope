from collections import namedtuple

from db.connection import get_connection


def get_pokemon(form_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT form_id, number, name, stamina, attack, defense, form "
            "FROM pokemon WHERE form_id = %s",
            (form_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        Pokemon = namedtuple("Pokemon", cursor.column_names)
        return Pokemon(*row)
    finally:
        cursor.close()
        conn.close()


def get_cpm(level):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM cpm WHERE level = %s", (level,))
        row = cursor.fetchone()
        return float(row[0]) if row else None
    finally:
        cursor.close()
        conn.close()


def get_cpm_table():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT level, value FROM cpm ORDER BY level ASC")
        rows = cursor.fetchall()
        return [float(row[0]) for row in rows], [float(row[1]) for row in rows]
    finally:
        cursor.close()
        conn.close()


POKEMON_COLUMNS = "form_id, number, name, stamina, attack, defense, form"

# one representative per (number, base stats) group, preferring the Normal form.
# keep this ordering in sync with get_ranking_form_id, or a lookup can resolve to
# a different row than the batch job stored.
DISTINCT_STATS_QUERY = f"""
    SELECT {POKEMON_COLUMNS} FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY number, attack, defense, stamina
            ORDER BY (form = 'Normal') DESC, form_id ASC
        ) rn FROM pokemon
    ) t WHERE rn = 1
"""


def get_all_pokemon(distinct_stats=False):
    """Returns every pokemon row, so a batch job can avoid one query per species.

    distinct_stats collapses forms that share a dex number and identical base
    stats -- costumes, unown letters, spinda patterns -- down to one row. Forms
    that genuinely differ (deoxys, gourgeist sizes, megas) have different stats,
    so they survive on their own.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if distinct_stats:
            cursor.execute(DISTINCT_STATS_QUERY)
        else:
            cursor.execute(f"SELECT {POKEMON_COLUMNS} FROM pokemon")
        rows = cursor.fetchall()
        Pokemon = namedtuple("Pokemon", cursor.column_names)
        return [Pokemon(*row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_ranking_form_id(form_id):
    """Maps any form_id onto the representative used by the rankings batch job.

    A costume pikachu has no rankings rows of its own -- they are stored against
    whichever form represents its (number, base stats) group.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT representative.form_id FROM pokemon scanned "
            "JOIN pokemon representative ON representative.number = scanned.number "
            "AND representative.attack = scanned.attack "
            "AND representative.defense = scanned.defense "
            "AND representative.stamina = scanned.stamina "
            "WHERE scanned.form_id = %s "
            "ORDER BY (representative.form = 'Normal') DESC, representative.form_id ASC "
            "LIMIT 1",
            (form_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
        conn.close()


def get_evolutions(from_id):
    """Returns a list of form_ids this pokemon can evolve into (empty if none)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT to_id FROM evolutions WHERE from_id = %s", (from_id,))
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_pokemon_lookup():
    """Returns a dict mapping (number, form) -> form_id for every pokemon row."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT number, form, form_id FROM pokemon")
        return {(number, form): form_id for number, form, form_id in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def insert_evolution_rows(rows):
    """rows: iterable of (from_id, to_id)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT IGNORE INTO evolutions (from_id, to_id) VALUES (%s, %s)", rows
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def get_rankings(form_id, cp_limit, limit=100):
    """Returns the stored top spreads for a pokemon/league, best rank first."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ranking, attack_iv, defense_iv, stamina_iv, level, cp, stat_product "
            "FROM pvp_rankings WHERE form_id = %s AND cp_limit = %s "
            "ORDER BY ranking ASC LIMIT %s",
            (form_id, cp_limit, limit),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def insert_ranking_rows(rows):
    """rows: iterable of
    (form_id, cp_limit, ranking, attack_iv, defense_iv, stamina_iv, level, cp, stat_product)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT IGNORE INTO pvp_rankings "
            "(form_id, cp_limit, ranking, attack_iv, defense_iv, stamina_iv, level, cp, stat_product) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            rows,
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def insert_cpm_rows(rows):
    """rows: iterable of (level, value)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany("INSERT IGNORE INTO cpm (level, value) VALUES (%s, %s)", rows)
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def insert_pokemon_stats(rows):
    """rows: iterable of (number, name, stamina, attack, defense, form).

    form_id is auto-increment, so each row is inserted individually to capture
    its generated form_id via cursor.lastrowid.

    Returns a dict mapping (number, form) -> generated form_id.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        id_lookup = {}
        for number, name, stamina, attack, defense, form in rows:
            cursor.execute(
                "INSERT INTO pokemon (number, name, stamina, attack, defense, form) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (number, name, stamina, attack, defense, form),
            )
            id_lookup[(number, form)] = cursor.lastrowid
        conn.commit()
        return id_lookup
    finally:
        cursor.close()
        conn.close()
