import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  BarChart3,
  ChevronDown,
  CircleHelp,
  Database,
  FileChartColumn,
  Gauge,
  LayoutDashboard,
  Menu,
  Search,
  ShieldCheck,
  Target,
  Trophy,
  Upload,
  Users,
  X,
} from "lucide-react";
import {
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { getJson, uploadCsv } from "./api.js";

const PlotlyChart = lazy(async () => {
  const [{ default: createPlotlyComponent }, { default: Plotly }] = await Promise.all([
    import("react-plotly.js/factory"),
    import("plotly.js-basic-dist-min"),
  ]);
  return { default: createPlotlyComponent(Plotly) };
});

const navigation = [
  { label: "Overview", path: "/", icon: LayoutDashboard },
  { label: "Teams", path: "/teams", icon: Trophy },
  { label: "Players", path: "/players", icon: Users },
  { label: "Venues", path: "/venues", icon: Target },
  { label: "Toss & outcomes", path: "/toss", icon: Activity },
  { label: "Data quality", path: "/data-quality", icon: ShieldCheck },
  { label: "Upload data", path: "/upload", icon: Upload },
];

const TITLES = Object.fromEntries(navigation.map(({ path, label }) => [path, label]));

function ErrorNotice({ message }) {
  if (!message) return null;
  return (
    <div className="error-notice" role="alert">
      <CircleHelp size={18} />
      <div>
        <strong>Could not load analytics</strong>
        <p>{message}</p>
        <span>Check that the FastAPI service is running at the configured API URL.</span>
      </div>
    </div>
  );
}

function EmptyState({ title, description, action }) {
  return (
    <div className="empty-state">
      <span className="empty-icon"><Database size={19} /></span>
      <strong>{title}</strong>
      <p>{description}</p>
      {action}
    </div>
  );
}

function PageHeading({ eyebrow, title, description, aside }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {aside}
    </div>
  );
}

function MetricCard({ label, value, helper, icon: Icon, tone = "violet" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-topline">
        <span>{label}</span>
        <span className="metric-icon"><Icon size={17} /></span>
      </div>
      <strong>{value ?? "—"}</strong>
      <small>{helper}</small>
    </article>
  );
}

