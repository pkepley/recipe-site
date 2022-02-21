import sqlite3
import os
import glob
import re


def extract_data(fp):
    with open(fp, "r") as f:
        contents = [
            r.strip().replace(u'\xa0', u' ')
            for r in list(f.readlines())
        ]
        contents = [
            c for c in contents if len(c) > 0
        ]

    content_dict = dict()
    content_curr = []
    sub_section_key = None
    sub_sub_section_key = None

    content_dict['source_file'] = fp.split("/")[-1]

    for row in contents:
        split_row = row.split(" ")

        property_match = re.match(":.+?:", row)
        if property_match:
            prop = property_match.group(0).lower()
            prop_val = row.replace(prop, "")
            if prop != ':properties:' and prop != ':end:' and prop_val:
                content_dict[prop.replace(":", "")] = prop_val
                print(prop.replace(":", ""), "|", prop_val)

        if "*" in split_row:
            content_dict['title'] = (" ".join(split_row[1:])).strip()

        if "**" in split_row:
            # clear out last round
            if sub_section_key is not None:
                # get rid of beginning of line characters
                if sub_section_key == "directions":
                    content_curr = [
                        re.sub("^\d+\. ", "", a.strip()) for a in content_curr
                    ]

                content_dict[sub_section_key] = (
                    [a for a in content_curr if len(a) > 0]
                )

            # set-up next round
            sub_section_key = " ".join(split_row[1:]).lower()
            sub_sub_section_key = None
            content_curr = []

        else:
            if "***" in split_row:
                sub_sub_section_key = " ".join(split_row[1:]).lower()

            elif sub_section_key == 'ingredients':
                if row.strip():
                    curr_ingredient = row.strip().replace("- ", "").strip()
                    content_curr.append((sub_sub_section_key, curr_ingredient))

            elif sub_section_key == 'directions':
                if row.strip():
                    row_split = row.split(".")
                    if row_split[0] == str(len(content_curr) + 1):
                        content_curr.append(row)
                    else:
                        content_curr[-1] = content_curr[-1] + row

            elif sub_section_key is not None:
                #print(content_dict['title'], " ", k)
                pass

    if sub_section_key is not None:
        # get rid of beginning of line characters
        if sub_section_key == "directions":
            content_curr = [
                re.sub("^\d+\. ", "", a.strip()) for a in content_curr
            ]
        content_dict[sub_section_key] = (
            [a for a in content_curr if len(a) > 0]
        )

    return content_dict


if __name__ == "__main__":
    rslts = []
    for fp in glob.glob("./content/*.org"):
        rslts.append(extract_data(fp))

    con = sqlite3.connect('recipe.db')
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
