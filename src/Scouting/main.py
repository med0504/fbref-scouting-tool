from typing import Dict, List, Optional
from db.create_db import insert_dataframe

import pandas as pd

from analysis.player_scout import (
    analyze_progressive_midfielders,
    find_clinical_forwards,
    find_complete_midfielders,
    identify_playmakers,
    identify_pressing_midfielders,
    analyze_passing_quality
)
from load_data.fbref_read_big_stats import process_player_stats, readfromhtml_player as readfromhtml
from procces_data.passing_stats import process_passing_df
from procces_data.shooting_stats import process_shooting_df


def get_defense_statistics(
    url: Optional[str] = None,
    positions: Optional[List[str]] = None,
    min_90s=None,
    max_age=None,
) -> pd.DataFrame:
    """Load and process defensive statistics."""
    if url is None:
        url = "https://fbref.com/en/comps/Big5/defense/players/Big-5-European-Leagues-Stats"

    defense_df = readfromhtml(url)
    processed_df = process_player_stats(
        defense_df, positions=positions, min_90s=min_90s, max_age=max_age
    )
    cols = processed_df.columns.tolist()
    col_to_change = "Tkl"
    second_index = cols.index(col_to_change, cols.index(col_to_change) + 1)
    cols[second_index] = col_to_change + "_challange"
    processed_df.columns = cols

    defense_df = processed_df[processed_df["Tkl%"] >= 50.0]
    return defense_df.sort_values(by="Tkl%", ascending=False)


def get_possession_statistics(
    url: Optional[str] = None,
    positions: Optional[List[str]] = None,
    min_90s=None,
    max_age=None,
) -> pd.DataFrame:
    """Load and process possession statistics."""
    if url is None:
        url = "https://fbref.com/en/comps/Big5/possession/players/Big-5-European-Leagues-Stats"

    possession_df = readfromhtml(url)
    processed_df = process_player_stats(
        possession_df, positions=positions, min_90s=min_90s, max_age=max_age
    )
    return processed_df.sort_values("Carries", ascending=False)


def get_passing_statistics(
    url: Optional[str] = None,
    positions: Optional[List[str]] = None,
    min_90s=None,
    max_age=None,
) -> pd.DataFrame:
    """Load and process passing statistics."""
    if url is None:
        url = "https://fbref.com/en/comps/Big5/passing/players/Big-5-European-Leagues-Stats"
    passing_df = readfromhtml(url)
    processed_df = process_player_stats(
        passing_df, positions=positions, min_90s=min_90s, max_age=max_age
    )
    passing_stats = process_passing_df(processed_df)
    return passing_stats.sort_values("total_Cmp%", ascending=False)


def get_shooting_statistics(
    url: Optional[str] = None,
    positions: Optional[List[str]] = None,
    min_90s=None,
    max_age=None,
) -> pd.DataFrame:
    """Load and process shooting statistics."""
    if url is None:
        url = "https://fbref.com/en/comps/Big5/shooting/players/Big-5-European-Leagues-Stats"

    shooting_df = readfromhtml(url)
    processed_df = process_player_stats(
        shooting_df, positions=positions, min_90s=min_90s, max_age=max_age
    )
    shooting_stats = process_shooting_df(processed_df)
    return shooting_stats.sort_values("npxG", ascending=False)


def get_shot_creation_statistics(
    url: Optional[str] = None,
    positions: Optional[List[str]] = None,
    min_90s=None,
    max_age=None,
) -> pd.DataFrame:
    """Load and process shot creation statistics."""
    if url is None:
        url = "https://fbref.com/en/comps/Big5/gca/players/Big-5-European-Leagues-Stats"

    goal_n_shots = readfromhtml(url)
    goal_n_shots_df = process_player_stats(
        goal_n_shots, positions=positions, min_90s=min_90s, max_age=max_age
    )
    return goal_n_shots_df.sort_values("SCA", ascending=False)


def analyze_players(
    min_shots: int = 20,
    top_n: int = 20,
    positions: List[str] = ["MF,FW", "MF", "FW, MF", "MF,DF"],
    min_90s: int = 10,
    max_age: int = 25,
) -> Dict[str, pd.DataFrame]:
    """
    Comprehensive player analysis combining all statistics and analysis methods.

    Parameters:
    -----------
    min_90s: float
        Minimum number of 90-minute periods played
    min_shots: int
        Minimum number of shots for forward analysis
    top_n: int
        Number of top players to return in each category

    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary containing different analysis results
    """

    params = locals()

    passing_stats = get_passing_statistics(
        positions=positions, min_90s=min_90s, max_age=max_age
    )
    shooting_stats = get_shooting_statistics(
        positions=positions, min_90s=min_90s, max_age=max_age
    )
    possession_stats = get_possession_statistics(
        positions=positions, min_90s=min_90s, max_age=max_age
    )
    defensive_stats = get_defense_statistics(
        positions=positions, min_90s=min_90s, max_age=max_age
    )
    shot_creation_stats = get_shot_creation_statistics(
        positions=positions, min_90s=min_90s, max_age=max_age
    )


    results = {}


    results["top_passers"] = passing_stats.head(top_n)
    results["top_shooters"] = shooting_stats.head(top_n)
    results["top_creators"] = shot_creation_stats.head(top_n)


    results["playmakers"] = identify_playmakers(passing_stats).head(top_n)

    results["clinical_forwards"] = find_clinical_forwards(
        shooting_stats, min_shots=min_shots
    ).head(top_n)

    results["progressive_midfielders"] = analyze_progressive_midfielders(
        possession_stats
    ).head(top_n)

    results["pressing_midfielders"] = identify_pressing_midfielders(
        defensive_stats
    ).head(top_n)

    results["passing_quailty"] = analyze_passing_quality(passing_stats).head(top_n)

    results["complete_midfielders"] = find_complete_midfielders(
        passing_stats, possession_stats, defensive_stats
    ).head(top_n)

    results["parameters"] = pd.DataFrame(params)
    return results


def generate_analysis_report(results: Dict[str, pd.DataFrame]) -> str:
    """
    Generate a formatted report from the analysis results.

    Parameters:
    -----------
    results: Dict[str, pd.DataFrame]
        Analysis results from analyze_players function

    """
    report = []
    for category, df in results.items():
        if category != "parameters":
            report.append(f"## {category.replace('_', ' ').title()}")
            report.append("\n")
            report.append(df[["Player", "Squad", "Age", "Pos"]].to_markdown())
            report.append("\n")
            return "\n".join(report)


if __name__ == "__main__":
    # Perform comprehensive analysis
    results = analyze_players(
        min_shots=20,
        top_n=20,
        positions=["MF", "FW, MF", "MF,DF"],
        min_90s=5,
        max_age=30,
    )

    # Generate and print report
    report = generate_analysis_report(results)

    for k, v in results.items():
        insert_dataframe(v, k)



    print(
        results["passing_quailty"].head(20)
    )
