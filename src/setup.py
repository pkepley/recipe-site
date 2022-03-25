import sqlite3

def create_recipe_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
       recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
       recipe_name TEXT NOT NULL,
       prep_time TEXT,
       cook_time TEXT,
       servings  TEXT,
       source_url TEXT,
       source_file TEXT NOT NULL
    );
    """)
    conn.commit()

def create_ingredient_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
       recipe_id INTEGER,
       recipe_step TEXT,
       ingredient_number INTEGER,
       ingredient TEXT NOT NULL
    );
    """)
    conn.commit()

def create_direction_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS directions (
       recipe_id INTEGER,
       direction_number INTEGER,
       direction TEXT NOT NULL
    );
    """)
    conn.commit()

def create_recipe_schedule_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipe_schedule (
       week_start TEXT NOT NULL,
       scheduled_day TEXT NOT NULL,
       day_of_week INTEGER NOT NULL,
       recipe_id INTEGER NOT NULL,
       quantity INTEGER DEFAULT 1 NOT NULL,
       added_datetime TEXT NOT NULL
    );
    """)
    conn.commit()

if __name__ == "__main__":
    from app import app
    root_dir = app.root_path + "/../"
    data_dir_in = root_dir + "/content/"
    data_dir_out = root_dir + "/data/"

    # open connection
    conn = sqlite3.connect(f'{data_dir_out}/recipe.db')

    # create tables
    create_recipe_table(conn)
    create_ingredient_table(conn)
    create_direction_table(conn)
    create_recipe_schedule_table(conn)

    # close connection
    conn.close()
