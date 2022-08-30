from pathlib import Path
import re
import sqlite3


def extract_level(content: str, level: int):
    if level == 1:
        section_re_str = r"(?:\*\s).+?(?=\n\*\s|\Z)$"
    else:
        section_re_str = fr'^\*{{{level}}}\s.+?(?=\n\*{{1,{level}}}\s|\Z)'

    section_re = re.compile(section_re_str, re.MULTILINE|re.DOTALL)
    rslt = re.findall(section_re, content)

    return rslt


def extract_level_name(content: str, level: int):
    level_name_re = fr"(?<=\*{{{level}}}\s)(.+?)\n"
    level_name = re.findall(level_name_re, content, re.IGNORECASE)

    if level_name is None:
        return ""
    else:
        return level_name[0]


def extract_properties(content: str):
    properties = dict()

    # find property blocks
    properties_block_re = re.compile(
        r"(?<=:properties:)(.+?)(?=:end:)",
        re.IGNORECASE|re.DOTALL|re.MULTILINE
    )
    property_blocks = re.findall(properties_block_re, content)

    # extract properties
    prop_re = r":(?!properties)(?!end).+?:"

    for block in property_blocks:
        content_rows = block.split("\n")
        for row in content_rows:
            property_match = re.match(prop_re, row, re.IGNORECASE)
            if property_match:
                prop = re.sub(prop_re, '', row, re.IGNORECASE)
                prop_val = prop.strip()
                if prop:
                    prop_key = property_match[0].replace(":", "")
                    properties[prop_key] = prop_val

    return properties


def extract_ingredients(content: str):
    ingredient_re_str = r"(?:^\s*-\s)(.+?)(?=\n\s*-\s|\Z)"
    sub_sub_levels = extract_level(content, 3)

    ingredients = []
    if sub_sub_levels:
        for ssl in sub_sub_levels:
            # remove sub-sub-level from the input-content
            content = content.replace(ssl, "")
            ssl_name = extract_level_name(ssl, 3)
            ssl_ingredients = re.findall(ingredient_re_str, ssl, re.MULTILINE|re.DOTALL)
            ingredients.extend([
                (ssl_name, ingr.replace("\n", " ").replace("  ", " ")) for ingr in ssl_ingredients
            ])

    # process sub-level ingredients (not subordinate to any sub-levels)
    sl_ingredients = re.findall(ingredient_re_str, content, re.MULTILINE|re.DOTALL)
    ingredients.extend([
        (None, ingr.replace("\n", " ").replace("  ", " ")) for ingr in sl_ingredients
    ])

    return ingredients


def extract_directions(content: str):
    directions_re_str = r"(?:^\s*\d\.\s)(.+?)(?=\n\s*\d\.\s|\Z)"
    rslts = re.findall(directions_re_str, content, re.MULTILINE|re.DOTALL)

    return rslts


def extract_data(fp):
    content_dict = dict()

    fp = Path(fp)
    source_file = fp.name

    with open(fp, "r") as f:
        content_rows = [r.strip().replace(u'\xa0', u' ') \
                        for r in list(f.readlines())]
        content_rows = [c for c in content_rows if len(c) > 0]

    if not content_rows:
        return content_dict

    content = "\n".join(content_rows)
    recipes = extract_level(content, 1)

    all_recipes = []

    for recipe in recipes:
        recipe_content = dict()
        recipe = recipes[0]

        recipe_content['source_file'] = source_file

        recipe_content['title']= extract_level_name(recipe, 1)

        recipe_content.update(extract_properties(recipe))

        sub_sections = extract_level(recipe, 2)
        sub_section_names = [extract_level_name(ss, 2).lower() for ss in sub_sections]

        if 'ingredients' in sub_section_names:
            ingredients_block = sub_sections[sub_section_names.index('ingredients')]
            recipe_content['ingredients'] = extract_ingredients(ingredients_block)

        if 'directions' in sub_section_names:
            directions_block = sub_sections[sub_section_names.index('directions')]
            recipe_content['directions'] = extract_directions(directions_block)

        all_recipes.append(recipe_content)

    return all_recipes


def create_db_destructive(con):
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS recipes")
    cur.execute("DROP TABLE IF EXISTS ingredients")
    cur.execute("DROP TABLE IF EXISTS directions")
    create_db(con)

    con.commit()


def create_db(con):
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
       recipe_id INTEGER,
       recipe_step TEXT,
       ingredient_number INTEGER,
       ingredient TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS directions (
       recipe_id INTEGER,
       direction_number INTEGER,
       direction TEXT NOT NULL
    );
    """)


def update_db(con, fps):
    # TODO: note db must exist first!
    cur = con.cursor()

    # get number of existing recipes
    cur.execute("select max(recipe_id) from recipes")
    max_recipe_id = cur.fetchone()[0]
    if max_recipe_id is None:
        max_recipe_id = 0

    # list to hold existing recipes
    cur.execute("select recipe_name, source_file from recipes")
    existing_recipes = set(cur.fetchall())

    # list to hold extracted results
    extracted_recipes = []
    for fp in fps:
        extracted_recipes.extend(extract_data(fp))

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


def get_tables(con):
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    tables = [t[0] for t in tables]

    return tables


def get_columns(con, table_name):
    cur = con.cursor()
    cur.execute(f"pragma table_info('{table_name}');")
    column_metas = cur.fetchall()
    columns = [cm[1] for cm in column_metas]

    return columns


def get_tables_with_column(con, column_name):
    tables = get_tables(con)
    tables = [table for table in tables if column_name in get_columns(con, table)]

    return tables


def remove_recipe(con, recipe_id, force_remove=False):
    cur = con.cursor()
    tables_to_check = get_tables_with_column(con, 'recipe_id')
    core_tables = ['recipes', 'directions', 'ingredients']
    other_tables = [t for t in tables_to_check if not t in core_tables]

    remove_okay = True
    if not force_remove:
        for table in other_tables:
            cur.execute(f"select * from {table} where recipe_id = ?", (recipe_id,))
            rslt = cur.fetchone()

            if rslt is not None:
                remove_okay = False
                break

    if not remove_okay:
        print(f"Note: Not deleting recipe_id: {recipe_id} since it was" + \
               "used elsewhere, and force_remove = False")
    else:
        print(f"Removing {recipe_id} from core tables")
        for table in core_tables:
            cur.execute(f"delete from {table} where recipe_id = ?", (recipe_id,))
        con.commit()


if __name__ == "__main__":
    from app import app
    root_dir = Path(app.root_path)/".."
    data_dir_in  = root_dir/"content"
    data_dir_out = root_dir/"src"

    # list to hold extracted results
    rslts = []
    fps = data_dir_in.glob(f"*.org")
    con = sqlite3.connect(data_dir_out/f'recipe.db')
    create_db(con)
    update_db(con, fps)
    con.close()
