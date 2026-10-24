# Technical documentation

## Files and execution
`app.py` contains the app factory, schema, validation helpers, routes, CLI, and demo seed. `templates/` contains Jinja views, `static/style.css` the offline stylesheet, and `tests/test_app.py` the pytest suite. Runtime state belongs under `instance/`; no runtime state is packaged. Python 3.12 was used for verification. A desktop browser is required for human use.

## Schema
- users: id PK; username UNIQUE NOCASE; password_hash; role CHECK(admin/viewer).
- assets: id PK; tag UNIQUE NOCASE; name; employee; os; support CHECK; created_at UTC.
- issues: id PK; asset_id FK; title; description; severity CHECK; status CHECK; owner_id FK; reported_at; resolved_at nullable; resolution. A CHECK requires a completion date and nonblank notes if resolved, and no completion date if unresolved. Indexes cover status and asset_id.
- activity: id PK; actor_id FK; action; entity; entity_id; happened_at. Metadata records who changed which entity and when. It does not retain before/after values and is not tamper-resistant.
Foreign-key enforcement is enabled on every connection. Queries use bound values; transactions include both the record update and its activity event. Seed-only support labels do not automatically infer real vendor lifecycle status.

## Routes
| Path | Method | Access / purpose |
| --- | --- | --- |
| /login | GET/POST | Anonymous login; POST requires CSRF token |
| /logout | POST | Signed-in session logout |
| / | GET | Both roles, aggregate dashboard |
| /assets | GET | Both roles, q search |
| /assets/new | GET/POST | Administrator, create |
| /assets/<id>/edit | GET/POST | Administrator, update |
| /assets/<id> | GET | Both roles, detail and linked issues |
| /issues | GET | Both roles, status/severity filters |
| /issues/new | GET/POST | Administrator, finding creation |
| /issues/<id> | GET/POST | Both roles read; administrator updates only |
| /export/assets.csv | GET | Both roles, all inventory fields |

## Security model
Werkzeug hashes passwords; no plaintext password column exists. Flask signs sessions with a locally generated random key or an environment-supplied SECRET_KEY. Cookie flags are HttpOnly and SameSite=Lax, with a 30-minute inactivity lifetime. Secure cookies are optional for a future HTTPS deployment; local HTTP uses them off. Login clears and rotates session/CSRF state. Server-side role lookup occurs on each request. CSRF tokens are required on every POST, including login/logout. CSP blocks scripts and framing, templates escape content, and response headers disable MIME sniffing and caching. Five failed logins from the same address within 300 seconds cause throttling in the current process. Request bodies are limited to 64 KiB.

The local limiter is not durable and is not suitable as a shared production defense. There is no MFA, password reset, account lock management, or enterprise authorization model. Filesystem access can modify SQLite and audit metadata. This is a local MVP, not a certified security product. No penetration test against an external host was performed.

## Operational procedures
1. Setup and initialize using README.md. Use `init-db` alone for an empty workspace, or `init-db --demo` for the fictional classroom demonstration. Re-running normal initialization is non-destructive. Demo seeding refuses to overwrite existing users.
2. To back up: stop the local server with Ctrl+C, then copy `instance/tracker.sqlite3` to a private, dated backup folder outside the repository. Stopping avoids inconsistent file copies.
3. To restore: stop the server; copy the current database to a separate recovery file; replace `instance/tracker.sqlite3` with your known backup; restart. Validate asset/issue counts and accounts. Never overwrite the only copy.
4. Keep `instance/session.key` private. If you change SECRET_KEY or regenerate the key, existing sessions become invalid; records remain in SQLite. Database backups contain employee names and password hashes and need protection.
5. Before dependency changes, create a Git branch, retain a database backup, install and test the new versions, and update requirements. Dependency security auditing is not included in this submission.

## Troubleshooting
- `py` not found: install Python 3.12 with the Windows launcher or substitute a verified `python` executable.
- `No module named flask`: install requirements with the same virtual-environment Python used to start the app.
- `no such table`: run the init-db command from this source folder before starting.
- Port 5000 in use: stop the conflicting local app, or run `python -m flask --app app run --host 127.0.0.1 --port 5001` and use that URL.
- Form expired: reload and re-enter unsaved changes. A login in another tab rotates the CSRF token.
- Viewer cannot save: expected behavior. Sign in with an administrator for data entry.
- Browser preview cannot run Python in the build environment: verify backend behavior through pytest and review rendered pages separately; complete a live browser smoke test on your own installed machine.

## Local testing helpers
SETUP_WINDOWS.bat prepares a Python 3.12 virtual environment and initializes the demo only if its database is absent. START_WINDOWS.bat runs the existing app without reinstalling packages. RUN_TESTS_WINDOWS.bat writes fresh results under ignored local-results/. scripts/local_check.py opens SQLite in read-only mode. scripts/git_preflight.py inspects candidate file paths and reachable Git history for common runtime files; it does not read secret values or mutate the repository. See LOCAL_TESTING_AND_GIT.md for the full handoff process.
