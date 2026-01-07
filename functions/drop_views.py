
def drop_all_views(conn_info, schema):
    import psycopg
    from psycopg import sql

    try:
        with psycopg.connect(conn_info) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT viewname
                    FROM pg_views
                    WHERE schemaname = %s;
                    """,
                    (schema,)
                )

                views = {row[0] for row in cur.fetchall()}

                for view_name in views:
                    query = sql.SQL(
                        "DROP VIEW IF EXISTS {}.{} CASCADE;"
                    ).format(
                        sql.Identifier(schema),
                        sql.Identifier(view_name)
                    )
                    cur.execute(query)
                return list(views)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()



if __name__ == "__main__":
    
    from conect_db import connect_to_db

    conn_info = connect_to_db()
    droped_views = drop_all_views(conn_info, 'public')
    for view in droped_views:
      print(f"Dropping view: {view}")
