import os
import re
from datetime import datetime, timedelta
from flask import (
    Flask, render_template,
    request, g, send_from_directory
)
import sqlite3
import appdbtools as apdb


# construct app and point app to useful folders
app = Flask(__name__)
app.template_folder = app.root_path + "/../templates/"
app.static_folder = app.root_path + "/../static/"
data_dir = app.root_path + "/../data/"
print(f"Using data_dir = {data_dir}")

WEEKDAYS = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def dict_factory(cur:sqlite3.Cursor, row:sqlite3.Row):
    col_names = [col[0] for col in cur.description]

    return {key: value for key, value in zip(col_names, row)}


def get_db(row_factory=sqlite3.Row):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(f"{data_dir}/recipe.db")
        # use a Row factory for named access
        db.row_factory = row_factory

    return db


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


def get_todays_recipe_id():
    ymd_date_str = datetime.now().strftime("%Y-%m-%d")

    return get_days_recipe_id(ymd_date_str)


def get_days_recipe_id(ymd_date):
    ## today's recipe
    db = get_db()
    cur = db.cursor()

    query = cur.execute('''
        SELECT
           recipe_id
        FROM recipe_schedule
        WHERE scheduled_day = ?
        ;
        ''',
        (ymd_date,)
    )
    row = query.fetchone()
    days_recipe_id = row[0] if row else "NONE"

    return days_recipe_id


def get_current_week_start():
    """
    Return the current week's start date (Sunday) as YYYY-MM-DD.
    This matches the JavaScript getThisSunday() logic used by the scheduler.
    """
    d = datetime.utcnow().date()
    # Python weekday(): Monday=0..Sunday=6; JS getUTCDay(): Sunday=0..Saturday=6
    js_day_index = (d.weekday() + 1) % 7
    sunday = d - timedelta(days=js_day_index)
    return sunday.strftime("%Y-%m-%d")


def get_today_date():
    """
    Return today's date as YYYY-MM-DD (UTC), matching scheduled_day format.
    """
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_weekly_schedule(week_start):
    """
    Fetch the scheduled recipes for a given week_start (YYYY-MM-DD).
    """
    db = get_db(row_factory=dict_factory)
    cur = db.cursor()
    cur.execute('''
        SELECT
           rs.scheduled_day
          ,rs.recipe_id
          ,r.recipe_name
          ,rs.day_of_week
          ,rs.quantity
        FROM recipe_schedule as rs
        LEFT JOIN recipes as r
          ON rs.recipe_id = r.recipe_id
        WHERE week_start = ?
        ''',
        (week_start,)
    )
    rows = cur.fetchall()

    return rows


def get_top_scheduled_recipes(
    limit: int,
    offset: int = 0,
    sort_key: str = "times",
    sort_direction: str = "desc",
):
    """
    Return a page of the most frequently scheduled recipes.
    Aggregates over the recipe_schedule table and joins recipe names.
    """
    # Map requested sort key/direction to safe SQL fragments
    if sort_key not in {"name", "times", "last"}:
        sort_key = "times"

    sort_direction = sort_direction.lower()
    if sort_direction not in {"asc", "desc"}:
        sort_direction = "desc"

    if sort_key == "name":
        order_clause = f"r.recipe_name {sort_direction.upper()}, times_cooked DESC"
    elif sort_key == "last":
        order_clause = f"last_cooked {sort_direction.upper()}, times_cooked DESC"
    else:
        # default: sort by times cooked
        order_clause = f"times_cooked {sort_direction.upper()}, last_cooked DESC"

    db = get_db(row_factory=dict_factory)
    cur = db.cursor()
    query = f'''
        SELECT
           rs.recipe_id
          ,r.recipe_name
          ,SUM(COALESCE(rs.quantity, 1)) AS times_cooked
          ,MAX(rs.scheduled_day)         AS last_cooked
        FROM recipe_schedule AS rs
        LEFT JOIN recipes AS r
          ON rs.recipe_id = r.recipe_id
        GROUP BY rs.recipe_id, r.recipe_name
        ORDER BY {order_clause}
        LIMIT ? OFFSET ?
    '''
    cur.execute(query, (limit, offset))
    rows = cur.fetchall()

    return rows


def get_scheduled_recipe_count() -> int:
    """
    Return the total number of distinct recipes that have ever been scheduled.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute(
        '''
        SELECT COUNT(DISTINCT recipe_id) AS total_recipes
        FROM recipe_schedule
        '''
    )
    row = cur.fetchone()
    total = row[0] if row and row[0] is not None else 0
    return total


@app.route('/recipe-icon/static/favicon.ico')
def favicon():
   return send_from_directory(app.static_folder, 'favicon.ico')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/recipe-site/recipe-search', methods=['GET'])
def recipe_search():
    search_terms = request.args.get('search-terms')
    search_terms = search_terms.split(" ")

    db = get_db(row_factory=dict_factory)
    cur = db.cursor()
    rows, _ = apdb.search_recipe_list(cur, search_terms)

    # get data
    return rows


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
    todays_recipe_id = get_todays_recipe_id()
    week_start = get_current_week_start()
    weekly_schedule = get_weekly_schedule(week_start)
    today = get_today_date()

    return render_template(
        'index.html',
        todays_recipe_id = todays_recipe_id,
        recipe_id        = recipe_data['recipe_id'],
        recipe_name      = recipe_data['recipe_name'],
        week_start       = week_start,
        weekly_schedule  = weekly_schedule,
        weekdays         = WEEKDAYS,
        today            = today,
    )


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


@app.route('/recipe-site/top-recipes/', methods=['GET'])
def render_top_recipes():
    """
    Render a paginated table of the most frequently scheduled recipes.
    The page size defaults to 10 recipes per page.
    """
    page_param = request.args.get('page', default='1')
    per_page_param = request.args.get('per_page', default='10')
    sort_key = request.args.get('sort', default='times')
    sort_direction = request.args.get('direction', default='desc')

    try:
        page = int(page_param)
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = int(per_page_param)
    except (TypeError, ValueError):
        per_page = 10

    if page < 1:
        page = 1
    if per_page <= 0:
        per_page = 10
    elif per_page > 100:
        per_page = 100

    total_recipes = get_scheduled_recipe_count()

    if total_recipes > 0:
        total_pages = (total_recipes + per_page - 1) // per_page
        if page > total_pages:
            page = total_pages
        offset = (page - 1) * per_page
        top_recipes = get_top_scheduled_recipes(
            per_page,
            offset,
            sort_key=sort_key,
            sort_direction=sort_direction,
        )
    else:
        total_pages = 1
        top_recipes = []

    has_prev = page > 1
    has_next = total_recipes > page * per_page

    return render_template(
        'top-recipes.html',
        top_recipes=top_recipes,
        page=page,
        per_page=per_page,
        total_recipes=total_recipes,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        sort_key=sort_key,
        sort_direction=sort_direction,
    )


@app.route('/recipe-site/recipes-scheduled', methods=['GET'])
def recipes_scheduled():
    week_start = request.args.get('week-start')

    db = get_db(row_factory=dict_factory)
    cur = db.cursor()
    cur.execute('''
        SELECT
           rs.recipe_id
          ,r.recipe_name
          ,rs.day_of_week
          ,rs.quantity
        FROM recipe_schedule as rs
        LEFT JOIN recipes as r
          ON rs.recipe_id = r.recipe_id
        WHERE week_start = ?
        ''',
        (week_start,)
    )
    rows = cur.fetchall()

    return rows


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
