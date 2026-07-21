import pytest

from db.connection import get_connection


@pytest.mark.integration
def test_get_connection_returns_live_connection():
    conn = get_connection()
    try:
        assert conn.is_connected()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
        cursor.close()
    finally:
        conn.close()
