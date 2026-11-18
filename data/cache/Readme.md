# Cache (offline data)

This folder holds environment data saved locally, so the demo works without internet.

| File | What it is | Made by |
|---|---|---|
| `synthetic_environment_hourly.csv` | 90 days of hourly PM2.5, humidity, temperature and rainfall for a synthetic district | `data/generate_synthetic.py` |
| `open_meteo_<district>_<start>_<end>.json` | Raw Open-Meteo responses for real districts, saved when the backend fetches data | `backend/services/environment.py` |

All values in the synthetic file are **synthetic**, not real measurements.

Synthetic districts (names containing "synthetic") are never fetched from the internet.
Real responses are saved here so the same data can be replayed offline.

To rebuild the synthetic files, run from the `data/` folder:

    python generate_synthetic.py
