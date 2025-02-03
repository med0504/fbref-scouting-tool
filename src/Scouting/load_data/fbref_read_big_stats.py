import pandas as pd


def readfromhtml_player(filepath):
    """
    x = readfromhtml(
        "https://fbref.com/en/comps/Big5/shooting/players/Big-5-European-Leagues-Stats"
    )
    """
    df = pd.read_html(filepath)[0]
    column_lst = list(df.columns)
    for index in range(len(column_lst)):
        column_lst[index] = column_lst[index][1]

    df.columns = column_lst
    df.drop(df[df["Player"] == "Player"].index, inplace=True)
    df = df.fillna("0")
    df.set_index("Rk", drop=True, inplace=True)
    try:
        df["Comp"] = df["Comp"].apply(lambda x: " ".join(x.split()[1:]))
        df["Nation"] = df["Nation"].astype(str)
        df["Nation"] = df["Nation"].apply(lambda x: x.split()[-1])
    except ValueError:
        print("Error in uploading file:" + filepath)
    finally:
        df = df.apply(pd.to_numeric, errors="ignore")
        return df


def process_player_stats(df, min_90s, max_age, positions):
    """
    Process player statistics dataframe with filtering and column renaming.

    Args:
        df: Input dataframe from fbref
        min_90s: Minimum number of 90-minute periods played
        max_age: Maximum player age to include
        positions: List of positions to filter for

    Returns:
        Processed dataframe
    """

    filtered_df = df[df["Pos"].apply(lambda x: x in positions)]
    filtered_df["Age"] = filtered_df["Age"].str.split("-").str[0].astype(int)
    filtered_df = filtered_df[filtered_df["Age"] <= max_age]
    filtered_df = filtered_df[filtered_df["90s"] >= min_90s]

    return filtered_df
