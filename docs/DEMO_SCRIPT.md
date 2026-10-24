# Final presentation and live demonstration

This is a recording guide, not a completed YouTube video. Record with your own voice after reviewing the code and reproducing the workflow. Explain any AI assistance accurately.

## Opening: problem and motivation
“My project is a small business IT asset and security tracking system called AssetGuard. In IT support, device information and follow-up work can end up spread across spreadsheets and emails. I wanted to bring that information together so a technician can see the device, identify who owns the issue, and document the fix.”

## System and architecture
Show the architecture diagram in the report. Explain the browser, Flask routes, Jinja templates, role checks, and SQLite database. Mention that support and issue details are entered manually. This application does not scan a network or verify an endpoint's actual security condition.

## Live workflow (run the actual Flask app locally)
1. Start the server and sign in as admin. Show the six assets, four unresolved issues, two high/critical issues, and one resolved issue in a fresh demo database.
2. Open Asset inventory. Search AST-003 and show its device page. Clear the search.
3. Add AST-DEMO, Demo laptop, Demo employee, Windows 11, Supported. Explain unique tags and required fields. Inventory total becomes seven.
4. Record an issue for AST-DEMO: “Antivirus setting needs review,” description “Reported disabled during a manual check,” severity High, owner admin. Dashboard becomes seven assets, five unresolved issues, three high/critical issues, one resolved.
5. Open that issue. Change it to In Progress and add “Reviewing the configuration.” Save.
6. Try Resolved with blank notes. Show the validation message. Enter “Enabled approved protection and verified the setting.” Save again and show the completion date.
7. Return to overview. Counts should be seven assets, four unresolved issues, two high/critical issues, two resolved. The demo device drops out of Devices needing attention.
8. Export the asset CSV if time permits. Explain safe CSV handling and manual data quality.
9. Sign out and sign in as viewer. Show the read-only layout and explain that write restrictions are also checked on the server.
10. Show the pytest output and Git repository. Explain one meaningful test: attempting a direct viewer POST cannot change a record.

If a device/tag already exists, use a different demo tag. Do not reset or delete a database that contains work you need.

## Challenges and lessons
Use your own experience after running it. Possible discussion points to verify: keeping resolved status and completion dates consistent; distinguishing hidden buttons from server-side authorization; maintaining a small scope while still testing invalid data. Do not claim those were your personal challenges unless that is accurate.

## Closing
“The MVP covers the inventory-to-remediation workflow. Future versions could add read-only device imports, a web account-management interface, and a more detailed change history. For now, the main limitation is that the information depends on manual entry.”

## Recording and submission
Use the report diagrams and real running app, not the captured static views, for the live demonstration. Make sure your face/voice requirements follow the instructor's directions. Upload the completed recording to your own YouTube account, choose the visibility required by the course, and add its actual URL to the final report. Confirm the instructor can view it. No upload has been performed by this package.
