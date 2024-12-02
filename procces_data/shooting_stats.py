def process_shooting_df(df):
    shooting_df_filtered = df[df["Gls"] >= 5]
    return shooting_df_filtered
