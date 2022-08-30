import sqlite3


def create_recipe_table(con):
    cur = con.cursor()
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
    con.commit()


def create_ingredient_table(con):
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
       recipe_id INTEGER,
       recipe_step TEXT,
       ingredient_number INTEGER,
       ingredient TEXT NOT NULL
    );
    """)
    con.commit()

def create_direction_table(con):
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS directions (
       recipe_id INTEGER,
       direction_number INTEGER,
       direction TEXT NOT NULL
    );
    """)
    con.commit()


def create_recipe_schedule_table(con):
    cur = con.cursor()
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
    con.commit()


def create_db(con):
    cur = con.cursor()

    create_recipe_table(con)
    create_ingredient_table(con)
    create_direction_table(con)
    create_recipe_schedule_table(con)

    con.commit()


def create_db_destructive(con):
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS recipes")
    cur.execute("DROP TABLE IF EXISTS ingredients")
    cur.execute("DROP TABLE IF EXISTS directions")
    create_db(con)

    con.commit()


def update_db(con, extracted_recipes):
    cur = con.cursor()

    # get number of existing recipes
    cur.execute("select max(recipe_id) from recipes")
    max_recipe_id = cur.fetchone()[0]
    if max_recipe_id is None:
        max_recipe_id = 0

    # list to hold existing recipes
    cur.execute("select recipe_name, source_file from recipes")
    existing_recipes = set(cur.fetchall())


    # list to hold new recipes
    new_recipes = [
        recipe_dict for recipe_dict in extracted_recipes if
        (recipe_dict['title'], recipe_dict['source_file'])
        not in existing_recipes
    ]

    for recipe_dict in new_recipes:
        # message
        print(f"Inserting {recipe_dict['title']}")

        # add some missing keys
        for k in ['prep-time', 'cook-time', 'servings', 'source-url']:
            if not k in recipe_dict:
                recipe_dict[k] = None

        # only create
        if 'title' in recipe_dict.keys():
            cur.execute(
                "INSERT INTO recipes (recipe_name, prep_time, cook_time, servings, source_url, source_file) VALUES (?,?,?,?,?,?)",
                (recipe_dict['title'], recipe_dict['prep-time'], recipe_dict['cook-time'],
                 recipe_dict['servings'], recipe_dict['source-url'], recipe_dict['source_file'])
            )

            # get the assigned id - take max just in case
            cur.execute(
                "select max(recipe_id) from recipes where recipe_name = ? and source_file = ?",
                (recipe_dict['title'], recipe_dict['source_file'])
            )
            recipe_id = cur.fetchone()[0]

        else:
            print(recipe_dict)
            break

        if 'ingredients' in recipe_dict.keys():
            ingredient_list = recipe_dict['ingredients']
            n_ingredients = len(ingredient_list)
            records = [(recipe_id, recipe_step, i, ingredient) for i, (recipe_step, ingredient) in enumerate(ingredient_list)]

            cur.executemany(
                "INSERT INTO ingredients (recipe_id, recipe_step, ingredient_number, ingredient) VALUES (?,?,?,?)",
                records
            )

        if 'directions' in recipe_dict.keys():
            direction_list = recipe_dict['directions']
            n_directions = len(direction_list)
            records = [(recipe_id, i, direction) for i, direction in enumerate(direction_list)]

            cur.executemany(
                "INSERT INTO directions (recipe_id, direction_number, direction) VALUES (?,?,?)",
                records
            )

    con.commit()


if __name__ == "__main__":
    from pathlib import Path
    from app import app

    root_dir = Path(app.root_path)/".."
    data_dir_in  = root_dir/"content"
    data_dir_out = root_dir/"data"
    con = sqlite3.connect(data_dir_out/f'recipe.db')
    create_db(con)
