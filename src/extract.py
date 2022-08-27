import sqlite3
import glob
import re

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

    content_dict['source_file'] = fp.split("/")[-1]
    with open(fp, "r") as f:
        content_rows = [
            r.strip().replace(u'\xa0', u' ')
            for r in list(f.readlines())
        ]
        content_rows = [
            c for c in content_rows if len(c) > 0
        ]

    if not content_rows:
        return content_dict

    content = "\n".join(content_rows)
    recipes = extract_level(content, 1)

    all_recipes = []

    for recipe in recipes:
        recipe_content = dict()
        recipe = recipes[0]

        recipe_content['source_file'] = fp
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


def create_db(data_dir_out, dbname='recipe'):
    con = sqlite3.connect(f'{data_dir_out}/{dbname}.db')
    cur = con.cursor()
    cur.execute("""
       DROP TABLE IF EXISTS recipes;
    """)
    cur.execute("""
    CREATE TABLE recipes (
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
       DROP TABLE IF EXISTS ingredients;
    """)
    cur.execute("""
    CREATE TABLE ingredients (
       recipe_id INTEGER,
       recipe_step TEXT,
       ingredient_number INTEGER,
       ingredient TEXT NOT NULL
    );
    """)

    cur.execute("""
          DROP TABLE IF EXISTS directions;
    """)
    cur.execute("""
    CREATE TABLE directions (
       recipe_id INTEGER,
       direction_number INTEGER,
       direction TEXT NOT NULL
    );
    """)


def update_db(data_dir_out, fps, dbname='recipe'):
    # TODO: note db must exist first!
    con = sqlite3.connect(f'{data_dir_out}/{dbname}.db')
    cur = con.cursor()

    # list to hold extracted results
    rslts = []
    for fp in fps:
        rslts.extend(extract_data(fp))

    recipe_id = 0
    for recipe_dict in rslts:
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
            recipe_id += 1
        else:
            print(recipe_dict)

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
    con.close()

if __name__ == "__main__":
    from app import app
    root_dir = app.root_path + "/../"
    data_dir_in = root_dir + "/content/"
    data_dir_out = root_dir + "/data/"

    # list to hold extracted results
    rslts = []
    fps = glob.glob(f"{data_dir_in}/*.org")
    create_db(data_dir_out, dbname='recipe')
    update_db(data_dir_out, fps, dbname='recipe')
