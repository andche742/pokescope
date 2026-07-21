from collections import namedtuple

from db.connection import get_connection


def get_pokemon(id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, number, name, hp AS stamina, attack, defense, form "
            "FROM pokemon WHERE id = %s",
            (id,),
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
        return row[0] if row else None
    finally:
        cursor.close()
        conn.close()


def get_cpm_table():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT level, value FROM cpm ORDER BY level ASC")
        rows = cursor.fetchall()
        return [row[0] for row in rows], [row[1] for row in rows]
    finally:
        cursor.close()
        conn.close()
