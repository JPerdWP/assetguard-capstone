# Local testing, then GitHub

Use this guide on your Windows computer. It covers the real application, not the screenshots in the report. No step pushes files or publishes anything automatically.

## A. Extract and prepare
1. Download the latest AssetGuard_Final_Project.zip. Right-click it > Extract All.
2. Use a normal local project folder, for example `C:\Projects\AssetGuard`. Avoid running inside the ZIP or copying a virtual environment from another machine.
3. Open the extracted `capstone-system` folder. It contains app.py and the Windows shortcuts. Keep this same folder for local testing and the Git steps below.
4. Install Python 3.12 with the Windows launcher and Git for Windows if needed. Close and reopen Command Prompt after installation.
5. Double-click SETUP_WINDOWS.bat. It creates a Python 3.12 virtual environment, installs runtime requirements, and loads the fictional demo only if no database exists. Existing data is retained. It finishes with a read-only diagnostic.
6. Double-click START_WINDOWS.bat. Open http://127.0.0.1:5000 in Chrome or Edge and leave the terminal open. Ctrl+C stops the server. Starting it again does not reset your records.

If you prefer Command Prompt, change to the source folder and run:

```bat
SETUP_WINDOWS.bat
START_WINDOWS.bat
```

Do not run both start commands at once. If port 5000 is already in use, stop the existing instance. For a deliberate alternate port, run `.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5001` and open that port instead.

Demo administrator: admin / CapstoneAdmin!2026
Demo viewer: viewer / CapstoneViewer!2026
These are public demonstration credentials for fictional local data only.

## B. Verify the actual browser workflow
Open docs/LOCAL_ACCEPTANCE_WORKSHEET.md and record results while testing. Keep the master worksheet unmarked; save your filled copy under local-results so private test notes are not accidentally published. Create that folder if needed.

Use a fresh demo database for the exact baseline counts below. If you already added data, use your current counts and record the differences; do not delete a database to force the example numbers.

1. Sign in as admin. Fresh baseline: 6 assets, 4 unresolved issues, 2 high/critical, 1 resolved.
2. Add AST-LOCAL-001, Local test laptop, Test employee, Windows 11, Supported. Expect 7 assets.
3. Search AST-LOCAL-001. Open it and change the employee to Updated employee. Confirm the edit persists after refreshing.
4. Record “Antivirus needs review,” description “Manual local test finding,” severity High, owner admin, on that device. Expect 5 unresolved issues and 3 high/critical.
5. Open the finding, set In Progress, add a note, and save.
6. Set Resolved with blank notes. Expect a validation error and no resolution.
7. Enter “Enabled approved protection and verified the setting,” then resolve. Expect a completion date; dashboard now 4 unresolved, 2 high/critical, 2 resolved. The test asset leaves Devices needing attention.
8. Reopen the issue with a note. Expect no completion date and 5 unresolved issues again. Resolve once more with notes so the session ends in the completed state.
9. Export CSV. Confirm it contains the test asset. Move the downloaded copy into exports if keeping it inside the project; exports is ignored by Git. The export contains all assets, not only search results.
10. Sign out and sign in as viewer. Browse all three sections. No Add/Edit/Save controls should appear. Opening /assets/new should display 403. Do not claim this alone proves all permissions: automated tests also exercise direct POSTs.
11. Try keyboard-only navigation and a narrow browser window. Record any overflow or confusing labels.
12. Stop and restart the application. Confirm the test device and resolution are still saved.

Take your own screenshots if useful, using fictional data. The report's existing evidence remains labeled with how it was captured. Do not mark Windows acceptance as passed in the report until this run is complete.

## C. Run automated checks
Double-click RUN_TESTS_WINDOWS.bat. It installs development requirements, runs the suite using temporary databases, and saves local output to local-results/test-output.txt and local-results/test-results.xml. It does not reset your live database or overwrite the shipped evidence.

Use CHECK_LOCAL_WINDOWS.bat to inspect the Python/Flask versions and saved record counts. The diagnostic is read-only. If it reports a missing or incomplete database, preserve the files and report the message rather than deleting the instance folder.

Expected automated result in this revision: 50 passing cases (42 application cases and 8 local-tool cases). Check the actual output, not just that the window opened. If a case fails, keep the output and resolve it before publication.

## D. Put this tested folder into Git
Git stores source/history on your computer. GitHub hosts a copy online. Your live SQLite data stays local.

Open Command Prompt inside the SAME capstone-system folder used above. If this folder was extracted directly from the ZIP, initialize it:

```bat
git init -b main
git config user.name "John Paul Perdicaro"
git config user.email "YOUR_GITHUB_EMAIL_OR_NOREPLY_ADDRESS"
.venv\Scripts\python.exe scripts\git_preflight.py
git status --short
```

Replace the email placeholder with the email or GitHub no-reply address you want attached to future commits. These config commands affect only this repository. A failed preflight needs review; it changes nothing itself.

Then review and create the first commit:

```bat
git add .
git diff --cached --stat
git diff --cached
.venv\Scripts\python.exe scripts\git_preflight.py
git commit -m "Add tested AssetGuard capstone application"
```

Check that instance/, .venv/, local-results/, exports/, backups/, and .env are absent from staged files. The preflight also detects common runtime file paths in reachable Git history, but it is not a general secret scanner. Read the staged diff for personal data, tokens, or credentials. The documented demo account passwords are intentionally part of the fictional seed.

If you previously cloned assetguard.bundle, you already have Git history: skip `git init` and use `git status` first. Commit your changes with a message describing what changed. The bundle is an alternative starting point; do not clone it over your tested source folder or move an existing .venv into a clone.

## E. Publish to GitHub
1. In your own GitHub account create an empty repository, such as assetguard-capstone. Choose the visibility required for your course. Leave README, .gitignore, and license initialization unchecked because they already come from your local files.
2. Copy the HTTPS repository URL GitHub provides. In your source folder run the commands below after replacing the placeholder:

```bat
git remote add origin YOUR_ACTUAL_GITHUB_REPOSITORY_URL
git remote -v
git push -u origin main
```

Complete any GitHub authentication in its normal browser/credential flow. Do not put a token in source files or paste it into this chat. If origin already exists, inspect `git remote -v` before changing it; do not add a second origin or overwrite an unrelated remote. If GitHub rejects the push due to existing remote commits, preserve both histories and resolve that situation before proceeding; do not force-push as a shortcut.

3. Open the repository on GitHub and confirm source, tests, and docs are visible, while runtime data and secrets are absent.
4. Add the real repository URL to report section 9 in docs/final_report_source.md. Rebuild the report with `.venv\Scripts\python.exe docs\build_report.py` after development requirements are installed.
5. Commit the updated source and PDF, run the preflight, and push again. A GitHub repository does not host the running Flask app; another computer must clone, set up its own .venv, and initialize its own local database.

## F. Preserve data while moving computers
Git carries the source and documentation. Recreate the virtual environment on the destination machine. The fictional demo seed can recreate demo records. For work you need to retain, stop the server and make a private copy of instance/tracker.sqlite3 outside the repository, then follow the backup/restore instructions. Never commit that backup. The new machine can generate its own session key; existing browser sessions do not need to transfer.

## Official references
- GitHub: https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
- Python virtual environments: https://docs.python.org/3.12/library/venv.html
