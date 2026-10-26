from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.data_service import IplDataStore
from backend.app.main import app


class IplApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_store = app.state.data_store
        app.state.data_store = IplDataStore(Path(self.temp_dir.name))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.state.data_store = self.previous_store
        self.temp_dir.cleanup()

    def upload(self, path: str, filename: str, csv: str):
        return self.client.post(
            path, files={"file": (filename, csv.encode("utf-8"), "text/csv")}
        )

    def test_empty_dashboard_is_explicit(self) -> None:
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_matches"], 0)
        self.assertFalse(response.json()["datasets_available"]["matches"])

    def test_upload_and_filtered_match_endpoints(self) -> None:
        csv = (
            "id,season,team1,team2,winner,venue,toss_winner,toss_decision\n"
            "1,2024,CSK,MI,CSK,Chennai,CSK,field\n"
            "2,2023,MI,RCB,RCB,Mumbai,MI,bat\n"
        )
        response = self.upload("/api/upload/matches", "matches.csv", csv)
        self.assertEqual(response.status_code, 200, response.text)
        dashboard = self.client.get("/api/dashboard?season=2024&team=CSK").json()
        self.assertEqual(dashboard["total_matches"], 1)
        self.assertEqual(dashboard["matches_with_results"], 1)
        self.assertEqual(self.client.get("/api/teams?season=2024").json()["teams"][0]["wins"], 1)
        self.assertEqual(self.client.get("/api/venues?season=2024").json()["venues"][0]["venue"], "Chennai")
        toss = self.client.get("/api/toss?season=2024").json()
        self.assertEqual(toss["decisions"], [{"decision": "field", "matches": 1}])
        self.assertEqual(toss["toss_winner_matches"], 1)
        self.assertEqual(toss["matches_with_toss_and_result"], 1)
        self.assertTrue(
            self.client.get("/api/data-quality").json()["datasets"]["matches"]["available"]
        )
        self.assertEqual(
            self.client.get("/api/seasons").json()["seasons"],
            [{"season": "2023", "matches": 1}, {"season": "2024", "matches": 1}],
        )

    def test_bowler_wickets_exclude_non_bowler_dismissals(self) -> None:
        matches = "id,season,team1,team2,winner\n1,2024,CSK,MI,CSK\n"
        deliveries = (
            "id,batter,batsman_runs,bowler,is_wicket,dismissal_kind\n"
            "1,A,4,Bowler X,1,caught\n"
            "1,A,0,Bowler X,1,run out\n"
            "1,C,0,Bowler X,1,stumped\n"
        )
        self.assertEqual(
            self.upload("/api/upload/matches", "matches.csv", matches).status_code, 200
        )
        self.assertEqual(
            self.upload("/api/upload/deliveries", "deliveries.csv", deliveries).status_code,
            200,
        )
        player_stats = self.client.get("/api/players?season=2024").json()
        self.assertEqual(player_stats["top_wicket_takers"][0], {"player": "Bowler X", "wickets": 2})
        self.assertEqual(player_stats["top_run_scorers"][0], {"player": "A", "runs": 4})

    def test_upload_rejects_wrong_filename_and_invalid_csv(self) -> None:
        wrong_name = self.upload("/api/upload/matches", "other.csv", "season\n2024\n")
        self.assertEqual(wrong_name.status_code, 400)
        path_name = self.upload(
            "/api/upload/matches", "..\\matches.csv", "season\n2024\n"
        )
        self.assertEqual(path_name.status_code, 400)
        malformed = self.upload("/api/upload/matches", "matches.csv", "season,season\n2024,2024\n")
        self.assertEqual(malformed.status_code, 400)
        unrelated = self.upload("/api/upload/matches", "matches.csv", "unknown\nvalue\n")
        self.assertEqual(unrelated.status_code, 400)

    def test_values_are_trimmed_and_blank_results_are_not_counted(self) -> None:
        csv = "season,team1,team2,winner\n2024, CSK ,MI, \n"
        response = self.upload("/api/upload/matches", "matches.csv", csv)
        self.assertEqual(response.status_code, 200, response.text)
        dashboard = self.client.get("/api/dashboard?season=2024&team=CSK").json()
        self.assertEqual(dashboard["total_matches"], 1)
        self.assertEqual(dashboard["matches_with_results"], 0)
        self.assertEqual(dashboard["matches_without_results"], 1)

    def test_toss_win_count_and_eligible_denominator_exclude_missing_results(self) -> None:
        csv = (
            "season,team1,team2,winner,toss_winner\n"
            "2024,CSK,MI,CSK,CSK\n"
            "2024,MI,RCB,RCB,MI\n"
            "2024,RCB,CSK,,RCB\n"
        )
        response = self.upload("/api/upload/matches", "matches.csv", csv)
        self.assertEqual(response.status_code, 200, response.text)

        toss = self.client.get("/api/toss").json()
        self.assertEqual(toss["toss_winner_matches"], 1)
        self.assertEqual(toss["matches_with_toss_and_result"], 2)
        self.assertEqual(toss["matches"], 3)

    def test_charts_return_plotly_figures_from_uploaded_data(self) -> None:
        csv = "id,season,team1,team2,winner\n1,2024,CSK,MI,CSK\n"
        self.upload("/api/upload/matches", "matches.csv", csv)
        response = self.client.get("/api/charts")
        self.assertEqual(response.status_code, 200)
        figures = response.json()["figures"]
        self.assertEqual(figures["matches_by_season"]["data"][0]["y"], [1])
        self.assertEqual(figures["wins_by_team"]["data"][0]["x"], [1])
        self.assertEqual(figures["wins_by_team"]["data"][0]["y"], ["CSK"])

    def test_season_caps_map_delivery_match_ids_and_apply_filters(self) -> None:
        matches = (
            "ID,season,team1,team2,winner\n"
            "1,2023,CSK,MI,CSK\n"
            "2,2023,MI,RCB,RCB\n"
            "3,2024,CSK,MI,MI\n"
            "4,2024,CSK,RCB,CSK\n"
        )
        deliveries = (
            "Match ID,Batsman,Batter Runs,Bowler Name,Is Wicket,Dismissal Kind\n"
            "1.0,Alice,30,Z,1,caught\n"
            "1.0,Bob,20,Z,1,run out\n"
            "1.0,Carol,8,Q,1,stumped\n"
            "2.0,Bob,16,Z,1,lbw\n"
            "3.0,Chen,22,M,1,caught\n"
            "3.0,Dan,11,M,1,run out\n"
            "4.0,Dan,18,N,1,caught\n"
            "4.0,Dan,0,M,1,obstructing the field\n"
            "4.0,,0,P,1,retired hurt\n"
            "4.0,,0,Q,1,retired out\n"
            "4.0,,0,R,1,hit the ball twice\n"
            "4.0,,0,S,1,handled the ball\n"
            "4.0,,0,T,1,timed out\n"
        )
        self.assertEqual(
            self.upload("/api/upload/matches", "matches.csv", matches).status_code,
            200,
        )
        self.assertEqual(
            self.upload("/api/upload/deliveries", "deliveries.csv", deliveries).status_code,
            200,
        )

        stats = self.client.get("/api/players").json()
        self.assertEqual(
            stats["orange_cap"],
            [
                {"season": "2023", "player": "Bob", "runs": 36},
                {"season": "2024", "player": "Dan", "runs": 29},
            ],
        )
        self.assertEqual(
            stats["purple_cap"],
            [
                {"season": "2023", "player": "Z", "wickets": 2},
                {"season": "2024", "player": "M", "wickets": 1},
            ],
        )

        filtered = self.client.get("/api/players?season=2024&player=Chen").json()
        self.assertEqual(
            filtered["orange_cap"],
            [{"season": "2024", "player": "Chen", "runs": 22}],
        )
        self.assertEqual(
            filtered["top_run_scorers"],
            [{"player": "Chen", "runs": 22}],
        )
        self.assertEqual(filtered["top_wicket_takers"], [])
        self.assertEqual(filtered["purple_cap"], [])

        team_filtered = self.client.get(
            "/api/players?season=2024&team=CSK"
        ).json()
        self.assertEqual(
            team_filtered["orange_cap"],
            [{"season": "2024", "player": "Dan", "runs": 29}],
        )
        self.assertEqual(
            team_filtered["purple_cap"],
            [{"season": "2024", "player": "M", "wickets": 1}],
        )

    def test_caps_explain_when_match_to_season_mapping_is_ambiguous(self) -> None:
        matches = (
            "id,season,team1,team2,winner\n"
            "1,2023,CSK,MI,CSK\n"
            "1,2024,MI,RCB,RCB\n"
        )
        deliveries = (
            "match_id,season,batter,batsman_runs,bowler,is_wicket,dismissal_kind\n"
            "1,2024,Alice,50,Bowler X,1,caught\n"
        )
        self.assertEqual(
            self.upload("/api/upload/matches", "matches.csv", matches).status_code,
            200,
        )
        self.assertEqual(
            self.upload("/api/upload/deliveries", "deliveries.csv", deliveries).status_code,
            200,
        )

        stats = self.client.get("/api/players").json()
        self.assertEqual(stats["orange_cap"], [])
        self.assertEqual(stats["purple_cap"], [])
        self.assertIn("No delivery rows could be mapped", stats["orange_cap_limitation"])
        self.assertIn("No delivery rows could be mapped", stats["purple_cap_limitation"])

    def test_delivery_season_column_is_not_used_as_a_match_mapping_guess(self) -> None:
        matches = "season,team1,team2,winner\n2024,CSK,MI,CSK\n"
        deliveries = (
            "season,batter,batsman_runs,bowler,is_wicket,dismissal_kind\n"
            "2024,Alice,50,Bowler X,1,caught\n"
        )
        self.assertEqual(
            self.upload("/api/upload/matches", "matches.csv", matches).status_code,
            200,
        )
        self.assertEqual(
            self.upload("/api/upload/deliveries", "deliveries.csv", deliveries).status_code,
            200,
        )

        stats = self.client.get("/api/players").json()
        self.assertEqual(stats["orange_cap"], [])
        self.assertEqual(stats["purple_cap"], [])
        self.assertIn("match_id", stats["orange_cap_limitation"])
        self.assertIn("match_id", stats["purple_cap_limitation"])

    def test_team_wins_by_season_respects_season_and_team_filters(self) -> None:
        matches = (
            "id,season,team1,team2,winner\n"
            "1,2023,CSK,MI,CSK\n"
            "2,2023,MI,RCB,RCB\n"
            "3,2024,CSK,MI,MI\n"
            "4,2024,CSK,RCB,CSK\n"
            "5,2024,MI,RCB,MI\n"
        )
        self.assertEqual(
            self.upload("/api/upload/matches", "matches.csv", matches).status_code,
            200,
        )

        figures = self.client.get("/api/charts").json()["figures"]
        traces = {
            trace["name"]: {"seasons": trace["x"], "wins": trace["y"]}
            for trace in figures["team_wins_by_season"]["data"]
        }
        self.assertEqual(traces["CSK"], {"seasons": ["2023", "2024"], "wins": [1, 1]})
        self.assertEqual(traces["MI"], {"seasons": ["2023", "2024"], "wins": [0, 2]})
        self.assertEqual(traces["RCB"], {"seasons": ["2023", "2024"], "wins": [1, 0]})

        filtered = self.client.get(
            "/api/charts?season=2024&team=CSK"
        ).json()["figures"]["team_wins_by_season"]["data"]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "CSK")
        self.assertEqual(filtered[0]["x"], ["2024"])
        self.assertEqual(filtered[0]["y"], [1])


if __name__ == "__main__":
    unittest.main()
