from flask import (
    Flask, render_template,
    request, g, jsonify, url_for,
    send_from_directory
)
import sqlite3
from datetime import datetime, timedelta
import os


# construct app and point app to useful folders
app = Flask(__name__)
app.template_folder = app.root_path + "/../templates/"
app.static_folder = app.root_path + "/../static/"
data_dir = app.root_path + "/../data/"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/png')

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

    ## today's recipe
    db = get_db()
    cur = db.cursor()
    todays_date=datetime.now().strftime("%Y-%m-%d")

    ## Get the Ingredients
    query = cur.execute('''
        SELECT
           recipe_id
        FROM recipe_schedule
        WHERE scheduled_day = ?
        ;
        ''',
        (todays_date,)
    )
    row = query.fetchone()
    todays_recipe_id = row[0] if row else "NONE"

    return render_template(
        'index.html',
        todays_recipe_id = todays_recipe_id,
        recipe_id        = recipe_data['recipe_id'],
        recipe_name      = recipe_data['recipe_name']
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
    # which recipes to display?
    recipe_ids = request.args.get('recipe_ids')
    if recipe_ids is not None:
        recipe_ids = [idx.strip() for idx in recipe_ids.split(",")]
    else:
        recipe_ids = []

    # how much to display?
    recipe_quantities = request.args.get('recipe_quantities')
    if recipe_quantities is not None:
        recipe_quantities.split(",")
    else:
        recipe_quantities = [1 for idx in recipe_ids if idx.strip() != ""]

    # fetch the recipes
    db = get_db()
    c  = db.cursor()
    query = c.execute(
        f"""
            SELECT
              ingredient
            FROM ingredients
            WHERE recipe_id in ({','.join(['?']*len(recipe_ids))})
        """,
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
        ingredient_list = column_vals['ingredient'],
        ingredient_quantities = recipe_quantities
    )

@app.route('/recipe-site/recipe-scheduler/', methods=['GET'])
def render_recipe_scheduler():
    week_start = request.args.get('week-start')
    recipe_data = populate_recipe_list()

    db = get_db()
    c  = db.cursor()
    query = c.execute('''
        SELECT
           rs.recipe_id
          ,rs.day_of_week
          ,rs.quantity
        FROM recipe_schedule as rs
        WHERE week_start = ?
        ''',
        (week_start,)
    )
    rows = c.fetchall()

    # convert values
    columns = [desc[0] for desc in c.description]
    column_vals = dict([(c, []) for c in columns])

    for row in rows:
        for i, c in enumerate(columns):
            column_vals[c].append(row[i])

    print(column_vals)

    return render_template(
        'recipe-scheduler.html',
        week_start=datetime.strptime(week_start, "%Y-%m-%d").strftime("%Y-%m-%d"),
        recipe_id=recipe_data['recipe_id'],
        recipe_name=recipe_data['recipe_name'],
        scheduled_recipe_ids = column_vals['recipe_id'],
        scheduled_day_of_week = column_vals['day_of_week'],
        scheduled_quantities = column_vals['quantity']
    )


@app.route('/recipe-site/recipe-scheduler/create-schedule', methods=['POST'])
def schedule_recipes():
    add_time = str(datetime.now())[0:23]
    week_start = request.args.get('week-start')
    recipe_ids = request.args.get('recipe-ids')
    recipe_counts = request.args.get('recipe-counts')

    try:
        recipe_ids = recipe_ids.split(",")
        recipe_ids = [int(rid) if rid.strip() else -1 for rid in recipe_ids]
    except:
        print("FAILURE")
        return "FAILED"

    try:
        recipe_counts = recipe_counts.split(",")
        recipe_counts = [int(amt) if amt.strip() else 0 for amt in recipe_counts]
    except:
        return "FAILED"

    # delete records
    db = get_db()
    c  = db.cursor()
    query = c.execute('''
        DELETE FROM recipe_schedule
        WHERE week_start = ?
        ''',
        (week_start,)
    )
    db.commit()

    # insert records
    keep_days = [i for i in range(7) if recipe_ids[i] >= 0 and recipe_counts[i] != 0]
    scheduled_days = [
        (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days = i)).strftime("%Y-%m-%d")
        for i in keep_days
    ]
    recipe_ids = [recipe_ids[i] for i in keep_days]
    recipe_counts = [recipe_counts[i] for i in keep_days]
    records = [
        (week_start, scheduled_day, day_of_week, recipe_id, quantity, add_time) for
        day_of_week, scheduled_day, recipe_id, quantity
        in zip(keep_days, scheduled_days, recipe_ids, recipe_counts)
    ]
    print(records)
    query = c.executemany('''
        INSERT INTO
        recipe_schedule (
             week_start
           , scheduled_day
           , day_of_week
           , recipe_id
           , quantity
           , added_datetime
        )
        VALUES (?,?,?,?,?,?)
        ''',
        records
    )
    db.commit()

    return "success"

@app.route('/recipe-site/static/<path:path>')
def send_js(path):
    return send_from_directory(app.static_folder, path)
