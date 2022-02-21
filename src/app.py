from glob import glob
from flask import (
    Flask, render_template, escape,
    request, g, jsonify, url_for,
    send_from_directory
)
import sqlite3
from markupsafe import escape
import os


# construct app and point app to useful folders
app = Flask(__name__)
app.template_folder = app.root_path + "/../templates/"
app.static_folder = app.root_path + "/../static/"
data_dir = app.root_path + "/../data/"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(f"{data_dir}/recipe.db")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def populate_recipe_list():
    db = get_db()
    c  = db.cursor()
    query = c.execute('''
    SELECT
       recipe_id
      ,recipe_name
    FROM recipes;
    ''')

    rows = query.fetchall()

    # convert values
    columns = [desc[0] for desc in c.description]
    column_vals = dict([(c, []) for c in columns])

    for row in rows:
        for i, c in enumerate(columns):
            column_vals[c].append(row[i])

    return column_vals


@app.route('/recipe-site')
@app.route('/recipe-site/')
def recipe_site():
    recipe_data = populate_recipe_list()

    return render_template(
        'index.html',
        recipe_id=recipe_data['recipe_id'],
        recipe_name=recipe_data['recipe_name']
    )

def get_recipe(recipe_id):
    db = get_db()
    cur = db.cursor()

    ## Get the Ingredients
    query = cur.execute('''
        SELECT
           recipe_name
        FROM recipes
        WHERE recipe_id = ?
        ;
        ''',
        (recipe_id,)
    )
    row = query.fetchone()
    if row:
        recipe_name = row[0]
    else:
        recipe_name = "???"

    ## Get the Ingredients
    query = cur.execute('''
        SELECT
           ingredient
        FROM ingredients
        WHERE recipe_id = ?
        ORDER BY ingredient_number
        ;
        ''',
        (recipe_id,)
    )
    rows = query.fetchall()

    # convert values
    columns = [desc[0] for desc in cur.description]
    ingredient_rslt = dict([(c, []) for c in columns])

    for row in rows:
        for i, column in enumerate(columns):
            ingredient_rslt[column].append(row[i])


    ## Get the Directions
    query = cur.execute('''
        SELECT
           direction
        FROM directions
        WHERE recipe_id = ?
        ORDER BY direction_number
        ;
        ''',
        (recipe_id,)
    )
    rows = query.fetchall()

    # convert values
    columns = [desc[0] for desc in cur.description]
    direction_rslt = dict([(column, []) for column in columns])

    for row in rows:
        for i, column in enumerate(columns):
            direction_rslt[column].append(row[i])

    rslt = dict(
        recipe_name = recipe_name,
        ingredients = ingredient_rslt['ingredient'],
        directions = direction_rslt['direction']
    )

    return rslt

@app.route('/recipe-site/recipe/<recipe_id>')
def render_recipe(recipe_id):
    recipe_data = get_recipe(recipe_id)

    return render_template(
        'recipe.html',
        recipe_name =recipe_data['recipe_name'],
        ingredients =recipe_data['ingredients'],
        directions  =recipe_data['directions']
    )

@app.route('/recipe-site/grocery-list/')
def render_grocery():
    recipe_data = populate_recipe_list()

    return render_template(
        'grocery-list.html',
        recipe_id=recipe_data['recipe_id'],
        recipe_name=recipe_data['recipe_name']
    )

@app.route('/recipe-site/grocery-list-print/', methods=['GET'])
def render_grocery_print():
    recipe_ids = request.args.get('recipe_ids').split(",")
    qq = f"SELECT ingredient FROM ingredients WHERE recipe_id in ({','.join(['?']*len(recipe_ids))})"

    db = get_db()
    c  = db.cursor()
    query = c.execute(
        f"SELECT ingredient FROM ingredients WHERE recipe_id in ({','.join(['?']*len(recipe_ids))})",
        recipe_ids
    )
    rows = query.fetchall()

    # convert values
    columns = [desc[0] for desc in c.description]
    column_vals = dict([(c, []) for c in columns])

    for row in rows:
        for i, c in enumerate(columns):
            column_vals[c].append(row[i])

    return render_template(
        'grocery-list-print.html',
        ingredient_list = column_vals['ingredient']
    )

@app.route('/recipe-site/static/<path:path>')
def send_js(path):
    return send_from_directory(app.static_folder, path)
