# Requirements and design

## Problem and users
Small business IT staff need a shared view of device ownership and manual security findings. The single-business MVP supports administrators (technicians) and viewers (managers). No external client data is used.

## Functional requirements and acceptance criteria
| ID | User story / requirement | Acceptance evidence |
| --- | --- | --- |
| FR-01 | As an administrator, add/edit a device with a unique tag, name, employee, OS, support state. | Create/edit/search persistence test and five invalid-asset cases. |
| FR-02 | As either role, search assets and view linked issues. | Search, read-access, and record-not-found tests. |
| FR-03 | As an administrator, link a manual finding to an existing device and admin owner. | End-to-end creation and invalid foreign-key/owner tests. |
| FR-04 | As an administrator, select a defined severity and status. | Valid workflow and invalid-selection tests. |
| FR-05 | As an administrator, resolve an issue with notes and an automatic completion timestamp. | Resolution rejection/acceptance and reopening in end-to-end test. |
| FR-06 | As a manager, review accurate counts and affected devices. | Dashboard totals and affected-list assertions. |
| FR-07 | As a viewer, read records without write access. | Form GET and direct POST permission cases. |
| FR-08 | As either role, export an inventory CSV. | Header, row-count, and formula-safety test. |
| FR-09 | As an administrator, inspect recent activity metadata. | Workflow generates actor-linked events; viewer-post tests assert no event changes. |

## Non-functional requirements
- NFR-01 Security: all POSTs require CSRF tokens; server enforces roles; SQL values are parameterized; templates escape user content; passwords are hashed.
- NFR-02 Privacy: only fictional sample data ships; database, generated session key, and environment files are excluded from version control and distribution.
- NFR-03 Data integrity: unique case-insensitive tags, foreign keys, controlled statuses/severities, and the resolution consistency constraint.
- NFR-04 Usability: visible labels and error summaries, keyboard-accessible links/forms, responsive CSS, and text labels in addition to severity colors. Full accessibility compliance has not been certified.
- NFR-05 Performance target: dashboard response under one second for the six-device/five-issue seed, measured using a local Flask test client; no load or production scalability claim.
- NFR-06 Reproducibility: Python 3.12, pinned runtime requirements, temporary test databases, and setup instructions tested in a clean virtual environment.
- NFR-07 Persistence: saved records remain after a new connection/session. SQL transaction failures roll back instead of partially logging a change.

## Architecture
Browser -> Flask routing -> authentication + CSRF + role checks -> validation -> parameterized SQLite queries -> Jinja HTML -> browser.
Flask serves local CSS. No external API, JavaScript framework, or CDN is required. Cookie sessions contain only the user ID, CSRF token, and session metadata; permissions are reloaded from SQLite on each request.

## Data model
USERS 1--many ISSUES through owner_id; ASSETS 1--many ISSUES through asset_id; USERS 1--many ACTIVITY through actor_id. Activity entity/entity_id identifies an asset or issue logically but is not a polymorphic foreign key. See app.py SCHEMA for exact SQL and docs/Final_Project_Report.pdf for the diagram.

## UI wireframes
- Sign-in: product introduction | username + password + error summary + sign-in action.
- Overview: sidebar; heading/action; four metric cards; severity cards/workflow help; affected-assets table; recent activity.
- Inventory: heading/add; search/export toolbar; device table; asset detail page with linked findings.
- Record forms: heading/back link; validation summary; labeled fields; save/cancel.
- Issue detail: finding/asset/history panel | status/severity/owner/notes panel. Viewer gets readable notes instead of mutation controls.
These textual wireframes describe the implemented layouts. The report includes actual rendered UI views.

## Test plan
Use pytest with a fresh temporary SQLite database per case and the documented demo seed. Positive coverage: authentication, CRUD operations in scope, filtering, exports, resolution, reopening, dashboard calculations, account creation. Negative coverage: invalid input, duplicate tags, nonexistent foreign keys, missing CSRF, unauthenticated access, direct viewer writes, HTML injection, SQL-style searches, invalid filters, weak CLI passwords, and repeat seed loading. Human acceptance run: use the demo script locally and check keyboard navigation and a narrow browser window. Do not mark that human run complete until it is performed.

## Scope boundary
No scanner, endpoint agent, automated patch-state detection, cloud tenant, email integration, real-time monitoring, or AI-generated risk score. No deletion, web account administration, MFA, password reset, pagination, or durable audit snapshots in the MVP.
