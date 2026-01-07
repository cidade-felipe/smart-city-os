def drop_all_triggers(conn_info, schema):
    import psycopg
    from psycopg import sql

    try:
        with psycopg.connect(conn_info) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT triggername
                    FROM pg_trigger
                    WHERE schemaname = %s;
                    """,
                    (schema,)
                )

                triggers = {row['triggername'] for row in cur.fetchall()}

                for trigger_name in triggers:
                    query = sql.SQL(
                        "DROP TRIGGER IF EXISTS {}.{} CASCADE;"
                    ).format(
                        sql.Identifier(schema),
                        sql.Identifier(trigger_name)
                    )
                    cur.execute(query)
                return list(triggers)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    from conect_db import connect_to_db
    conn_info = connect_to_db()
    droped_triggers = drop_all_triggers(conn_info, 'public')
    for trigger in droped_triggers:
      print(f"Dropping trigger: {trigger}")