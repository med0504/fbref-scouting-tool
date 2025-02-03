import pandas as pd
import duckdb
import uuid
from datetime import datetime

def insert_dataframe(df: pd.DataFrame, table_name: str, db_path: str = "scouting.db") -> None:
    """
    Insert a DataFrame into a DuckDB table using context manager. Creates the table if it doesn't exist,
    appends data if it does.

    Args:
        df: pandas DataFrame to insert
        table_name: name of the target table
        db_path: path to the DuckDB database file
    """
    run_id = str(uuid.uuid4())
    current_time = datetime.utcnow()
    df['run_id'] = run_id
    df['created_at'] = current_time

    try:
        with duckdb.connect(db_path) as con:
            table_exists = con.execute(
                f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table_name}'"
            ).fetchone()[0] > 0

            if table_exists:
                con.execute(f"INSERT INTO {table_name} SELECT * FROM df")
            else:
                con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

            con.commit()
    except Exception as e:
        raise Exception(f"Failed to insert data: {str(e)}")
