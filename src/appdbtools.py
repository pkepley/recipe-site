import sqlite3


def search_recipe_list(cur:sqlite3.Cursor, search_terms:list[str]):
    query_str = '''
    SELECT
       recipe_id
      ,recipe_name
    FROM recipes
    '''

    # append search terms
    for (i, _) in enumerate(search_terms):
        if i == 0:
          query_str = query_str + "WHERE recipe_name LIKE ?\n"
        else:
          query_str = query_str + "  AND recipe_name LIKE ?\n"
    query_str = query_str + ";"
    print(query_str)

    # get data
    if search_terms:
        query = cur.execute(query_str, tuple(['%'+term+'%' for term in search_terms]))
    else:
        query = cur.execute(query_str)
    rows = query.fetchall()

    # get column names
    columns = [desc[0] for desc in cur.description]

    return rows, columns
