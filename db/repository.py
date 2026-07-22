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
