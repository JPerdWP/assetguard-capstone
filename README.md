# AssetGuard: Small Business IT Asset and Security Tracking System

CIT Capstone, John Paul Perdicaro, Fall Session 2 2026. Instructor: Nan Wang.
A local Flask/SQLite web application for one small business. All demo information is fictional.

## Start here on Windows
Install Python 3.12 and Git if they are not already installed. Extract this folder first; do not run inside the ZIP. Open Command Prompt in this folder.

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m flask --app app init-db --demo
.venv\Scripts\python.exe app.py
```
Open http://127.0.0.1:5000 in a browser. Leave Command Prompt open. Stop the server with Ctrl+C. Future starts only need the last command. Recommended shortcuts: run `SETUP_WINDOWS.bat` once, then `START_WINDOWS.bat`. Setup preserves existing data. Start uses installed dependencies without downloading them again. `CHECK_LOCAL_WINDOWS.bat` reports interpreter and database status.

## macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app init-db --demo
.venv/bin/python app.py
```

## Demo accounts
Only use these intentionally public demonstration credentials on your local machine with fictional data.

| Username | Password | Access |
| --- | --- | --- |
| admin | CapstoneAdmin!2026 | Create/edit assets, create/update issues, read/export |
| viewer | CapstoneViewer!2026 | Read dashboard, assets, issues, export CSV |

The `--demo` flag creates six devices and five issues. It refuses to load over existing users. Starting the server never resets the database. Do not delete your database to troubleshoot a login problem; preserve a backup first.

## Empty workspace instead of demo
Run `init-db` without `--demo`. Then create each account interactively:

```bat
.venv\Scripts\python.exe -m flask --app app create-user yourname --role admin
.venv\Scripts\python.exe -m flask --app app create-user manager --role viewer
```
Passwords are prompted twice and must contain at least 12 characters. No web-based user management or password reset is implemented. This command adds accounts; it does not change existing ones.

## Main features
- Add/edit/search assets; unique tags, employee, OS, support status.
- Link manual security findings to devices; choose severity and responsible administrator.
- Track Open / In Progress / Resolved, notes, and completion dates.
- Dashboard counts, affected devices, severity views, activity records.
- Administrator/viewer access enforced on the server, CSRF protection, password hashing.
- Small extras: safe CSV asset export and activity metadata (not an immutable audit trail).

The interface uses local custom CSS instead of the proposed Bootstrap dependency so the application works without a CDN. The rest of the proposed Python/Flask/SQLite/Jinja/pytest stack is retained.

## Local browser testing and GitHub

Follow [Local testing, then GitHub](docs/LOCAL_TESTING_AND_GIT.md) for the complete Windows walkthrough. Record your real browser results using [the blank acceptance worksheet](docs/LOCAL_ACCEPTANCE_WORKSHEET.md); save the filled copy under `local-results/`. Run tests before adding your source to Git. The guide includes fresh-folder Git initialization, a bundle-clone alternative, file review, and GitHub publication. Your SQLite database and virtual environment stay local.

## Run tests

On Windows, `RUN_TESTS_WINDOWS.bat` installs development requirements and writes your local results under `local-results/`.

```bat
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q --junitxml=local-results/test-results.xml
```
Create `local-results` first when running the command manually. On macOS/Linux substitute `.venv/bin/python`. Tests use temporary databases, not your workspace data. See `evidence/test-output.txt` and `docs/TEST_RESULTS.md` for the executed results.

## Documentation and submission
- `docs/Final_Project_Report.pdf`: final report matching all nine supplied sections.
- `docs/final_report_source.md`: editable report text.
- `docs/REQUIREMENTS_AND_DESIGN.md`: requirements, design, wireframes, test plan.
- `docs/LOCAL_TESTING_AND_GIT.md`: Windows setup, browser testing, and Git/GitHub workflow.
- `docs/LOCAL_ACCEPTANCE_WORKSHEET.md`: blank results form, initially marked Not run.
- `docs/USER_MANUAL.md`: step-by-step feature instructions.
- `docs/TECHNICAL_DOCUMENTATION.md`: architecture, schema, routes, security, backup/restore.
- `docs/DEMO_SCRIPT.md`: presentation outline and live demo walkthrough.
- `docs/SUBMISSION_CHECKLIST.md`: remaining student actions and honest contribution record.
- `evidence/`: raw pytest results, UI captures, performance observations, dependency versions.

## Git
For a folder already tested locally, follow `docs/LOCAL_TESTING_AND_GIT.md` to initialize and publish that same folder. This preserves your local edits. `CHECK_GIT_WINDOWS.bat` checks for runtime files in candidate paths and reachable Git history without changing the repository. It is not a full secret scanner.

The submission ZIP includes `assetguard.bundle`, a portable Git repository with a generated baseline commit. To obtain the complete repository, run `git clone assetguard.bundle assetguard` from the extracted ZIP's outer folder. Use the resulting `assetguard` folder in VS Code. The adjacent source folder is provided for convenient reading and running.

Create an empty repository in your GitHub account, then use the exact repository URL GitHub returns:

```sh
git remote add origin YOUR_ACTUAL_REPOSITORY_URL
git push -u origin main
```
Replace the placeholder above before running it. No remote repository has been created or pushed by this package. The baseline commit is labeled as assistant-generated; it is not a semester-long development history. Make future changes on feature branches and commit tested work with descriptive messages.

## Local deployment, data, and limits
The standard entry point binds only to 127.0.0.1 with debugging disabled. This is a local classroom MVP, not a public hosting setup. Do not expose demo accounts to a network. The session secret is generated at first use and stored in `instance/session.key` (or supplied through `SECRET_KEY`); database and secrets are excluded from Git and the ZIP. `COOKIE_SECURE=1` is available for a future HTTPS deployment, but the local HTTP demo must leave it unset.

Manual input does not prove the current security condition of a device. There is no automated scanner, agent, live telemetry, MFA, password-reset workflow, durable distributed rate limiter, pagination, multi-company support, or tamper-proof audit history. Device deletion is intentionally not implemented to preserve linked issues. User acceptance testing and the student's final recorded presentation remain to be completed.

## AI assistance
ChatGPT was used as a supporting tool to build on the project idea and help with coding, troubleshooting, testing, and preparing documentation and the report. Review the code, reproduce the tests, and explain the design in your own words before submission. Do not present generated reflection or contribution notes as a personal experience you have not verified.
