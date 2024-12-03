from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def normalize_metric(series: pd.Series) -> pd.Series:
    """Normalize a metric to 0-1 scale using robust scaling."""
    min_val = series.quantile(0.05)  # Use 5th percentile instead of minimum
    max_val = series.quantile(0.95)  # Use 95th percentile instead of maximum
    return (series - min_val) / (max_val - min_val)


def identify_playmakers(passing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify creative midfielders based on progressive passing and creation metrics.

    Parameters:
    -----------
    passing_df: pd.DataFrame
        DataFrame containing passing statistics
    min_age: int
        Minimum age to consider
    max_age: int
        Maximum age to consider
    """
    playmaker_metrics = passing_df.copy()


    playmaker_metrics["PrgP_90"] = playmaker_metrics["PrgP"] / playmaker_metrics["90s"]
    playmaker_metrics["KP_90"] = playmaker_metrics["KP"] / playmaker_metrics["90s"]
    playmaker_metrics["Ast_90"] = playmaker_metrics["Ast"] / playmaker_metrics["90s"]


    metrics_to_normalize = ["PrgP_90", "KP_90", "Ast_90", "total_Cmp%"]
    for metric in metrics_to_normalize:
        playmaker_metrics[f"{metric}_norm"] = normalize_metric(
            playmaker_metrics[metric]
        )

    weights = {
        "PrgP_90_norm": 0.35,
        "KP_90_norm": 0.30,
        "total_Cmp%_norm": 0.20,
        "Ast_90_norm": 0.15,
    }

    playmaker_metrics["playmaker_score"] = sum(
        playmaker_metrics[metric] * weight for metric, weight in weights.items()
    )

    return playmaker_metrics.sort_values("playmaker_score", ascending=False)


def find_clinical_forwards(
    shooting_df: pd.DataFrame,
    min_shots: int = 20,
) -> pd.DataFrame:
    """
    Identify efficient forwards based on shooting and conversion metrics.

    Parameters:
    -----------
    shooting_df: pd.DataFrame
        DataFrame containing shooting statistics
    min_shots: int
        Minimum number of shots taken
    """
    shooting_analysis = shooting_df[(shooting_df["Sh"] >= min_shots)].copy()

    shooting_analysis["Sh_90"] = shooting_analysis["Sh"] / shooting_analysis["90s"]
    shooting_analysis["Gls_90"] = shooting_analysis["Gls"] / shooting_analysis["90s"]
    shooting_analysis["conversion_rate"] = (
        shooting_analysis["Gls"] / shooting_analysis["Sh"]
    )
    shooting_analysis["xG_difference"] = (
        shooting_analysis["Gls"] - shooting_analysis["xG"]
    )

    metrics_to_normalize = ["conversion_rate", "SoT%", "xG_difference", "Gls_90"]
    for metric in metrics_to_normalize:
        shooting_analysis[f"{metric}_norm"] = normalize_metric(
            shooting_analysis[metric]
        )

    weights = {
        "conversion_rate_norm": 0.30,
        "SoT%_norm": 0.25,
        "xG_difference_norm": 0.25,
        "Gls_90_norm": 0.20,
    }

    shooting_analysis["efficiency_score"] = sum(
        shooting_analysis[metric] * weight for metric, weight in weights.items()
    )

    return shooting_analysis.sort_values("efficiency_score", ascending=False)


def analyze_progressive_midfielders(possession_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify midfielders who excel at moving the ball forward.

    Parameters:
    -----------
    possession_df: pd.DataFrame
        DataFrame containing possession statistics
    """
    midfield_metrics = possession_df.copy()

    per_90_metrics = ["PrgDist", "PrgC", "1/3", "PrgR"]
    for metric in per_90_metrics:
        midfield_metrics[f"{metric}_90"] = (
            midfield_metrics[metric] / midfield_metrics["90s"]
        )
        midfield_metrics[f"{metric}_norm"] = normalize_metric(
            midfield_metrics[f"{metric}_90"]
        )

    weights = {
        "PrgDist_norm": 0.35,
        "PrgC_norm": 0.30,
        "1/3_norm": 0.20,
        "PrgR_norm": 0.15,
    }

    midfield_metrics["progression_score"] = sum(
        midfield_metrics[metric] * weight for metric, weight in weights.items()
    )

    return midfield_metrics.sort_values("progression_score", ascending=False)


def identify_pressing_midfielders(defensive_df: pd.DataFrame) -> pd.DataFrame:
    """
    Find midfielders who excel in pressing and defensive actions.

    Parameters:
    -----------
    defensive_df: pd.DataFrame
        DataFrame containing defensive statistics
    """
    defensive_mids = defensive_df[
        (defensive_df["Pos"].str.contains("MF", na=False))
    ].copy()

    defensive_mids["Tkl_90"] = defensive_mids["Tkl"] / defensive_mids["90s"]
    defensive_mids["Int_90"] = defensive_mids["Int"] / defensive_mids["90s"]
    defensive_mids["Att3rd_90"] = defensive_mids["Att 3rd"] / defensive_mids["90s"]

    metrics_to_normalize = ["Tkl_90", "Int_90", "Tkl%", "Att3rd_90"]
    for metric in metrics_to_normalize:
        defensive_mids[f"{metric}_norm"] = normalize_metric(defensive_mids[metric])

    weights = {
        "Tkl_90_norm": 0.35,
        "Int_90_norm": 0.30,
        "Tkl%_norm": 0.20,
        "Att3rd_90_norm": 0.15,
    }

    defensive_mids["pressing_score"] = sum(
        defensive_mids[metric] * weight for metric, weight in weights.items()
    )

    return defensive_mids.sort_values("pressing_score", ascending=False)


def find_complete_midfielders(
    passing_df: pd.DataFrame,
    possession_df: pd.DataFrame,
    defensive_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identify well-rounded midfielders who contribute in multiple areas.

    Parameters:
    -----------
    passing_df: pd.DataFrame
        DataFrame containing passing statistics
    possession_df: pd.DataFrame
        DataFrame containing possession statistics
    defensive_df: pd.DataFrame
        DataFrame containing defensive statistics
    """
    progressive = analyze_progressive_midfielders(possession_df)
    defensive = identify_pressing_midfielders(defensive_df)
    playmaking = identify_playmakers(passing_df)

    complete_score = progressive[
        ["Player", "Squad", "Age", "Pos", "progression_score"]
    ].copy()
    complete_score = complete_score.merge(
        defensive[["Player", "pressing_score"]], on="Player", how="inner"
    )
    complete_score = complete_score.merge(
        playmaking[["Player", "playmaker_score"]], on="Player", how="inner"
    )

    for col in ["progression_score", "pressing_score", "playmaker_score"]:
        complete_score[f"{col}_norm"] = normalize_metric(complete_score[col])

    weights = {
        "progression_score_norm": 0.40,
        "pressing_score_norm": 0.30,
        "playmaker_score_norm": 0.30,
    }

    complete_score["complete_midfielder_score"] = sum(
        complete_score[metric] * weight for metric, weight in weights.items()
    )

    return complete_score.sort_values("complete_midfielder_score", ascending=False)


def analyze_passing_quality(df):
    """
    Analyze passing quality and chance creation for players

    Parameters:
    df: DataFrame containing passing statistics
    Returns:
    DataFrame with passing quality scores and rankings
    """
    # Acoid modifying the orginal datframe
    df_filtered = df.copy()

    df_filtered['passes_per_90'] = df_filtered['total_cmp'] / df_filtered['90s']
    df_filtered['prog_passes_per_90'] = df_filtered['PrgP'] / df_filtered['90s']
    df_filtered['key_passes_per_90'] = df_filtered['KP'] / df_filtered['90s']
    df_filtered['xA_per_90'] = df_filtered['xA'] / df_filtered['90s']

    df_filtered['passing_accuracy_score'] = (
        df_filtered['total_Cmp%'] / 100 *
        np.where(df_filtered['total_cmp'] > df_filtered['total_cmp'].median(), 1.2, 1.0)
    )

    df_filtered['progression_score'] = (
        df_filtered['prog_passes_per_90'] / df_filtered['prog_passes_per_90'].max() +
        df_filtered['PrgDist'] / df_filtered['PrgDist'].max()
    ) / 2

    df_filtered['chance_creation_score'] = (
        df_filtered['key_passes_per_90'] / df_filtered['key_passes_per_90'].max() +
        df_filtered['xA_per_90'] / df_filtered['xA_per_90'].max() +
        df_filtered['PPA'] / df_filtered['PPA'].max()
    ) / 3

    df_filtered['passing_quality_score'] = (
        df_filtered['passing_accuracy_score'] * 0.3 +
        df_filtered['progression_score'] * 0.3 +
        df_filtered['chance_creation_score'] * 0.4
    )

    cols_to_round = ['passes_per_90', 'prog_passes_per_90', 'key_passes_per_90', 'xA_per_90',
                     'passing_accuracy_score', 'progression_score', 'chance_creation_score',
                     'passing_quality_score']

    df_filtered[cols_to_round] = df_filtered[cols_to_round].round(3)

    result = df_filtered.sort_values('passing_quality_score', ascending=False)

    return result[['Player', 'Squad', 'Comp', '90s',
                  'passes_per_90', 'total_Cmp%', 'prog_passes_per_90',
                  'key_passes_per_90', 'xA_per_90',
                  'passing_accuracy_score', 'progression_score', 'chance_creation_score',
                  'passing_quality_score']]
