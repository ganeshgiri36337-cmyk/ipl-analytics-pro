# IPL Analytics

IPL Analytics is a CSV-powered IPL dashboard. The existing Streamlit dashboard and analysis script remain in the project; the new React/Vite interface and FastAPI service run alongside them.

## Project layout

```text
IPL_Project/
├── backend/
│   ├── app/
│   │   ├── data_service.py
│   │   └── main.py
│   └── tests/
│       └── test_api.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── data/                 # Created automatically for accepted CSV uploads
├── dashboard.py          # Existing Streamlit dashboard, preserved
├── ipl_analysis.py       # Existing analysis script, preserved
├── requirements.txt
└── README.md
```

## Windows setup

Open PowerShell in the project directory.

### 1. Start the API

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --reload-dir backend
```

The API is available at <http://127.0.0.1:8000>; interactive API documentation is at <http://127.0.0.1:8000/docs>.

### 2. Start the web app

In a second PowerShell window, install a current Node.js LTS release if Node.js and npm are not already installed. Then run:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally <http://localhost:5173>). The frontend calls the API at `http://localhost:8000` by default. To use a different API URL, create `frontend/.env.local` with:

```text
VITE_API_BASE_URL=http://localhost:8000
```

### Deploy to Render

Create a Render Blueprint from this repository and select `render.yaml`. It creates a static React site and a FastAPI web service. The `data/` directory is intentionally excluded from Git; upload `matches.csv` and `deliveries.csv` through the deployed Upload page after the services are live.

The free web service uses ephemeral storage. Uploaded CSV files are not durable across service restarts or redeployments unless a persistent storage option is configured.

### Optional: keep using Streamlit

The existing dashboard is not replaced:

```powershell
python -m streamlit run dashboard.py
```

## Datasets and uploads

Use the **Upload data** page to upload files named exactly `matches.csv` and `deliveries.csv`. Uploads are validated before replacing the current dataset and are stored under the project `data` directory by default. The API accepts a configurable storage path and upload limit:

```powershell
$env:IPL_DATA_DIR = "C:\ipl-data"
$env:IPL_MAX_UPLOAD_BYTES = "52428800"
```

The backend normalizes common column-name variants (including `id`/`match_id` and `batsman`/`batter`) and reports missing expected fields. Insights that need unavailable columns are returned as unavailable/empty rather than fabricated. Deliveries are mapped to match seasons and team filters by match ID when available. Orange and Purple Cap leaders are calculated separately for each season; Purple Cap requires dismissal-kind data to exclude uncredited dismissals. The team chart includes season-by-season wins.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Service health |
| `GET /api/filters` | Available season, team, and player filters |
| `GET /api/seasons` | Seasons and match counts |
| `GET /api/dashboard` | Overview KPIs |
| `GET /api/teams` | Team wins, matches played, and win rates |
| `GET /api/players` | Run and credited wicket leaders, including per-season Orange and Purple Cap |
| `GET /api/venues` | Match totals by venue |
| `GET /api/toss` | Toss decisions and toss-winner outcomes |
| `GET /api/charts` | Filtered Plotly figure JSON, including team wins by season |
| `GET /api/data-quality` | Dataset presence, schema, and missing values |
| `POST /api/upload/matches` | Validate and store `matches.csv` |
| `POST /api/upload/deliveries` | Validate and store `deliveries.csv` |

Analytics GET endpoints accept repeatable filters, for example `?season=2024&team=CSK&team=MI`. The player endpoint and charts also accept repeatable `player` filters.

## Verification

With the Python requirements installed:

```powershell
python -m unittest discover -s backend\tests -v
```

With Node.js installed:

```powershell
cd frontend
npm run build
```
