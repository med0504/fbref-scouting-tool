def process_passing_df(df):
    columns = df.columns.tolist()
    columns[8] = "total_cmp"
    columns[10] = "total_Cmp%"
    df.columns = columns
    return df
