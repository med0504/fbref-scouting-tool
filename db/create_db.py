import duckdb
import pandas as pd
import uuid
from datetime import datetime

def insert_dataframe(df: pd.DataFrame, table_name: str, db_path: str = "scouting.db") -> None:
    """
    Insert a DataFrame into a DuckDB table. Creates the table if it doesn't exist,
    appends data if it does.

    Args:
        df: pandas DataFrame to insert
        table_name: name of the target table
        db_path: path to the DuckDB database file
    """
    try:
        df_tracked = df.copy()
        run_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        df_tracked['run_id'] = run_id
        df_tracked['created_at'] = current_time

        con = duckdb.connect(db_path)

        table_exists = con.execute(
            f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table_name}'"
        ).fetchone()[0] > 0

        if table_exists:
            con.execute(f"INSERT INTO {table_name} SELECT * FROM df_tracked")
        else:
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_tracked")

        con.commit()
        con.close()

    except Exception as e:
        if 'con' in locals():
            con.close()
        raise Exception(f"Failed to insert data: {str(e)}")
