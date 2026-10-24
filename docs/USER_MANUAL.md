# User manual

## 1. Sign in
Start the app using README.md. Open http://127.0.0.1:5000 and enter a local account username and password. The demo administrator can change data; the viewer can only read/export. Five failed attempts from one address trigger a five-minute local throttle. Sessions expire after 30 minutes without activity.

## 2. Review the overview
Total assets counts all inventory records. Open issues includes both Open and In Progress. High priority counts unresolved High and Critical findings. Resolved counts completed issues. Severity cards link to the relevant issue list; that list can also include resolved issues unless the Status filter is applied. Devices needing attention lists only assets with unresolved issues. Support status is entered manually and does not automatically create a finding.

## 3. Add or edit an asset (administrator)
Choose Asset inventory > Add asset. Enter a unique tag (up to 40 characters), device name, assigned employee/team, operating system (each up to 100 characters), and support status. Save to open the device detail page. Use Edit asset to change those fields later. Tags are unique without regard to case. Use Unassigned for an unassigned device; required fields cannot be blank. Cancel returns to inventory without saving.

## 4. Find or export devices
Search by all or part of a tag, name, assigned employee, or operating system. Search treats percent and underscore as literal characters. Use Clear to return to all devices. Export CSV downloads the inventory's five primary fields, including all assets rather than only search results. Formula-like values are prefixed with an apostrophe for safer spreadsheet use. Export does not include issue details or passwords.

## 5. Record an issue (administrator)
Open a device and select Record issue, or use the Security issues page. Select an existing asset, enter a title (up to 150 characters) and description (up to 3,000), choose Low/Medium/High/Critical, and select a responsible administrator. Save. The system creates an Open issue and records its reporting time automatically in UTC. If no assets exist, create one first.

## 6. Update remediation (administrator)
Open the issue. Change its status, severity, or responsible technician, and write progress notes. Save changes. To mark Resolved, provide meaningful resolution notes; a blank note is rejected. The completion date is automatic. Editing an already resolved item keeps its original completion date. Reopening removes that date and retains the submitted notes. The notes box is a current record, not an append-only comment thread; saving replaces the previous text.

## 7. Viewer access
Viewer accounts can browse every read page, filter issues, and export assets. They cannot add/edit assets or create/update issues, even by posting directly to a write URL. Only administrators appear in the technician assignment dropdown.

## 8. Validation and sign out
Errors appear above the form. Correct the named fields and save again. If a form expires, reload and enter the changes again. Use the sign-out arrow beside your account name when finished. Unsaved edits are discarded on navigation. Passwords and user accounts are managed through the CLI described in README.md.

## 9. Protect your work
The SQLite database persists between restarts. Follow the backup procedure in TECHNICAL_DOCUMENTATION.md before moving the project or changing environments. Do not publish the instance folder. The demo labels are fictional examples, not verified vulnerability assessments.
