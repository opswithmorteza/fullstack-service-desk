# Full-stack Service Desk

A working portfolio demonstration by Morteza Rajabi: HTML/CSS/JavaScript frontend, Python JSON API and SQLite persistence. Create incidents, filter by status and close them. No third-party Python dependencies.

```sh
python -m unittest -v
python app.py
```

Open http://127.0.0.1:8090. Data is stored in `service-desk.sqlite3`, which must not be committed. Set `DB_PATH` to choose another location. Tests use temporary databases.

## API

- `GET /api/incidents`: list incidents
- `POST /api/incidents`: create with JSON `title` and `priority` (low/medium/high)
- `PATCH /api/incidents/{id}`: update JSON `status` (open/closed)
- `GET /health`: status

The default host is loopback. The demo intentionally has no authentication and is not a production ticketing system. Do not expose it publicly without adding authentication, authorization, TLS, CSRF/origin controls, backups and an appropriate production server. Stored user text is rendered with DOM textContent, and SQL values are parameterized. This demo is Python/JavaScript; it does not claim implementations in every programming language.
