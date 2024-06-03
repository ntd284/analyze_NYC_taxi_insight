import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT #không cần chờ cho tới khi giao dịch hoàn thành, mới thực hiện các thao tác tiếp theo.

def create_database():
    conn=psycopg2.connect("host=localhost port=5433 dbname=postgres user=postgres password=postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname='uber_db'")
    exits = cur.fetchone()
    if not exits:
        cur.execute("CREATE DATABASE uber_db WITH ENCODING 'utf8' TEMPLATE template0 ")
    conn.close()
    conn=psycopg2.connect("host=localhost port=5433 dbname=uber_db user=postgres password=postgres")
    cur = conn.cursor()
    return cur,conn
create_database()