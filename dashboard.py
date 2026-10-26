
import streamlit as st
import pandas as pd
import plotly.express as px


def style_chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font={"family": "Arial, sans-serif", "color": "#e8ebf5", "size": 13},
        colorway=["#9B7BFF", "#FF9F43", "#39C6C8", "#78D6A3"],
        margin={"l": 12, "r": 16, "t": 56, "b": 16},
        hoverlabel={
            "bgcolor": "#171d30",
            "bordercolor": "#6552a3",
            "font": {"color": "#f4f5fa", "size": 13}
        },
        legend={"title_text": ""},
        hovermode="closest",
        hoverlabel_namelength=-1,
        title_font={"size": 17, "color": "#f4f5fa"},
        autosize=True
    )
    fig.update_xaxes(
        gridcolor="rgba(170, 180, 205, 0.12)",
        zerolinecolor="rgba(170, 180, 205, 0.2)",
        tickfont={"color": "#aab4cc"},
        title_font={"color": "#c0c8da"},
        showline=True,
        linecolor="rgba(170, 180, 205, 0.18)"
    )
    fig.update_yaxes(
        gridcolor="rgba(170, 180, 205, 0.12)",
        zerolinecolor="rgba(170, 180, 205, 0.2)",
        tickfont={"color": "#c0c8da"},
        title_font={"color": "#c0c8da"},
        showline=False
    )
    return fig


