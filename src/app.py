import os
import re
from datetime import datetime, timedelta
from flask import (
    Flask, render_template,
    request, g, send_from_directory
)
import sqlite3


# construct app and point app to useful folders
app = Flask(__name__)
app.template_folder = app.root_path + "/../templates/"
app.static_folder = app.root_path + "/../static/"
data_dir = app.root_path + "/../data/"
print(f"Using data_dir = {data_dir}")


def dict_factory(cursor, row):
    col_names = [col[0] for col in cursor.description]
    return {key: value for key, value in zip(col_names, row)}


@app.route('/recipe-icon/static/favicon.ico')
def favicon():
   return send_from_directory(app.static_folder, 'favicon.ico')


def get_db(row_factory=sqlite3.Row):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(f"{data_dir}/recipe.db")
        # use a Row factory for named access
        db.row_factory = row_factory

    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def populate_recipe_list():
    db = get_db()
    cur = db.cursor()
    query = cur.execute('''
    SELECT
       recipe_id
      ,recipe_name
    FROM recipes;
    ''')

    # get data
    rows = query.fetchall()

    # convert values
    columns = [desc[0] for desc in cur.description]
    column_vals = dict([(c, [row[c] for row in rows]) for c in columns])

    return column_vals

@app.route('/recipe-site/recipe-list.json', methods=['GET'])
def recipe_lister():
    db = get_db(row_factory=dict_factory)
    cur = db.cursor()
    query = cur.execute('''
    SELECT
       recipe_id
      ,recipe_name
    FROM recipes;
    ''')

    # get data
    rows = query.fetchall()
    return rows


@app.route('/recipe-site')
@app.route('/recipe-site/')
def recipe_site():
    recipe_data = populate_recipe_list()

    ## today's recipe
    db = get_db()
    cur = db.cursor()
    todays_date = datetime.now().strftime("%Y-%m-%d")

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
           recipe_name,
           source_url
        FROM recipes
        WHERE recipe_id = ?
        ;
        ''',
        (recipe_id,)
    )
    row = query.fetchone()
    if row:
        recipe_name = row[0]
        source_url  = row[1] if row[1] is not None else ""
    else:
        recipe_name = "???"
        source_url  = ""

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
    ingredient_rslt = dict([(c, [row[c] for row in rows]) for c in columns])

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
    direction_rslt = dict([(c, [row[c] for row in rows]) for c in columns])

    rslt = dict(
        recipe_name = recipe_name,
        ingredients = ingredient_rslt['ingredient'],
        directions = direction_rslt['direction'],
        source_url = source_url
    )

    return rslt


@app.route('/recipe-site/recipe/<recipe_id>')
def render_recipe(recipe_id):
    recipe_data = get_recipe(recipe_id)

    return render_template(
        'recipe.html',
        recipe_name=recipe_data['recipe_name'],
        ingredients=recipe_data['ingredients'],
        directions=recipe_data['directions'],
        source_url=recipe_data['source_url']
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
        recipe_ids = [rid.strip() for rid in recipe_ids.split(",")]
    else:
        recipe_ids = []

    # how much to display?
    recipe_quantities = request.args.get('recipe_quantities')
    if recipe_quantities is not None:
        recipe_quantities = [rq.strip() for rq in recipe_quantities.split(",")]
    else:
        recipe_quantities = ['1' for _ in recipe_ids]

    # filter the lists
    recipe_ids, recipe_quantities = zip(
       *((rid, amt) for rid, amt in zip(recipe_ids, recipe_quantities)
         if rid != "" and amt != "" and int(amt) > 0)
    )

    # conver to ints
    recipe_ids = [int(idx) for idx in recipe_ids]
    recipe_quantities = [int(n) for n in recipe_quantities]

    # convert to map
    recipe_amt_map = {idx: amt for (idx, amt) in zip(recipe_ids, recipe_quantities)}

    # fetch the recipes
    db = get_db()
    cur = db.cursor()
    query = cur.execute(
        f"""
            SELECT
              recipe_id,
              ingredient
            FROM ingredients
            WHERE recipe_id in ({','.join(['?']*len(recipe_ids))})
        """,
        recipe_ids
    )
    rows = query.fetchall()

    # convert values
    columns = [desc[0] for desc in cur.description]
    column_vals = dict([(c, [row[c] for row in rows]) for c in columns])

    # multiplier for each ingredient?
    ingredient_quantities = [recipe_amt_map[idx] for idx in column_vals['recipe_id']]

    return render_template(
        'grocery-list-print.html',
        # TODO: for now, send as a zip, because zips are hard(ish) with jinja
        # later, we could just render on front end instead
        ingredient_zip = zip(column_vals['ingredient'], ingredient_quantities)
    )


@app.route('/recipe-site/recipe-scheduler/', methods=['GET'])
def render_recipe_scheduler():
    return render_template(
        'recipe-scheduler.html'
    )


@app.route('/recipe-site/recipes-scheduled', methods=['GET'])
def recipes_scheduled():
    week_start = request.args.get('week-start')

    db = get_db()
    cur = db.cursor()
    cur.execute('''
        SELECT
           rs.recipe_id
          ,rs.day_of_week
          ,rs.quantity
        FROM recipe_schedule as rs
        WHERE week_start = ?
        ''',
        (week_start,)
    )
    rows = cur.fetchall()

    # convert values
    columns = [desc[0] for desc in cur.description]
    column_vals = dict([(c, [row[c] for row in rows]) for c in columns])

    return column_vals


@app.route('/recipe-site/recipe-scheduler/create-schedule', methods=['POST'])
def schedule_recipes():
    add_time = str(datetime.now())[0:23]
    week_start = request.args.get('week-start')
    days_of_week = request.args.get('weekdays-scheduled')
    recipe_ids = request.args.get('recipe-ids')
    recipe_counts = request.args.get('recipe-counts')

    print(week_start)
    print(days_of_week)
    print(recipe_ids)
    print(recipe_counts)

    try:
        recipe_ids = recipe_ids.split(",")
        recipe_ids = [int(rid) if rid.strip() else -1 for rid in recipe_ids]
    except:
        return "schedule-failure"

    try:
        recipe_counts = recipe_counts.split(",")
        recipe_counts = [int(amt) if amt.strip() else 0 for amt in recipe_counts]
    except:
        return "schedule-failure"

    try:
        days_of_week = days_of_week.split(",")
        days_of_week = [int(weekday) if weekday.strip() else -1 for weekday in days_of_week]
    except:
        return "schedule-failure"

    # delete records
    db = get_db()
    c  = db.cursor()
    query = c.execute('''
        DELETE FROM recipe_schedule
        WHERE week_start = ?
        ''',
        (week_start,)
    )

    print("HERE")
    # insert records
    #keep_days = [i for i in range(7) if recipe_ids[i] >= 0 and recipe_counts[i] != 0]
    scheduled_days = [
        (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days = i)).strftime("%Y-%m-%d")
        for i in days_of_week #keep_days
    ]
    # recipe_ids = [recipe_ids[i] for i in keep_days]
    # recipe_counts = [recipe_counts[i] for i in keep_days]
    records = [
        (week_start, scheduled_day, day_of_week, recipe_id, quantity, add_time) for
        day_of_week, scheduled_day, recipe_id, quantity
        in zip(days_of_week, scheduled_days, recipe_ids, recipe_counts)
        if quantity > 0
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

    return "schedule-success"


@app.route('/recipe-site/static/<path:path>')
def send_js(path):
    return send_from_directory(app.static_folder, path)