function Panel({ title, subtitle, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function DataTable({ columns, rows, emptyText = "No rows for the current filters." }) {
  if (!rows?.length) {
    return <div className="table-empty">{emptyText}</div>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row[columns[0].key]}-${index}`}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render ? column.render(row[column.key], row) : row[column.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartCard({ title, subtitle, figure, loading, error, emptyText }) {
  return (
    <Panel title={title} subtitle={subtitle}>
      {loading ? (
        <div className="chart-skeleton shimmer" role="status" aria-label="Loading chart" />
      ) : error ? (
        <div className="chart-empty" role="alert">Could not load chart data: {error}</div>
      ) : figure ? (
        <div className="chart-host">
          <Suspense fallback={<div className="chart-empty">Preparing interactive chart…</div>}>
            <PlotlyChart
              data={figure.data}
              layout={{ ...figure.layout, autosize: true, height: 310 }}
              config={{ responsive: true, displaylogo: false, displayModeBar: false }}
              useResizeHandler
              style={{ width: "100%", height: "310px" }}
            />
          </Suspense>
        </div>
      ) : (
        <div className="chart-empty" role="status">
          {emptyText || "No chart data is available for the current filters."}
        </div>
      )}
    </Panel>
  );
}

function MultiSelect({ label, options = [], value = [], onChange, searchable = false }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const shown = options.filter((option) =>
    String(option).toLowerCase().includes(search.toLowerCase()),
  );
  const toggle = (option) => {
    onChange(value.includes(option)
      ? value.filter((item) => item !== option)
      : [...value, option]);
  };
  return (
    <div className="filter-select">
      <span className="filter-label">{label}</span>
      <button
        type="button"
        className={`filter-trigger ${open ? "is-open" : ""}`}
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
      >
        <span>{value.length ? `${value.length} selected` : `All ${label.toLowerCase()}`}</span>
        <ChevronDown size={15} />
      </button>
      {open && (
        <div className="filter-menu">
          {searchable && (
            <label className="filter-search">
              <Search size={14} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={`Search ${label.toLowerCase()}`}
                autoFocus
              />
            </label>
          )}
          <button type="button" className="filter-option select-all" onClick={() => onChange([])}>
            All {label.toLowerCase()}
            {value.length === 0 && <span>✓</span>}
          </button>
          <div className="filter-options">
            {shown.map((option) => (
              <button
                type="button"
                key={option}
                className="filter-option"
                onClick={() => toggle(option)}
              >
                <span className={`checkbox-mark ${value.includes(option) ? "checked" : ""}`}>
                  {value.includes(option) ? "✓" : ""}
                </span>
                <span>{option}</span>
              </button>
            ))}
            {!shown.length && <span className="filter-no-results">No matches</span>}
          </div>
          <button type="button" className="filter-done" onClick={() => setOpen(false)}>Done</button>
        </div>
      )}
    </div>
  );
}

function FilterBar({ options, filters, onChange }) {
  return (
    <div className="filter-bar">
      <div className="filter-intro">
        <span className="filter-spark" />
        <div>
          <strong>Explore data</strong>
          <small>Filters apply across analytics</small>
        </div>
      </div>
      <MultiSelect
        label="Seasons"
        options={options.seasons}
        value={filters.season}
        onChange={(season) => onChange({ ...filters, season })}
      />
      <MultiSelect
        label="Teams"
        options={options.teams}
        value={filters.team}
        onChange={(team) => onChange({ ...filters, team })}
      />
      <MultiSelect
        label="Players"
        options={options.players}
        value={filters.player}
        onChange={(player) => onChange({ ...filters, player })}
        searchable
      />
      <button
        className="clear-filters"
        type="button"
        onClick={() => onChange({ season: [], team: [], player: [] })}
        disabled={!filters.season.length && !filters.team.length && !filters.player.length}
      >
        Clear
      </button>
    </div>
  );
}

function OverviewPage({ data, loading, error, onUpload }) {
  const kpis = data.dashboard || {};
  const matchChartsEmptyText = kpis.datasets_available?.matches
    ? "No match data is available for the current filters or required fields."
    : "Upload matches.csv to create this chart.";
  const seasonCount = kpis.seasons == null ? "—" : kpis.seasons.toLocaleString();
  const teamCount = kpis.teams == null ? "—" : kpis.teams.toLocaleString();
  return (
    <>
      <PageHeading
        eyebrow="Your analytics workspace"
        title="The season, at a glance."
        description="A clear view of match outcomes, team form and player performance."
        aside={<span className="freshness"><span /> Data updates as you upload</span>}
      />
      <div className="metrics-grid">
        <MetricCard label="Total matches" value={kpis.total_matches?.toLocaleString() ?? "0"} helper="In the current selection" icon={Gauge} />
        <MetricCard label="Seasons tracked" value={seasonCount} helper="Distinct seasons in data" icon={Activity} tone="blue" />
        <MetricCard label="Teams represented" value={teamCount} helper="Across selected matches" icon={Users} tone="teal" />
        <MetricCard label="With a result" value={kpis.matches_with_results?.toLocaleString() ?? "—"} helper={kpis.matches_without_results == null ? "Winner data unavailable" : `${kpis.matches_without_results} without a result`} icon={Trophy} tone="amber" />
      </div>
      {!kpis.datasets_available?.matches && (
        <EmptyState
          title="Your analytics start with the match dataset"
          description="Upload matches.csv to populate the dashboard with real IPL results. Player insights can be added with deliveries.csv."
          action={<button type="button" className="button-primary" onClick={onUpload}><Upload size={16} /> Upload data</button>}
        />
      )}
      <div className="content-grid two-up">
        <ChartCard title="Matches by season" subtitle="Match volume across the selected seasons" figure={data.charts?.matches_by_season} loading={loading} error={error} emptyText={matchChartsEmptyText} />
        <ChartCard title="Wins by team" subtitle="Recorded match wins in this selection" figure={data.charts?.wins_by_team} loading={loading} error={error} emptyText={matchChartsEmptyText} />
        <ChartCard title="Leading run scorers" subtitle="Aggregate batter runs in deliveries.csv" figure={data.charts?.top_run_scorers} loading={loading} error={error} emptyText={data.quality?.datasets?.deliveries?.available ? "No player data is available for the current filters or required fields." : "Upload deliveries.csv to create this chart."} />
        <ChartCard title="Most-used venues" subtitle="Matches hosted at each ground" figure={data.charts?.matches_by_venue} loading={loading} error={error} emptyText={matchChartsEmptyText} />
      </div>
      <div className="footnote"><ShieldCheck size={14} /> All figures are calculated from your uploaded CSV files.</div>
    </>
  );
}

function TeamsPage({ data, loading, error }) {
  const teams = data.teams?.teams || [];
  const [pair, setPair] = useState([]);
  useEffect(() => {
    if (teams.length && !pair.length) setPair(teams.slice(0, 2).map((item) => item.team));
    if (pair.some((name) => !teams.some((item) => item.team === name))) setPair([]);
  }, [teams, pair]);
  const compareTeams = pair.map((name) => teams.find((item) => item.team === name)).filter(Boolean);
  return (
    <>
      <PageHeading eyebrow="Team performance" title="Rivalries, in perspective." description="Compare wins, matches played and win rates across the teams in your data." />
      {!teams.length && !loading && <EmptyState title="No team results yet" description="Upload matches.csv with team and winner columns to build team performance insights." />}
      <div className="content-grid two-up">
        <ChartCard
          title="Wins by team"
          subtitle="Based on the current match filters"
          figure={data.charts?.wins_by_team}
          loading={loading}
          error={error}
          emptyText={data.quality?.datasets?.matches?.available
            ? "No match wins are available for the current filters or required fields."
            : "Upload matches.csv to create this chart."}
        />
        <ChartCard
          title="Season-by-season team wins"
          subtitle="Win totals by team across the selected seasons"
          figure={data.charts?.team_wins_by_season}
          loading={loading}
          error={error}
          emptyText="No team win data is available for the current filters."
        />
      </div>
      <div className="content-grid two-up">
        <Panel title="Compare teams" subtitle="Choose teams to compare from the current selection">
          <div className="compare-controls">
            <select aria-label="First team" value={pair[0] || ""} onChange={(event) => setPair([event.target.value, pair[1]].filter(Boolean))}>
              <option value="">Select a team</option>
              {teams.map((item) => <option key={item.team} value={item.team}>{item.team}</option>)}
            </select>
            <span>vs</span>
            <select aria-label="Second team" value={pair[1] || ""} onChange={(event) => setPair([pair[0], event.target.value].filter(Boolean))}>
              <option value="">Select a team</option>
              {teams.map((item) => <option key={item.team} value={item.team}>{item.team}</option>)}
            </select>
          </div>
          <div className="comparison-grid">
            {compareTeams.length ? compareTeams.map((team) => (
              <div className="comparison-item" key={team.team}>
                <span className="comparison-dot" />
                <strong>{team.team}</strong>
                <small>{team.played} matches</small>
                <b>{team.wins} <small>wins</small></b>
                <div className="progress-track"><span style={{ width: `${Math.min(team.win_rate || 0, 100)}%` }} /></div>
                <small>{team.win_rate == null ? "Win rate unavailable" : `${team.win_rate}% win rate`}</small>
              </div>
            )) : <div className="table-empty">Upload match data and choose teams to compare.</div>}
          </div>
        </Panel>
      </div>
      <Panel title="Team standings" subtitle="Win totals and appearances in the filtered dataset">
        <DataTable
          rows={teams}
          columns={[
            { key: "team", label: "Team" },
            { key: "played", label: "Matches played" },
            { key: "wins", label: "Wins" },
            { key: "win_rate", label: "Win rate", render: (value) => value == null ? "—" : `${value}%` },
          ]}
          emptyText={loading ? "Loading team data…" : "No teams found for these filters."}
        />
      </Panel>
    </>
  );
}

function PlayersPage({ data, loading, error }) {
  const players = data.players || {};
  const orangeCapEmptyText = loading
    ? "Loading Orange Cap data…"
    : players.orange_cap_limitation || "No Orange Cap data is available for the current filters.";
  const purpleCapEmptyText = loading
    ? "Loading Purple Cap data…"
    : players.purple_cap_limitation || "No Purple Cap data is available for the current filters.";
  return (
    <>
      <PageHeading eyebrow="Player performance" title="Individual brilliance." description="Surface the leading batters and credited wicket takers in your deliveries data." />
      {!data.quality?.datasets?.deliveries?.available && (
        <EmptyState title="Player insights need deliveries.csv" description="Upload ball-by-ball deliveries to calculate batter runs and bowler wickets." />
      )}
      <div className="content-grid two-up">
        <ChartCard title="Top run scorers" subtitle="Sum of batsman_runs by batter" figure={data.charts?.top_run_scorers} loading={loading} error={error} emptyText={data.quality?.datasets?.deliveries?.available ? "No run data is available for the current filters or required fields." : "Upload deliveries.csv to create this chart."} />
        <ChartCard title="Top wicket takers" subtitle="Non-bowler dismissals are excluded" figure={data.charts?.top_wicket_takers} loading={loading} error={error} emptyText={data.quality?.datasets?.deliveries?.available ? "No wicket data is available for the current filters or required fields." : "Upload deliveries.csv to create this chart."} />
      </div>
      <div className="content-grid two-up">
        <Panel title="Orange Cap" subtitle="Leading run scorer in each selected season">
          <DataTable
            rows={players.orange_cap}
            columns={[
              { key: "season", label: "Season" },
              { key: "player", label: "Player" },
              { key: "runs", label: "Runs" },
            ]}
            emptyText={orangeCapEmptyText}
          />
        </Panel>
        <Panel title="Purple Cap" subtitle="Leading bowler-credited wickets in each selected season">
          <DataTable
            rows={players.purple_cap}
            columns={[
              { key: "season", label: "Season" },
              { key: "player", label: "Player" },
              { key: "wickets", label: "Credited wickets" },
            ]}
            emptyText={purpleCapEmptyText}
          />
        </Panel>
      </div>
      <div className="content-grid two-up">
        <Panel title="Run leaderboard" subtitle="Top batters by total runs">
          <DataTable
            rows={players.top_run_scorers}
            columns={[{ key: "player", label: "Batter" }, { key: "runs", label: "Runs" }]}
            emptyText="No batter run totals are available."
          />
        </Panel>
        <Panel title="Wicket leaderboard" subtitle="Bowler-credited dismissals only">
          <DataTable
            rows={players.top_wicket_takers}
            columns={[{ key: "player", label: "Bowler" }, { key: "wickets", label: "Wickets" }]}
            emptyText="No credited wicket totals are available."
          />
        </Panel>
      </div>
      <div className="footnote"><ShieldCheck size={14} /> Run-outs, retired dismissals and other non-bowler dismissals are not credited to bowlers.</div>
    </>
  );
}

function VenuesPage({ data, loading, error }) {
  const venues = data.venues?.venues || [];
  return (
    <>
      <PageHeading eyebrow="Grounds & conditions" title="Every venue has a story." description="Explore where matches have been played and how often each ground appears." />
      <div className="content-grid two-up">
        <ChartCard title="Matches by venue" subtitle="Most-used grounds in the filtered match data" figure={data.charts?.matches_by_venue} loading={loading} error={error} />
        <Panel title="Venue summary" subtitle={`${venues.length} venues shown · ranked by match count`}>
          <DataTable rows={venues} columns={[{ key: "venue", label: "Venue" }, { key: "matches", label: "Matches" }]} />
        </Panel>
      </div>
      {!venues.length && !loading && <EmptyState title="Venue data is not available" description="Upload matches.csv with a venue column to see ground-level insights." />}
    </>
  );
}

function TossPage({ data, loading, error }) {
  const toss = data.toss || {};
  const decisions = toss.decisions || [];
  const rate = toss.toss_winner_matches == null
    || toss.matches_with_toss_and_result == null
    || !toss.matches_with_toss_and_result
    ? "—"
    : `${Math.round((toss.toss_winner_matches / toss.matches_with_toss_and_result) * 100)}%`;
  const decisionFigure = decisions.length ? {
    data: [{
      type: "pie",
      labels: decisions.map((item) => item.decision),
      values: decisions.map((item) => item.matches),
      hole: 0.66,
      marker: { colors: ["#9b8afb", "#6ba8ff", "#50d0c5", "#f0b36d"] },
      textinfo: "label+percent",
      textposition: "outside",
    }],
    layout: { showlegend: false },
  } : null;
  return (
    <>
      <PageHeading eyebrow="Match dynamics" title="The decision before play." description="Understand toss choices and how often the toss-winning side also wins the match." />
      <div className="metrics-grid two-metrics">
        <MetricCard label="Toss winner also won" value={toss.toss_winner_matches?.toLocaleString() ?? "—"} helper="Matches won by the toss-winning side" icon={Trophy} tone="blue" />
        <MetricCard label="Share of toss winners who also won" value={rate} helper="Among matches with a recorded toss and result" icon={BarChart3} tone="teal" />
      </div>
      <div className="content-grid two-up">
        <ChartCard title="Toss decisions" subtitle="Choose to bat or field" figure={decisionFigure} loading={loading} error={error} emptyText="Toss decision data is not available." />
        <Panel title="Toss decision breakdown" subtitle="Counts from the filtered dataset">
          <DataTable rows={decisions} columns={[{ key: "decision", label: "Decision" }, { key: "matches", label: "Matches" }]} />
        </Panel>
      </div>
    </>
  );
}

function QualityPage({ data, onUpload }) {
  const datasets = data.quality?.datasets || {};
  return (
    <>
      <PageHeading eyebrow="Dataset health" title="Know what your data contains." description="Review dataset coverage, missing fields and null values before interpreting a chart." aside={<button type="button" className="button-secondary" onClick={onUpload}><Upload size={15} /> Manage uploads</button>} />
      <div className="quality-grid">
        {["matches", "deliveries"].map((name) => {
          const dataset = datasets[name] || {};
          return (
            <Panel title={`${name}.csv`} subtitle={dataset.available ? `${dataset.rows.toLocaleString()} records loaded` : "No file uploaded"} key={name}>
              <div className="quality-status">
                <span className={`status-dot ${dataset.available ? "ready" : ""}`} />
                {dataset.available ? "Available" : "Awaiting upload"}
              </div>
              {dataset.available ? (
                <>
                  <div className="quality-label">Detected columns</div>
                  <div className="tag-list">{dataset.columns.map((column) => <span key={column}>{column}</span>)}</div>
                  <div className="quality-label">Expected fields not found</div>
                  <div className="tag-list muted-tags">
                    {dataset.missing_expected_columns?.length
                      ? dataset.missing_expected_columns.map((column) => <span key={column}>{column}</span>)
                      : <span className="all-good">All expected fields found</span>}
                  </div>
                  <div className="quality-label">Columns with missing values</div>
                  {Object.keys(dataset.missing_values || {}).length ? (
                    <DataTable
                      rows={Object.entries(dataset.missing_values).map(([column, count]) => ({ column, count }))}
                      columns={[{ key: "column", label: "Column" }, { key: "count", label: "Missing cells" }]}
                    />
                  ) : <div className="table-empty compact">No missing cells detected.</div>}
                </>
              ) : (
                <EmptyState title="Dataset not uploaded" description={`Upload ${name}.csv to enable related analytics.`} />
              )}
            </Panel>
          );
        })}
      </div>
    </>
  );
}

function UploadCard({ dataset, description, onUploaded }) {
  const formRef = useRef(null);
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const result = await uploadCsv(dataset, file);
      setMessage(`${result.rows.toLocaleString()} rows loaded.`);
      setFile(null);
      formRef.current?.reset();
      onUploaded();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="upload-card" onSubmit={submit} ref={formRef}>
      <div className="upload-card-head">
        <span className="upload-icon"><FileChartColumn size={19} /></span>
        <div><h2>{dataset}.csv</h2><p>{description}</p></div>
      </div>
      <label className="drop-zone">
        <Upload size={20} />
        <strong>{file ? file.name : "Choose a CSV file"}</strong>
        <span>{file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Browse your computer · CSV only"}</span>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => {
            const selected = event.target.files?.[0] || null;
            setFile(selected);
            setError("");
            setMessage("");
          }}
        />
      </label>
      {error && <div className="upload-error" role="alert">{error}</div>}
      {message && <div className="upload-success" role="status"><ShieldCheck size={15} /> {message}</div>}
      <div className="upload-actions">
        <span>File must be named <b>{dataset}.csv</b></span>
        <button type="submit" className="button-primary" disabled={!file || busy}>
          {busy ? <><span className="button-spinner" /> Uploading</> : <><ArrowDownToLine size={15} /> Upload dataset</>}
        </button>
      </div>
    </form>
  );
}

function UploadPage({ onUploaded }) {
  return (
    <>
      <PageHeading eyebrow="Bring your own data" title="Your data. Your insights." description="Upload IPL match results and ball-by-ball deliveries to power your analytics." />
      <div className="upload-grid">
        <UploadCard dataset="matches" description="Match-level data: season, teams, results, venue and toss." onUploaded={onUploaded} />
        <UploadCard dataset="deliveries" description="Ball-by-ball data: batter runs, bowler and dismissal details." onUploaded={onUploaded} />
      </div>
      <div className="upload-note"><ShieldCheck size={16} /><span>Files are validated before replacing the current dataset. They are stored locally by the API and are not sent to a third-party service.</span></div>
    </>
  );
}

function LoadingPage() {
  return (
    <div className="loading-page">
      <span className="loading-spinner" />
      <strong>Loading your analytics</strong>
      <small>Connecting to your IPL data…</small>
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [filters, setFilters] = useState({ season: [], team: [], player: [] });
  const [options, setOptions] = useState({ seasons: [], teams: [], players: [] });
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const pageTitle = TITLES[location.pathname] || "Overview";
  const connectionState = error ? "offline" : loading ? "connecting" : "connected";

  useEffect(() => {
    const controller = new AbortController();
    getJson("/api/filters", {}, controller.signal)
      .then(setOptions)
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      });
    return () => controller.abort();
  }, [refreshKey]);

  const activeFilters = useMemo(() => ({
    season: filters.season,
    team: filters.team,
    player: filters.player,
  }), [filters]);

  const loadData = useCallback(async (signal) => {
    setLoading(true);
    setError("");
    try {
      const [dashboard, teams, players, venues, toss, charts, quality] = await Promise.all([
        getJson("/api/dashboard", activeFilters, signal),
        getJson("/api/teams", activeFilters, signal),
        getJson("/api/players", activeFilters, signal),
        getJson("/api/venues", activeFilters, signal),
        getJson("/api/toss", activeFilters, signal),
        getJson("/api/charts", activeFilters, signal),
        getJson("/api/data-quality", {}, signal),
      ]);
      if (!charts.figures || typeof charts.figures !== "object") {
        throw new Error("The chart response did not include a figures object.");
      }
      setData({ dashboard, teams, players, venues, toss, charts: charts.figures, quality });
    } catch (requestError) {
      if (requestError.name !== "AbortError") setError(requestError.message);
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  }, [activeFilters]);

  useEffect(() => {
    const controller = new AbortController();
    loadData(controller.signal);
    return () => controller.abort();
  }, [loadData, refreshKey]);

  function refresh() {
    setRefreshKey((key) => key + 1);
  }

  function renderCurrentPage() {
    if (loading && !Object.keys(data).length) return <LoadingPage />;
    switch (location.pathname) {
      case "/teams": return <TeamsPage data={data} loading={loading} error={error} />;
      case "/players": return <PlayersPage data={data} loading={loading} error={error} />;
      case "/venues": return <VenuesPage data={data} loading={loading} error={error} />;
      case "/toss": return <TossPage data={data} loading={loading} error={error} />;
      case "/data-quality": return <QualityPage data={data} onUpload={() => navigate("/upload")} />;
      case "/upload": return <UploadPage onUploaded={refresh} />;
      default: return <OverviewPage data={data} loading={loading} error={error} onUpload={() => navigate("/upload")} />;
    }
  }

  return (
    <div className="app-shell">
      {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><span /><span /><span /></div>
          <div><strong>IPL Analytics</strong><small>CRICKET DATA</small></div>
          <button className="icon-button mobile-close" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X size={18} /></button>
        </div>
        <div className="workspace-switcher">
          <div className="workspace-avatar">I</div>
          <div><strong>IPL workspace</strong><small>Personal analytics</small></div>
          <ChevronDown size={15} />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {navigation.map(({ label, path, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={17} strokeWidth={1.8} />
              <span>{label}</span>
              {path === "/upload" && <span className="nav-new">CSV</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className={`status-dot ${data.dashboard?.datasets_available?.matches ? "ready" : ""}`} />
            <div><strong>{data.dashboard?.datasets_available?.matches ? "Data connected" : "No dataset yet"}</strong><small>{data.dashboard?.datasets_available?.matches ? "Local CSV source" : "Upload to get started"}</small></div>
          </div>
          <div className="sidebar-footer">Built for the love of the game.</div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu size={19} /></button>
            <span className="breadcrumb-muted">Workspace</span>
            <span className="breadcrumb-slash">/</span>
            <strong>{pageTitle}</strong>
          </div>
          <div className="topbar-right">
            <span className={`api-status is-${connectionState}`}><span /> API {connectionState}</span>
            <span className="avatar">IA</span>
          </div>
        </header>
        <main className="main-content">
          <ErrorNotice message={error} />
          {location.pathname !== "/upload" && location.pathname !== "/data-quality" && (
            <FilterBar options={options} filters={filters} onChange={setFilters} />
          )}
          <Routes>
            <Route path="*" element={renderCurrentPage()} />
          </Routes>
          <footer className="app-footer">
            <span>IPL ANALYTICS <span className="footer-dot">·</span> Cricket, clearly.</span>
            <span>Data is processed locally by your API</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