# ---------- PAGE CONFIGURATION ----------
st.set_page_config(
    page_title="IPL Cricket Data Analysis & Visualization",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 85% 0%, rgba(111, 66, 193, 0.14), transparent 34%),
            #0b1020;
        color: #f4f5fa;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1600px;
        padding: 2.2rem clamp(1.25rem, 3vw, 3.25rem) 3rem;
    }
    [data-testid="stHeader"] {
        background: rgba(11, 16, 32, 0.92);
    }
    h1, h2, h3 {
        color: #f4f5fa;
        letter-spacing: -0.025em;
    }
    h1 {
        font-size: clamp(1.8rem, 3vw, 2.45rem) !important;
    }
    .dashboard-hero {
        position: relative;
        overflow: hidden;
        margin: 0.35rem 0 1.7rem;
        padding: clamp(1.5rem, 3vw, 2.5rem);
        border: 1px solid rgba(155, 123, 255, 0.28);
        border-radius: 18px;
        background:
            radial-gradient(ellipse at 88% 20%, rgba(155, 123, 255, 0.23), transparent 36%),
            linear-gradient(115deg, #131a2d 0%, #17172d 58%, #201936 100%);
        box-shadow: 0 18px 44px rgba(0, 0, 0, 0.2);
    }
    .dashboard-hero::after {
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #a78bfa, #ff9f43);
        content: "";
    }
    .hero-kicker {
        margin-bottom: 0.65rem;
        color: #c4b3ff;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }
    .hero-title {
        margin: 0;
        color: #f7f7fb;
        font-size: clamp(1.8rem, 3.4vw, 2.8rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.12;
    }
    .hero-subtitle {
        max-width: 720px;
        margin: 0.85rem 0 0;
        color: #b4bed2;
        font-size: 1rem;
        line-height: 1.65;
    }
    .hero-tag {
        display: inline-block;
        margin-top: 1.2rem;
        padding: 0.38rem 0.7rem;
        border: 1px solid rgba(196, 179, 255, 0.26);
        border-radius: 999px;
        background: rgba(155, 123, 255, 0.1);
        color: #d7cbff;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    [data-testid="stSidebar"] {
        width: 20rem !important;
        min-width: 20rem !important;
        max-width: 20rem !important;
        background: #0e1425;
        border-right: 1px solid rgba(170, 180, 205, 0.14);
        color: #e8ebf5;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #c0c8da;
    }
    [data-testid="stSidebar"] h1 {
        margin-bottom: 0.15rem;
        font-size: 1.45rem !important;
    }
    [data-testid="stSidebar"] a {
        display: block;
        padding: 0.2rem 0;
        color: #c9c1e5 !important;
        font-size: 0.9rem;
        text-decoration: none;
    }
    [data-testid="stSidebar"] a:hover {
        color: #ffb15e !important;
    }
    [data-testid="stMultiSelect"],
    [data-testid="stSelectbox"] {
        margin-bottom: 0.45rem;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #121a2d;
        border: 1px dashed rgba(155, 123, 255, 0.5);
        border-radius: 10px;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: #211b38;
        border-color: rgba(155, 123, 255, 0.48);
        color: #f4f5fa;
    }
    [data-testid="stFileUploaderDropzone"] p {
        color: #aab4cc;
    }
    [data-testid="stAlert"] {
        background: #141d32;
        border: 1px solid rgba(120, 150, 205, 0.22);
        border-radius: 10px;
    }
    [data-testid="stAlert"] p {
        color: #e1e7f4;
    }
    [data-testid="stMetric"] {
        position: relative;
        min-height: 112px;
        overflow: hidden;
        background: #121a2d;
        border: 1px solid rgba(170, 180, 205, 0.14);
        border-radius: 14px;
        padding: 18px 18px 16px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
        transition: border-color 160ms ease, transform 160ms ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(155, 123, 255, 0.48);
        transform: translateY(-2px);
    }
    [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] {
        border-top: 2px solid #9b7bff;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] {
        border-top: 2px solid #ff9f43;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] {
        border-top: 2px solid #39c6c8;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] {
        border-top: 2px solid #78d6a3;
    }
    [data-testid="stMetricLabel"] {
        color: #aab4cc;
        font-size: 0.82rem;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-size: clamp(1.45rem, 2vw, 2rem);
        font-weight: 700;
        letter-spacing: -0.035em;
    }
    [data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid rgba(170, 180, 205, 0.13);
        border-radius: 14px;
        background: rgba(18, 26, 45, 0.58);
        padding: 0.35rem 0.45rem;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(170, 180, 205, 0.13);
        border-radius: 12px;
        overflow: hidden;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 8px;
        border: 1px solid rgba(155, 123, 255, 0.48);
        background: #211b38;
        color: #f4f5fa;
        transition: border-color 150ms ease, background 150ms ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #ff9f43;
        background: #2a2144;
        color: #ffffff;
    }
    a {
        color: #c4b3ff !important;
    }
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.25rem 1rem 2rem;
        }
        [data-testid="stSidebar"] {
            width: 85vw !important;
            min-width: 85vw !important;
            max-width: 85vw !important;
        }
        h1 {
            font-size: 1.8rem !important;
        }
        .dashboard-hero {
            border-radius: 14px;
        }
        [data-testid="stMetric"] {
            min-height: 96px;
            padding: 14px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <section class="dashboard-hero">
        <div class="hero-kicker">IPL Analytics Pro · Cricket Data & Insights</div>
        <h1 class="hero-title">IPL Cricket Data Analysis &amp; Visualization</h1>
        <p class="hero-subtitle">
            A focused match and player performance dashboard, powered by the
            CSV datasets you upload.
        </p>
        <span class="hero-tag">CSV-POWERED ANALYTICS</span>
    </section>
    """,
    unsafe_allow_html=True
)

# ---------- DATA UPLOAD ----------
st.sidebar.title("IPL Analytics Pro")
st.sidebar.caption("Dataset controls")
st.sidebar.subheader("Upload data")

matches_file = st.sidebar.file_uploader(
    "Upload matches.csv",
    type=["csv"],
    key="matches"
)

deliveries_file = st.sidebar.file_uploader(
    "Upload deliveries.csv",
    type=["csv"],
    key="deliveries"
)

# ---------- LOAD DATA ----------
matches = None
deliveries = None

if matches_file is not None:
    try:
        matches = pd.read_csv(matches_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.sidebar.error(f"Could not read matches.csv: {error}")
        st.stop()

    matches.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in matches.columns
    ]
    expected_match_columns = {"season", "team1", "team2", "winner", "venue"}
    missing_match_columns = expected_match_columns.difference(matches.columns)
    if missing_match_columns:
        st.sidebar.warning(
            "Some match insights may be unavailable. Missing columns: "
            + ", ".join(sorted(missing_match_columns))
        )

if deliveries_file is not None:
    try:
        deliveries = pd.read_csv(deliveries_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.sidebar.error(f"Could not read deliveries.csv: {error}")
        deliveries = None

if deliveries is not None:
    deliveries.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in deliveries.columns
    ]

    if "batsman" in deliveries.columns:
        deliveries.rename(
            columns={"batsman": "batter"},
            inplace=True
        )
    expected_delivery_columns = {
        "batter", "batsman_runs", "bowler", "is_wicket"
    }
    missing_delivery_columns = expected_delivery_columns.difference(deliveries.columns)
    if missing_delivery_columns:
        st.sidebar.warning(
            "Some player insights may be unavailable. Missing columns: "
            + ", ".join(sorted(missing_delivery_columns))
        )

# ---------- MAIN DASHBOARD ----------
if matches is None:
    st.info(
        "Upload a valid matches.csv file from the sidebar to begin. "
        "Add deliveries.csv to explore player and bowling insights."
    )
    st.caption(
        "The dashboard reads your CSV uploads directly; no sample statistics are shown."
    )
    st.stop()

if matches.empty:
    st.warning("The uploaded matches.csv contains headers but no match records.")

if deliveries_file is None:
    st.sidebar.info("Upload deliveries.csv to enable player analysis.")

st.sidebar.divider()
st.sidebar.subheader("Dashboard sections")
st.sidebar.markdown(
    """
- [Overview](#overview)
- [Team Analytics](#team-analytics)
- [Season Trends](#season-trends)
- [Toss Analysis](#toss-analysis)
- [Venue Insights](#venue-insights)
- [Player Analytics](#player-analytics)
- [Player Comparison](#player-comparison)
- [Data Export](#data-export)
"""
)
st.sidebar.caption("Select a section to jump to its analysis.")

# ---------- FILTERS ----------
st.sidebar.divider()
st.sidebar.subheader("Match filters")

filtered = matches.copy()

if "season" in filtered.columns:
    seasons = sorted(
        filtered["season"].dropna().unique().tolist(),
        key=str
    )
    selected_seasons = st.sidebar.multiselect(
        "Select Season",
        seasons,
        default=seasons
    )
    filtered = filtered[
        filtered["season"].isin(selected_seasons)
    ]

team_columns = [
    c for c in ["team1", "team2"]
    if c in filtered.columns
]

if team_columns:
    all_teams = sorted({
        team
        for c in team_columns
        for team in filtered[c].dropna().astype(str)
    })

    selected_teams = st.sidebar.multiselect(
        "Select Team",
        all_teams,
        default=all_teams
    )

    if selected_teams:
        team_mask = pd.Series(False, index=filtered.index)

        for c in team_columns:
            team_mask |= filtered[c].astype(str).isin(selected_teams)

        filtered = filtered[team_mask]

if "venue" in filtered.columns:
    venues = sorted(
        filtered["venue"].dropna().astype(str).unique()
    )
    selected_venues = st.sidebar.multiselect(
        "Select Venue",
        venues,
        default=venues
    )
    filtered = filtered[
        filtered["venue"].astype(str).isin(selected_venues)
    ]

exports = {}

# ---------- SUMMARY METRICS ----------
st.header("Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Matches", len(filtered))

if "season" in filtered.columns:
    col2.metric("IPL Seasons", filtered["season"].nunique())
else:
    col2.metric("IPL Seasons", "N/A")

if "team1" in filtered.columns and "team2" in filtered.columns:
    teams_count = pd.concat([
        filtered["team1"],
        filtered["team2"]
    ]).nunique()
else:
    teams_count = "N/A"

col3.metric("Teams", teams_count)

if "winner" in filtered.columns:
    col4.metric("Matches with Result", filtered["winner"].notna().sum())
else:
    col4.metric("Matches with Result", "N/A")

st.caption("All match-level indicators reflect the current sidebar filters.")

# ---------- TEAM PERFORMANCE ----------
st.header("Team Analytics")

if "winner" in filtered.columns:
    wins = (
        filtered["winner"]
        .dropna()
        .value_counts()
        .reset_index()
    )
    wins.columns = ["Team", "Wins"]

    if not wins.empty:
        fig = px.bar(
            wins.sort_values("Wins"),
            x="Wins",
            y="Team",
            orientation="h",
            title="Matches won by team",
            labels={"Wins": "Wins", "Team": "Team"},
            color_discrete_sequence=["#9B7BFF"]
        )
        st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})
        st.dataframe(wins, width="stretch", hide_index=True)
        exports["Team statistics"] = ("ipl_team_statistics.csv", wins)
    else:
        st.info("No team results are available for the selected filters.")
else:
    st.info("Team results are unavailable because the winner column is missing.")

# ---------- SEASON ANALYSIS ----------
st.header("Season Trends")

if "season" in filtered.columns:
    season_counts = (
        filtered.groupby("season")
        .size()
        .reset_index(name="Matches")
    )

    fig = px.line(
        season_counts,
        x="season",
        y="Matches",
        markers=True,
        title="Matches played by season",
        labels={"season": "Season", "Matches": "Matches"}
    )
    fig.update_traces(
        line={"color": "#9B7BFF", "width": 3},
        marker={"color": "#FF9F43", "size": 9}
    )
    st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})
else:
    st.info("Season trends are unavailable because the season column is missing.")

# ---------- TOSS ANALYSIS ----------
st.header("Toss Analysis")

if "toss_winner" in filtered.columns:
    toss_counts = (
        filtered["toss_decision"].value_counts().reset_index()
        if "toss_decision" in filtered.columns
        else pd.DataFrame()
    )

    if not toss_counts.empty:
        toss_counts.columns = ["Decision", "Matches"]

        fig = px.pie(
            toss_counts,
            names="Decision",
            values="Matches",
            title="Toss decisions",
            color_discrete_sequence=["#9B7BFF", "#FF9F43", "#39C6C8"]
        )
        st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})

    if "winner" in filtered.columns:
        toss_wins = filtered[
            filtered["toss_winner"].notna()
            & (filtered["toss_winner"] == filtered["winner"])
        ]
        st.metric("Toss Winner Also Won", len(toss_wins))
else:
    st.info("Toss analysis is unavailable because toss_winner is missing.")

# ---------- VENUE ANALYSIS ----------
st.header("Venue Insights")

if "venue" in filtered.columns:
    venue_stats = (
        filtered["venue"].dropna()
        .value_counts()
        .head(10)
        .reset_index()
    )
    venue_stats.columns = ["Venue", "Matches"]

    fig = px.bar(
        venue_stats.sort_values("Matches"),
        x="Matches",
        y="Venue",
        orientation="h",
        title="Most-used venues",
        labels={"Matches": "Matches", "Venue": "Venue"},
        color_discrete_sequence=["#39C6C8"]
    )
    st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})
    exports["Venue statistics"] = ("ipl_venue_statistics.csv", venue_stats)
else:
    st.info("Venue insights are unavailable because the venue column is missing.")

# ---------- PLAYER ANALYSIS ----------
st.header("Player Analytics")
st.caption("Batting totals and bowling dismissals are calculated from deliveries.csv.")

if deliveries is not None:
    if "batter" in deliveries.columns and "batsman_runs" in deliveries.columns:
        deliveries["batsman_runs"] = pd.to_numeric(
            deliveries["batsman_runs"], errors="coerce"
        ).fillna(0)

        player_runs = (
            deliveries.groupby("batter")["batsman_runs"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        player_runs.columns = ["Player", "Runs"]

        st.subheader("Run leaders")
        fig = px.bar(
            player_runs.sort_values("Runs"),
            x="Runs",
            y="Player",
            orientation="h",
            title="Top 10 run scorers",
            labels={"Runs": "Runs", "Player": "Batter"},
            color_discrete_sequence=["#FF9F43"]
        )
        st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})
        st.dataframe(player_runs, width="stretch", hide_index=True)
        exports["Player statistics"] = ("ipl_player_statistics.csv", player_runs)

        # ---------- PLAYER COMPARISON ----------
        st.header("Player Comparison")

        players = sorted(
            deliveries["batter"].dropna().unique().tolist()
        )

        if len(players) >= 2:
            st.caption("Compare total runs for any two batters in the uploaded data.")
            p1 = st.selectbox("First player", players, index=0)
            p2 = st.selectbox("Second player", players, index=1)

            player_runs_all = (
                deliveries.groupby("batter")["batsman_runs"].sum()
            )

            comparison_df = pd.DataFrame({
                "Player": [p1, p2],
                "Total Runs": [
                    int(player_runs_all.get(p1, 0)),
                    int(player_runs_all.get(p2, 0))
                ]
            })

            st.dataframe(
                comparison_df,
                width="stretch",
                hide_index=True
            )

            fig = px.bar(
                comparison_df,
                x="Player",
                y="Total Runs",
                color="Player",
                title="Total runs comparison",
                labels={"Total Runs": "Runs", "Player": "Batter"},
                color_discrete_sequence=["#9B7BFF", "#FF9F43"]
            )
            st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})
            exports["Player comparison"] = (
                "ipl_player_comparison.csv",
                comparison_df
            )
        else:
            st.info("At least two batters are needed for a player comparison.")

    else:
        st.warning(
            "Player analysis needs batter and batsman_runs columns in deliveries.csv."
        )
else:
    st.info("Upload deliveries.csv to see player statistics.")

# ---------- BOWLING ANALYSIS ----------
st.subheader("Bowling leaders")

if deliveries is not None:
    if "bowler" in deliveries.columns:
        if "is_wicket" in deliveries.columns:
            bowling = deliveries.copy()
            bowling["wicket_count"] = pd.to_numeric(
                bowling["is_wicket"], errors="coerce"
            ).fillna(0)

            if "dismissal_kind" in bowling.columns:
                excluded = [
                    "run out", "retired hurt", "retired out",
                    "obstructing the field"
                ]
                bowling.loc[
                    bowling["dismissal_kind"]
                    .fillna("")
                    .str.lower()
                    .isin(excluded),
                    "wicket_count"
                ] = 0

            wickets = (
                bowling.groupby("bowler")["wicket_count"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )
            wickets.columns = ["Bowler", "Wickets"]

            fig = px.bar(
                wickets.sort_values("Wickets"),
                x="Wickets",
                y="Bowler",
                orientation="h",
                title="Top 10 wicket takers",
                labels={"Wickets": "Wickets", "Bowler": "Bowler"},
                color_discrete_sequence=["#9B7BFF"]
            )
            st.plotly_chart(style_chart(fig), width="stretch", config={"displaylogo": False})
            st.dataframe(wickets, width="stretch", hide_index=True)
            exports["Bowling statistics"] = (
                "ipl_bowling_statistics.csv",
                wickets
            )
        else:
            st.info("Bowling analysis needs the is_wicket column.")
    else:
        st.info("Bowling analysis needs the bowler column.")

# ---------- MATCH INSIGHTS ----------
st.header("Match Insights")

if "winner" in filtered.columns:
    no_result = filtered["winner"].isna().sum()
    st.metric("Matches without a recorded winner", no_result)

# ---------- DATA EXPORT ----------
st.header("Data Export")
st.caption(
    "Download the statistics currently calculated from your uploaded data "
    "and selected match filters."
)

if exports:
    export_columns = st.columns(min(3, len(exports)))
    for index, (label, (filename, dataframe)) in enumerate(exports.items()):
        with export_columns[index % len(export_columns)]:
            st.download_button(
                f"Download {label}",
                dataframe.to_csv(index=False).encode("utf-8"),
                filename,
                "text/csv",
                width="stretch",
                key=f"download_{filename}"
            )
else:
    st.info("No statistics are available to export yet.")

st.divider()
st.caption(
    "IPL Cricket Data Analysis & Visualization  ·  Built with Streamlit, "
    "Python, Pandas, and Plotly"
)
