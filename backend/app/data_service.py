from __future__ import annotations

import csv
import base64
import io
import re
import threading
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px


EXPECTED_COLUMNS = {
    "matches": {
        "season", "team1", "team2", "winner", "venue",
        "toss_winner", "toss_decision", "match_id",
    },
    "deliveries": {
        "match_id", "batter", "batsman_runs", "bowler",
        "is_wicket", "dismissal_kind",
    },
}

ALIASES = {
    "batsman": "batter",
    "batter_name": "batter",
    "bowler_name": "bowler",
    "batsman_run": "batsman_runs",
    "batter_runs": "batsman_runs",
    "runs_off_bat": "batsman_runs",
    "matchid": "match_id",
    "id": "match_id",
}

NON_BOWLER_DISMISSALS = {
    "handled the ball",
    "hit the ball twice",
    "obstructing the field",
    "retired hurt",
    "retired not out",
    "retired out",
    "run out",
    "timed out",
}

TEAM_COLUMNS = ("team1", "team2")


class CsvValidationError(ValueError):
    """Raised when an uploaded CSV cannot be used safely."""


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = _normalized_column_names(frame.columns)
    duplicates = sorted({name for name in normalized if normalized.count(name) > 1})
    if duplicates:
        raise CsvValidationError(
            "Column names are duplicated after normalization: "
            + ", ".join(duplicates)
        )
    result = frame.copy()
    result.columns = normalized
    if not normalized or any(not name for name in normalized):
        raise CsvValidationError("The CSV must contain non-empty column names.")
    return result


def _normalized_column_names(columns: Any) -> list[str]:
    normalized: list[str] = []
    for column in columns:
        name = re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        normalized.append(ALIASES.get(name, name))
    return normalized


