# TripWise backend

Flask API and SQLAlchemy models for TripWise. From this folder, create a
virtual environment and install dependencies:

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py run.py
```

The backend runs on http://127.0.0.1:5000.

Run API integration tests with `py -m unittest discover -s tests -v`. See the
project root README for environment variables, route details, planning algorithm,
and sample-data limitations. `FLASK_DEBUG` defaults to false.

Health endpoint:

```text
GET /api/health
```