def parse_csv(contents: bytes, dataset: str) -> pd.DataFrame:
    if not contents:
        raise CsvValidationError("The uploaded file is empty.")
    try:
        header = next(csv.reader(io.StringIO(contents.decode("utf-8-sig"))))
        normalized_header = _normalized_column_names(header)
        if not normalized_header or any(not name for name in normalized_header):
            raise CsvValidationError("The CSV must contain non-empty column names.")
        duplicate_headers = sorted(
            {name for name in normalized_header if normalized_header.count(name) > 1}
        )
        if duplicate_headers:
            raise CsvValidationError(
                "Column names are duplicated after normalization: "
                + ", ".join(duplicate_headers)
            )
        frame = pd.read_csv(io.BytesIO(contents), encoding="utf-8-sig", low_memory=False)
    except StopIteration as error:
        raise CsvValidationError("The CSV must contain a header row.") from error
    except (csv.Error, pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        raise CsvValidationError(f"Could not parse the CSV: {error}") from error

    frame = normalize_columns(frame)
    if frame.empty:
        raise CsvValidationError("The CSV contains column headers but no data rows.")
    if dataset not in EXPECTED_COLUMNS:
        raise CsvValidationError("Unknown dataset type.")
    if not EXPECTED_COLUMNS[dataset].intersection(frame.columns):
        raise CsvValidationError(
            f"The CSV does not contain any recognized {dataset} columns."
        )
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        values = frame[column].str.strip()
        frame[column] = values.mask(values.eq(""), pd.NA)
    return frame


def _clean_values(series: pd.Series) -> pd.Series:
    return series.dropna().astype(str).str.strip().loc[lambda values: values.ne("")]


def _filter_matches(
    matches: pd.DataFrame | None,
    seasons: list[str] | None = None,
    teams: list[str] | None = None,
) -> pd.DataFrame:
    if matches is None:
        return pd.DataFrame()
    filtered = matches.copy()
    if seasons and "season" in filtered.columns:
        filtered = filtered[filtered["season"].astype(str).isin(seasons)]
    if teams:
        team_columns = [column for column in TEAM_COLUMNS if column in filtered.columns]
        if team_columns:
            team_mask = pd.Series(False, index=filtered.index)
            for column in team_columns:
                team_mask |= filtered[column].astype(str).isin(teams)
            filtered = filtered[team_mask]
        elif "winner" in filtered.columns:
            filtered = filtered[filtered["winner"].astype(str).isin(teams)]
        else:
            return filtered.iloc[0:0]
    return filtered


def _normalized_match_ids(values: pd.Series) -> pd.Series:
    normalized = values.astype("string").str.strip()
    return normalized.str.replace(r"^([+-]?\d+)\.0+$", r"\1", regex=True)


def _filter_deliveries(
    deliveries: pd.DataFrame | None,
    matches: pd.DataFrame | None,
    seasons: list[str] | None = None,
    teams: list[str] | None = None,
) -> pd.DataFrame:
    if deliveries is None:
        return pd.DataFrame()
    filtered = deliveries.copy()

    if seasons or teams:
        match_rows = _filter_matches(matches, seasons, teams)
        match_id_available = (
            matches is not None
            and "match_id" in matches.columns
            and "match_id" in filtered.columns
        )
        metadata_available = (
            (not seasons or "season" in filtered.columns)
            and (
                not teams
                or any(column in filtered.columns for column in TEAM_COLUMNS)
                or "winner" in filtered.columns
            )
        )
        if match_id_available:
            allowed_ids = _normalized_match_ids(match_rows["match_id"].dropna()).unique()
            filtered_ids = _normalized_match_ids(filtered["match_id"])
            filtered = filtered[filtered_ids.isin(allowed_ids)]
        elif metadata_available:
            if seasons and "season" in filtered.columns:
                filtered = filtered[filtered["season"].astype(str).isin(seasons)]
            if teams:
                team_columns = [
                    column for column in TEAM_COLUMNS if column in filtered.columns
                ]
                if team_columns:
                    team_mask = pd.Series(False, index=filtered.index)
                    for column in team_columns:
                        team_mask |= filtered[column].astype(str).isin(teams)
                    filtered = filtered[team_mask]
                elif "winner" in filtered.columns:
                    filtered = filtered[filtered["winner"].astype(str).isin(teams)]
        else:
            return filtered.iloc[0:0]

    return filtered


def _delivery_seasons(
    deliveries: pd.DataFrame, matches: pd.DataFrame | None
) -> pd.Series:
    if (
        matches is not None
        and {"match_id", "season"}.issubset(matches.columns)
        and "match_id" in deliveries.columns
    ):
        season_map = matches[["match_id", "season"]].dropna(
            subset=["match_id", "season"]
        ).copy()
        season_map["match_id"] = _normalized_match_ids(season_map["match_id"])
        season_counts = season_map.groupby("match_id")["season"].nunique()
        unambiguous_ids = season_counts[season_counts == 1].index
        season_map = (
            season_map[season_map["match_id"].isin(unambiguous_ids)]
            .drop_duplicates("match_id")
            .set_index("match_id")["season"]
        )
        match_ids = _normalized_match_ids(deliveries["match_id"])
        return match_ids.map(season_map).astype("string")
    return pd.Series(pd.NA, index=deliveries.index, dtype="string")


def _season_mapping_limitation(
    deliveries: pd.DataFrame, matches: pd.DataFrame | None, seasons: pd.Series
) -> str | None:
    if matches is None or not {"match_id", "season"}.issubset(matches.columns):
        return "Season caps require match_id and season columns in matches.csv."
    if "match_id" not in deliveries.columns:
        return "Season caps require a match_id column in deliveries.csv."
    if seasons.notna().sum() == 0:
        return "No delivery rows could be mapped to a match season using match_id."
    unmapped = int(seasons.isna().sum())
    if unmapped:
        return f"{unmapped} delivery rows have no unambiguous match_id-to-season mapping and were excluded."
    return None


def _credited_wicket_values(deliveries: pd.DataFrame) -> pd.Series | None:
    if not {"bowler", "dismissal_kind"}.issubset(deliveries.columns):
        return None
    dismissal = (
        deliveries["dismissal_kind"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("_", " ", regex=False)
        .str.replace("-", " ", regex=False)
    )
    credited = dismissal.ne("") & ~dismissal.isin(NON_BOWLER_DISMISSALS)
    if "is_wicket" in deliveries.columns:
        is_wicket = pd.to_numeric(deliveries["is_wicket"], errors="coerce").fillna(0)
        credited &= is_wicket.eq(1)
    return credited.astype(int)


def _bowler_wickets(deliveries: pd.DataFrame) -> pd.Series | None:
    credited = _credited_wicket_values(deliveries)
    if credited is None:
        return None
    return credited.groupby(deliveries["bowler"]).sum()


def _plot_json(figure: Any) -> dict[str, Any]:
    import json

    from plotly.utils import PlotlyJSONEncoder

    def expand_array(value: Any) -> Any:
        if isinstance(value, dict):
            if {"dtype", "bdata"}.issubset(value):
                array = np.frombuffer(
                    base64.b64decode(value["bdata"]), dtype=np.dtype(value["dtype"])
                )
                if "shape" in value:
                    array = array.reshape(value["shape"])
                return array.tolist()
            return {key: expand_array(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [expand_array(item) for item in value]
        return value

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#d9e2f3", "family": "Inter, sans-serif"},
        margin={"l": 20, "r": 20, "t": 48, "b": 20},
        colorway=["#9b8afb", "#6ba8ff", "#50d0c5", "#f0b36d"],
        hoverlabel={"bgcolor": "#151d2d", "font": {"color": "#f4f7fc"}},
    )
    figure_json = expand_array(figure.to_plotly_json())
    return json.loads(json.dumps(figure_json, cls=PlotlyJSONEncoder))


class IplDataStore:
    def __init__(self, data_dir: Path, max_upload_bytes: int = 50 * 1024 * 1024):
        self.data_dir = data_dir
        self.max_upload_bytes = max_upload_bytes
        self._lock = threading.RLock()
        self.matches: pd.DataFrame | None = None
        self.deliveries: pd.DataFrame | None = None
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for dataset in ("matches", "deliveries"):
            path = self.data_dir / f"{dataset}.csv"
            if path.is_file():
                frame = parse_csv(path.read_bytes(), dataset)
                setattr(self, dataset, frame)

    def upload(self, dataset: str, filename: str | None, contents: bytes) -> dict[str, Any]:
        expected_filename = f"{dataset}.csv"
        if dataset not in EXPECTED_COLUMNS:
            raise CsvValidationError("Upload type must be matches or deliveries.")
        if (
            filename is None
            or Path(filename).name.lower() != expected_filename
            or filename.lower() != expected_filename
        ):
            raise CsvValidationError(f"Choose a file named {expected_filename}.")
        if len(contents) > self.max_upload_bytes:
            raise CsvValidationError(
                f"The file exceeds the {self.max_upload_bytes // (1024 * 1024)} MB upload limit."
            )

        frame = parse_csv(contents, dataset)
        missing = sorted(EXPECTED_COLUMNS[dataset].difference(frame.columns))
        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            destination = self.data_dir / expected_filename
            temporary = self.data_dir / f".{expected_filename}.upload"
            try:
                temporary.write_bytes(contents)
                temporary.replace(destination)
            except OSError as error:
                temporary.unlink(missing_ok=True)
                raise OSError(f"Could not save {expected_filename}: {error}") from error
            setattr(self, dataset, frame)
        return {
            "dataset": dataset,
            "filename": expected_filename,
            "rows": len(frame),
            "columns": list(frame.columns),
            "missing_expected_columns": missing,
        }

    def filter_options(self) -> dict[str, list[str]]:
        matches = self.matches
        deliveries = self.deliveries
        seasons: set[str] = set()
        teams: set[str] = set()
        players: set[str] = set()
        if matches is not None:
            if "season" in matches.columns:
                seasons.update(_clean_values(matches["season"]))
            for column in (*TEAM_COLUMNS, "winner"):
                if column in matches.columns:
                    teams.update(_clean_values(matches[column]))
        if deliveries is not None:
            for column in ("batter", "bowler"):
                if column in deliveries.columns:
                    players.update(_clean_values(deliveries[column]))
        return {
            "seasons": sorted(seasons, key=lambda item: (not item.isdigit(), item)),
            "teams": sorted(teams),
            "players": sorted(players),
        }

    def seasons(self) -> dict[str, list[dict[str, Any]]]:
        if self.matches is None or "season" not in self.matches.columns:
            return {"seasons": []}
        counts = self.matches["season"].dropna().astype(str).value_counts()
        return {
            "seasons": [
                {"season": season, "matches": int(count)}
                for season, count in sorted(counts.items())
            ]
        }

    def dashboard(
        self, seasons: list[str] | None = None, teams: list[str] | None = None
    ) -> dict[str, Any]:
        matches = _filter_matches(self.matches, seasons, teams)
        team_names: set[str] = set()
        for column in TEAM_COLUMNS:
            if column in matches.columns:
                team_names.update(_clean_values(matches[column]))
        if not team_names and "winner" in matches.columns:
            team_names.update(_clean_values(matches["winner"]))
        winner_count = (
            int(matches["winner"].notna().sum())
            if "winner" in matches.columns
            else None
        )
        return {
            "total_matches": len(matches),
            "seasons": int(matches["season"].nunique(dropna=True))
            if "season" in matches.columns
            else None,
            "teams": len(team_names) if self.matches is not None else None,
            "matches_with_results": winner_count,
            "matches_without_results": len(matches) - winner_count
            if winner_count is not None
            else None,
            "datasets_available": {
                "matches": self.matches is not None,
                "deliveries": self.deliveries is not None,
            },
        }

    def team_statistics(
        self, seasons: list[str] | None = None, teams: list[str] | None = None
    ) -> dict[str, Any]:
        matches = _filter_matches(self.matches, seasons, teams)
        wins: dict[str, int] = {}
        if "winner" in matches.columns:
            wins = {
                str(team): int(count)
                for team, count in matches["winner"].dropna().value_counts().items()
            }
        played: dict[str, int] = {}
        for column in TEAM_COLUMNS:
            if column in matches.columns:
                counts = matches[column].dropna().astype(str).value_counts()
                for team, count in counts.items():
                    played[team] = played.get(team, 0) + int(count)
        names = sorted(set(played) | set(wins))
        rows = [
            {
                "team": name,
                "played": played.get(name, 0),
                "wins": wins.get(name, 0),
                "win_rate": round(wins.get(name, 0) / played[name] * 100, 1)
                if played.get(name, 0)
                else None,
            }
            for name in names
        ]
        return {"teams": rows}

    def player_statistics(
        self,
        seasons: list[str] | None = None,
        teams: list[str] | None = None,
        players: list[str] | None = None,
    ) -> dict[str, Any]:
        deliveries = _filter_deliveries(self.deliveries, self.matches, seasons, teams)
        runs: list[dict[str, Any]] = []
        if {"batter", "batsman_runs"}.issubset(deliveries.columns):
            deliveries = deliveries.copy()
            deliveries["batsman_runs"] = pd.to_numeric(
                deliveries["batsman_runs"], errors="coerce"
            ).fillna(0)
            totals = deliveries.groupby("batter")["batsman_runs"].sum()
            if players:
                totals = totals[totals.index.astype(str).isin(players)]
            runs = [
                {"player": str(name), "runs": int(total)}
                for name, total in totals.sort_values(ascending=False).head(10).items()
            ]
        wicket_counts = _bowler_wickets(deliveries)
        if wicket_counts is not None and players:
            wicket_counts = wicket_counts[wicket_counts.index.astype(str).isin(players)]
        wickets = (
            [
                {"player": str(name), "wickets": int(total)}
                for name, total in wicket_counts.sort_values(ascending=False)
                .head(10)
                .items()
            ]
            if wicket_counts is not None
            else []
        )
        orange_cap: list[dict[str, Any]] = []
        purple_cap: list[dict[str, Any]] = []
        seasons_by_delivery = _delivery_seasons(deliveries, self.matches)
        mapping_limitation = _season_mapping_limitation(
            deliveries, self.matches, seasons_by_delivery
        )
        orange_cap_limitation = mapping_limitation
        if orange_cap_limitation is None and not {
            "batter", "batsman_runs"
        }.issubset(deliveries.columns):
            orange_cap_limitation = (
                "Orange Cap requires batter and batsman_runs columns in deliveries.csv."
            )
        purple_cap_limitation = mapping_limitation
        if purple_cap_limitation is None and not {
            "bowler", "dismissal_kind"
        }.issubset(deliveries.columns):
            purple_cap_limitation = (
                "Purple Cap requires bowler and dismissal_kind columns in deliveries.csv."
            )

        orange_deliveries = deliveries
        if players and "batter" in deliveries.columns:
            orange_deliveries = deliveries[
                deliveries["batter"].astype(str).isin(players)
            ]
        if (
            {"batter", "batsman_runs"}.issubset(orange_deliveries.columns)
            and seasons_by_delivery.notna().any()
            and {"batter", "batsman_runs"}.issubset(orange_deliveries.columns)
        ):
            run_values = pd.to_numeric(
                orange_deliveries["batsman_runs"], errors="coerce"
            ).fillna(0)
            run_totals = pd.DataFrame({
                "season": seasons_by_delivery.loc[orange_deliveries.index],
                "player": orange_deliveries["batter"],
                "runs": run_values,
            }).dropna(subset=["season", "player"])
            if not run_totals.empty:
                run_totals = (
                    run_totals.groupby(["season", "player"], as_index=False)["runs"]
                    .sum()
                    .sort_values(
                        ["season", "runs", "player"],
                        ascending=[True, False, True],
                        kind="stable",
                    )
                    .drop_duplicates("season")
                )
                orange_cap = [
                    {"season": str(row.season), "player": str(row.player), "runs": int(row.runs)}
                    for row in run_totals.itertuples(index=False)
                ]

        purple_deliveries = deliveries
        if players and "bowler" in deliveries.columns:
            purple_deliveries = deliveries[
                deliveries["bowler"].astype(str).isin(players)
            ]
        if (
            "dismissal_kind" in purple_deliveries.columns
            and "bowler" in purple_deliveries.columns
            and seasons_by_delivery.notna().any()
            and {"bowler", "dismissal_kind"}.issubset(purple_deliveries.columns)
        ):
            wicket_values = _credited_wicket_values(purple_deliveries)
            if wicket_values is not None:
                wicket_frame = pd.DataFrame({
                    "season": seasons_by_delivery.loc[purple_deliveries.index],
                    "player": purple_deliveries["bowler"],
                    "wickets": wicket_values,
                }).dropna(subset=["season", "player"])
                wicket_frame = wicket_frame[wicket_frame["wickets"] > 0]
                if not wicket_frame.empty:
                    wicket_frame = (
                        wicket_frame.groupby(["season", "player"], as_index=False)["wickets"]
                        .sum()
                        .sort_values(
                            ["season", "wickets", "player"],
                            ascending=[True, False, True],
                            kind="stable",
                        )
                        .drop_duplicates("season")
                    )
                    purple_cap = [
                        {"season": str(row.season), "player": str(row.player), "wickets": int(row.wickets)}
                        for row in wicket_frame.itertuples(index=False)
                    ]

        return {
            "top_run_scorers": runs,
            "top_wicket_takers": wickets,
            "orange_cap": orange_cap,
            "purple_cap": purple_cap,
            "orange_cap_limitation": orange_cap_limitation,
            "purple_cap_limitation": purple_cap_limitation,
        }

    def venue_statistics(
        self, seasons: list[str] | None = None, teams: list[str] | None = None
    ) -> dict[str, Any]:
        matches = _filter_matches(self.matches, seasons, teams)
        venues: list[dict[str, Any]] = []
        if "venue" in matches.columns:
            counts = matches["venue"].dropna().astype(str).value_counts().head(20)
            venues = [
                {"venue": str(name), "matches": int(count)}
                for name, count in counts.items()
            ]
        return {"venues": venues}

    def toss_statistics(
        self, seasons: list[str] | None = None, teams: list[str] | None = None
    ) -> dict[str, Any]:
        matches = _filter_matches(self.matches, seasons, teams)
        decisions: list[dict[str, Any]] = []
        if "toss_decision" in matches.columns:
            counts = matches["toss_decision"].dropna().astype(str).value_counts()
            decisions = [
                {"decision": str(name), "matches": int(count)}
                for name, count in counts.items()
            ]
        toss_winner_matches = None
        matches_with_toss_and_result = None
        if {"toss_winner", "winner"}.issubset(matches.columns):
            valid = matches["toss_winner"].notna() & matches["winner"].notna()
            matches_with_toss_and_result = int(valid.sum())
            toss_winner_matches = int(
                (matches.loc[valid, "toss_winner"] == matches.loc[valid, "winner"]).sum()
            )
        return {
            "decisions": decisions,
            "toss_winner_matches": toss_winner_matches,
            "matches_with_toss_and_result": matches_with_toss_and_result,
            "matches": len(matches),
        }

    def data_quality(self) -> dict[str, Any]:
        datasets: dict[str, Any] = {}
        for dataset in ("matches", "deliveries"):
            frame = getattr(self, dataset)
            if frame is None:
                datasets[dataset] = {
                    "available": False,
                    "rows": 0,
                    "columns": [],
                    "missing_expected_columns": sorted(EXPECTED_COLUMNS[dataset]),
                    "missing_values": {},
                }
                continue
            missing_values = {
                str(column): int(count)
                for column, count in frame.isna().sum().items()
                if count
            }
            datasets[dataset] = {
                "available": True,
                "rows": len(frame),
                "columns": list(frame.columns),
                "missing_expected_columns": sorted(
                    EXPECTED_COLUMNS[dataset].difference(frame.columns)
                ),
                "missing_values": missing_values,
            }
        return {"datasets": datasets}

    def charts(
        self,
        seasons: list[str] | None = None,
        teams: list[str] | None = None,
        players: list[str] | None = None,
    ) -> dict[str, Any]:
        figures: dict[str, Any] = {}
        matches = _filter_matches(self.matches, seasons, teams)
        if "season" in matches.columns:
            counts = matches.groupby("season").size().reset_index(name="matches")
            if not counts.empty:
                figures["matches_by_season"] = _plot_json(
                    px.line(counts, x="season", y="matches", markers=True)
                )
        if "winner" in matches.columns:
            counts = matches["winner"].dropna().astype(str).value_counts()
            if not counts.empty:
                figures["wins_by_team"] = _plot_json(
                    px.bar(
                        counts.sort_values().rename_axis("team").reset_index(name="wins"),
                        x="wins",
                        y="team",
                        orientation="h",
                    )
                )
        if {"season", "winner"}.issubset(matches.columns):
            wins_by_season = matches.dropna(subset=["season", "winner"])
            wins_by_season = (
                wins_by_season.groupby(["season", "winner"])
                .size()
                .reset_index(name="wins")
                .rename(columns={"winner": "team"})
            )
            participant_columns = [
                column for column in TEAM_COLUMNS if column in matches.columns
            ]
            if participant_columns:
                participants = pd.concat(
                    [
                        matches[["season", column]].rename(columns={column: "team"})
                        for column in participant_columns
                    ],
                    ignore_index=True,
                ).dropna(subset=["season", "team"])
                participants["season"] = participants["season"].astype(str)
                participants["team"] = participants["team"].astype(str)
                if teams:
                    participants = participants[participants["team"].isin(teams)]
                wins_by_season["season"] = wins_by_season["season"].astype(str)
                wins_by_season["team"] = wins_by_season["team"].astype(str)
                wins_by_season = (
                    participants.drop_duplicates(["season", "team"])
                    .merge(wins_by_season, on=["season", "team"], how="left")
                )
                wins_by_season["wins"] = wins_by_season["wins"].fillna(0).astype(int)
            elif teams:
                wins_by_season = wins_by_season[
                    wins_by_season["team"].isin(teams)
                ]
            if not wins_by_season.empty:
                wins_by_season["season"] = wins_by_season["season"].astype(str)
                season_order = sorted(
                    wins_by_season["season"].unique(),
                    key=lambda value: (not value[:4].isdigit(), value[:4], value),
                )
                wins_by_season = wins_by_season.sort_values(
                    "season",
                    key=lambda values: values.map(
                        {season: index for index, season in enumerate(season_order)}
                    ),
                )
                figures["team_wins_by_season"] = _plot_json(
                    px.line(
                        wins_by_season,
                        x="season",
                        y="wins",
                        color="team",
                        markers=True,
                        category_orders={"season": season_order},
                    )
                )
        venues = self.venue_statistics(seasons, teams)["venues"]
        if venues:
            figures["matches_by_venue"] = _plot_json(
                px.bar(
                    pd.DataFrame(venues).sort_values("matches"),
                    x="matches",
                    y="venue",
                    orientation="h",
                )
            )

        player_stats = self.player_statistics(seasons, teams, players)
        if player_stats["top_run_scorers"]:
            figures["top_run_scorers"] = _plot_json(
                px.bar(
                    pd.DataFrame(player_stats["top_run_scorers"]).sort_values("runs"),
                    x="runs",
                    y="player",
                    orientation="h",
                )
            )
        if player_stats["top_wicket_takers"]:
            figures["top_wicket_takers"] = _plot_json(
                px.bar(
                    pd.DataFrame(player_stats["top_wicket_takers"]).sort_values("wickets"),
                    x="wickets",
                    y="player",
                    orientation="h",
                )
            )
        return {"figures": figures}
