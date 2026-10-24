"""Small Business IT Asset and Security Tracking System.
Run `flask --app app init-db --demo`, then `python app.py` for a local demo.
"""
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path
import csv
import io
import os
import secrets
import sqlite3
import time

import click
from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for, Response)
from werkzeug.security import check_password_hash, generate_password_hash

SEVERITIES = ('Low', 'Medium', 'High', 'Critical')
STATUSES = ('Open', 'In Progress', 'Resolved')
SUPPORT = ('Supported', 'Unsupported', 'Unknown')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','viewer'))
);
CREATE TABLE IF NOT EXISTS assets (
 id INTEGER PRIMARY KEY, tag TEXT NOT NULL UNIQUE COLLATE NOCASE,
 name TEXT NOT NULL, employee TEXT NOT NULL, os TEXT NOT NULL,
 support TEXT NOT NULL CHECK(support IN ('Supported','Unsupported','Unknown')),
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS issues (
 id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL REFERENCES assets(id),
 title TEXT NOT NULL, description TEXT NOT NULL,
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 status TEXT NOT NULL CHECK(status IN ('Open','In Progress','Resolved')),
 owner_id INTEGER NOT NULL REFERENCES users(id), reported_at TEXT NOT NULL,
 resolved_at TEXT, resolution TEXT NOT NULL DEFAULT '',
 CHECK((status='Resolved' AND resolved_at IS NOT NULL AND length(trim(resolution))>0)
 OR (status!='Resolved' AND resolved_at IS NULL))
);
CREATE INDEX IF NOT EXISTS issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS issues_asset ON issues(asset_id);
CREATE TABLE IF NOT EXISTS activity (
 id INTEGER PRIMARY KEY, actor_id INTEGER NOT NULL REFERENCES users(id),
 action TEXT NOT NULL, entity TEXT NOT NULL, entity_id INTEGER NOT NULL,
 happened_at TEXT NOT NULL
);
'''


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / 'tracker.sqlite3'),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config.get('SECRET_KEY'):
        key = os.environ.get('SECRET_KEY')
        if not key:
            keyfile = Path(app.instance_path) / 'session.key'
            try:
                fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'w') as f:
                    f.write(secrets.token_hex(32))
            except FileExistsError:
                pass
            key = keyfile.read_text().strip()
        app.config['SECRET_KEY'] = key
    # Local-process throttle; not shared across workers. See known limitations.
    login_attempts = {}

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys = ON')
        return g.db

    app.db = db

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop('db', None)
        if connection is not None:
            connection.close()

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        if session.get('uid'):
            g.user = db().execute('SELECT id,username,role FROM users WHERE id=?',
                                  (session['uid'],)).fetchone()
        session.setdefault('csrf', secrets.token_urlsafe(32))
        if request.method == 'POST':
            supplied = request.form.get('csrf', '')
            if not supplied or not secrets.compare_digest(supplied, session['csrf']):
                abort(400, 'The form expired or is missing its security token. Reload and try again.')

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; style-src 'self'; img-src 'self' data:; "
            "script-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store'
        return response

    def logged_in(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapped

    def admin(fn):
        @wraps(fn)
        @logged_in
        def wrapped(*args, **kwargs):
            if g.user['role'] != 'admin':
                abort(403, 'Viewer accounts cannot change records.')
            return fn(*args, **kwargs)
        return wrapped

    def activity(action, entity, entity_id):
        db().execute('INSERT INTO activity(actor_id,action,entity,entity_id,happened_at) VALUES(?,?,?,?,?)',
                     (g.user['id'], action, entity, entity_id, now()))

    def get_asset(id):
        row = db().execute('SELECT * FROM assets WHERE id=?', (id,)).fetchone()
        if row is None:
            abort(404)
        return row

    def get_issue(id):
        row = db().execute('''SELECT i.*,a.tag,a.name AS asset_name,u.username AS owner
            FROM issues i JOIN assets a ON a.id=i.asset_id
            JOIN users u ON u.id=i.owner_id WHERE i.id=?''', (id,)).fetchone()
        if row is None:
            abort(404)
        return row

    def text_field(data, key, label, maximum, errors):
        value = data.get(key, '').strip()
        if not value or len(value) > maximum:
            errors.append(f'{label} is required and must be {maximum} characters or fewer.')
        return value

    def selection(data, key, options, label, errors):
        value = data.get(key, '')
        if value not in options:
            errors.append(f'Select a valid {label}.')
        return value

    @app.context_processor
    def constants():
        return dict(severities=SEVERITIES, statuses=STATUSES, support_options=SUPPORT)

    @app.template_filter('date')
    def short_date(value):
        return value[:10] if value else '-'

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            address = request.remote_addr or 'local'
            recent = [t for t in login_attempts.get(address, []) if time.monotonic()-t < 300]
            login_attempts[address] = recent
            if len(recent) >= 5:
                return render_template('login.html', error='Too many failed attempts. Try again in five minutes.'), 429
            username = request.form.get('username', '').strip()
            user = db().execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            if user and check_password_hash(user['password_hash'], request.form.get('password', '')):
                session.clear()
                session.update(uid=user['id'], csrf=secrets.token_urlsafe(32))
                session.permanent = True
                login_attempts.pop(address, None)
                return redirect(url_for('dashboard'))
            login_attempts[address].append(time.monotonic())
            return render_template('login.html', error='Invalid username or password.'), 401
        return render_template('login.html')

    @app.post('/logout')
    @logged_in
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @logged_in
    def dashboard():
        counts = {s: 0 for s in SEVERITIES}
        for row in db().execute("SELECT severity,COUNT(*) n FROM issues WHERE status!='Resolved' GROUP BY severity"):
            counts[row['severity']] = row['n']
        assets = db().execute('SELECT COUNT(*) FROM assets').fetchone()[0]
        resolved = db().execute("SELECT COUNT(*) FROM issues WHERE status='Resolved'").fetchone()[0]
        affected = db().execute('''SELECT a.id,a.tag,a.name,COUNT(i.id) AS count,
            SUM(CASE WHEN i.severity IN ('Critical','High') THEN 1 ELSE 0 END) AS urgent
            FROM assets a JOIN issues i ON i.asset_id=a.id AND i.status!='Resolved'
            GROUP BY a.id ORDER BY urgent DESC,count DESC,a.tag''').fetchall()
        recent = db().execute('''SELECT x.*,u.username FROM activity x
            JOIN users u ON u.id=x.actor_id ORDER BY x.id DESC LIMIT 6''').fetchall()
        return render_template('dashboard.html', counts=counts, total_assets=assets,
            resolved=resolved, affected=affected, recent=recent)

    @app.get('/assets')
    @logged_in
    def assets():
        query = request.args.get('q', '').strip()[:100]
        # Escape wildcard characters so searches match the text the user typed.
        term = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        rows = db().execute('''SELECT a.*,COUNT(CASE WHEN i.status!='Resolved' THEN 1 END) AS open_count
            FROM assets a LEFT JOIN issues i ON i.asset_id=a.id
            WHERE a.tag LIKE ? ESCAPE '\\' OR a.name LIKE ? ESCAPE '\\'
              OR a.employee LIKE ? ESCAPE '\\' OR a.os LIKE ? ESCAPE '\\'
            GROUP BY a.id ORDER BY a.tag''', (term,)*4).fetchall()
        return render_template('assets.html', assets=rows, query=query)

    @app.route('/assets/new', methods=['GET', 'POST'])
    @app.route('/assets/<int:id>/edit', methods=['GET', 'POST'])
    @admin
    def asset_form(id=None):
        asset = dict(get_asset(id)) if id else {}
        errors = []
        if request.method == 'POST':
            data = request.form
            asset = {k: text_field(data, k, label, n, errors) for k,label,n in
                     [('tag','Asset tag',40),('name','Device name',100),
                      ('employee','Assigned employee',100),('os','Operating system',100)]}
            asset['support'] = selection(data, 'support', SUPPORT, 'support status', errors)
            if not errors:
                try:
                    with db():
                        if id:
                            db().execute('UPDATE assets SET tag=?,name=?,employee=?,os=?,support=? WHERE id=?',
                                (*asset.values(),id))
                            saved_id = id
                        else:
                            saved_id = db().execute('INSERT INTO assets(tag,name,employee,os,support,created_at) VALUES(?,?,?,?,?,?)',
                                (*asset.values(),now())).lastrowid
                        activity('Updated' if id else 'Created', 'asset', saved_id)
                    flash('Asset saved.', 'success')
                    return redirect(url_for('asset_detail', id=saved_id))
                except sqlite3.IntegrityError:
                    errors.append('That asset tag already exists. Use a unique tag.')
        return render_template('asset_form.html', asset=asset, editing=id is not None, errors=errors), 422 if errors else 200

    @app.get('/assets/<int:id>')
    @logged_in
    def asset_detail(id):
        rows = db().execute('''SELECT i.*,u.username owner FROM issues i JOIN users u ON u.id=i.owner_id
            WHERE i.asset_id=? ORDER BY i.id DESC''', (id,)).fetchall()
        return render_template('asset_detail.html', asset=get_asset(id), issues=rows)

    @app.get('/issues')
    @logged_in
    def issues():
        severity = request.args.get('severity', '')
        status = request.args.get('status', '')
        if severity and severity not in SEVERITIES or status and status not in STATUSES:
            abort(400, 'Invalid issue filter.')
        rows = db().execute('''SELECT i.*,a.tag,u.username owner FROM issues i
            JOIN assets a ON a.id=i.asset_id JOIN users u ON u.id=i.owner_id
            WHERE (?='' OR severity=?) AND (?='' OR status=?)
            ORDER BY CASE severity WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,i.id DESC''',
            (severity,severity,status,status)).fetchall()
        return render_template('issues.html', issues=rows, severity=severity, status=status)

    @app.route('/issues/new', methods=['GET', 'POST'])
    @admin
    def issue_new():
        errors = []
        data = dict(request.form) if request.method == 'POST' else {'asset_id':request.args.get('asset_id','')}
        if request.method == 'POST':
            title = text_field(data,'title','Title',150,errors)
            description = text_field(data,'description','Description',3000,errors)
            severity = selection(data,'severity',SEVERITIES,'severity',errors)
            asset = db().execute('SELECT id FROM assets WHERE id=?',(data.get('asset_id'),)).fetchone()
            owner = db().execute("SELECT id FROM users WHERE id=? AND role='admin'",(data.get('owner_id'),)).fetchone()
            if not asset: errors.append('Select an existing asset.')
            if not owner: errors.append('Select an administrator as the responsible technician.')
            if not errors:
                with db():
                    id = db().execute('''INSERT INTO issues(asset_id,title,description,severity,status,owner_id,reported_at)
                        VALUES(?,?,?,?,?,?,?)''', (asset['id'],title,description,severity,'Open',owner['id'],now())).lastrowid
                    activity('Created','issue',id)
                flash('Security issue recorded.', 'success')
                return redirect(url_for('issue_detail',id=id))
        return render_template('issue_form.html', data=data, errors=errors,
            assets=db().execute('SELECT id,tag,name FROM assets ORDER BY tag').fetchall(),
            owners=db().execute("SELECT id,username FROM users WHERE role='admin' ORDER BY username").fetchall()), 422 if errors else 200

    @app.route('/issues/<int:id>', methods=['GET','POST'])
    @logged_in
    def issue_detail(id):
        issue = get_issue(id)
        errors = []
        data = dict(issue)
        if request.method == 'POST':
            if g.user['role'] != 'admin': abort(403, 'Viewer accounts cannot change records.')
            data = dict(request.form)
            status = selection(data,'status',STATUSES,'status',errors)
            severity = selection(data,'severity',SEVERITIES,'severity',errors)
            resolution = data.get('resolution','').strip()
            owner = db().execute("SELECT id FROM users WHERE id=? AND role='admin'",(data.get('owner_id'),)).fetchone()
            if not owner: errors.append('Select an administrator as the responsible technician.')
            if len(resolution)>3000: errors.append('Resolution notes must be 3000 characters or fewer.')
            if status == 'Resolved' and not resolution: errors.append('Add resolution notes before resolving the issue.')
            if not errors:
                resolved_at = (issue['resolved_at'] or now()) if status=='Resolved' else None
                with db():
                    db().execute('UPDATE issues SET status=?,severity=?,owner_id=?,resolution=?,resolved_at=? WHERE id=?',
                        (status,severity,owner['id'],resolution,resolved_at,id))
                    activity('Updated','issue',id)
                flash('Issue updated.', 'success')
                return redirect(url_for('issue_detail',id=id))
        history = db().execute("SELECT a.*,u.username FROM activity a JOIN users u ON u.id=a.actor_id WHERE entity='issue' AND entity_id=? ORDER BY a.id DESC",(id,)).fetchall()
        return render_template('issue_detail.html',issue=issue,data=data,errors=errors,history=history,
            owners=db().execute("SELECT id,username FROM users WHERE role='admin'").fetchall()), 422 if errors else 200

    @app.get('/export/assets.csv')
    @logged_in
    def export_assets():
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(['Asset tag','Device name','Assigned employee','Operating system','Support status'])
        for row in db().execute('SELECT tag,name,employee,os,support FROM assets ORDER BY tag'):
            # Avoid formula execution when a CSV is opened in spreadsheet software.
            writer.writerow([("'"+v if v.lstrip().startswith(('=','+','-','@')) else v) for v in row])
        return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=assets.csv'})

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error):
        return render_template('error.html',error=error),error.code

    @app.cli.command('init-db')
    @click.option('--demo', is_flag=True, help='Load fictional records and documented local demo accounts.')
    def init_db(demo):
        """Initialize without destroying existing records. Demo loading requires an empty DB."""
        db().executescript(SCHEMA)
        if demo:
            if db().execute('SELECT COUNT(*) FROM users').fetchone()[0]:
                raise click.ClickException('Demo requires an empty database; existing data was not changed.')
            seed(db())
        click.echo('Database initialized.' + (' Demo accounts: see README.md.' if demo else ' Create accounts with create-user.'))

    @app.cli.command('create-user')
    @click.argument('username')
    @click.option('--role', type=click.Choice(['admin','viewer']), required=True)
    @click.password_option(confirmation_prompt=True)
    def create_user(username, role, password):
        if not username.strip() or len(username)>80 or len(password)<12:
            raise click.ClickException('Username: 1-80 characters. Password: at least 12 characters.')
        try:
            with db():
                db().execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',
                    (username.strip(),generate_password_hash(password),role))
        except sqlite3.IntegrityError:
            raise click.ClickException('Username already exists.')
        click.echo('User created.')

    return app


def seed(db):
    """Fictional demonstration dataset. Never use these credentials for real data."""
    db.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',
        ('admin',generate_password_hash('CapstoneAdmin!2026'),'admin'))
    db.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',
        ('viewer',generate_password_hash('CapstoneViewer!2026'),'viewer'))
    devices = [
        ('AST-001','Reception laptop','Morgan Lee','Windows 11','Supported'),
        ('AST-002','Accounting desktop','Taylor Brooks','Windows 10','Unsupported'),
        ('AST-003','Sales laptop','Jordan Quinn','Windows 11','Supported'),
        ('AST-004','File server','IT team','Ubuntu Server 24.04 LTS','Supported'),
        ('AST-005','Office workstation','Casey Lane','Windows 11','Supported'),
        ('AST-006','Spare laptop','Unassigned','Windows 11','Unknown')]
    db.executemany('INSERT INTO assets(tag,name,employee,os,support,created_at) VALUES(?,?,?,?,?,?)',
        [(*d,now()) for d in devices])
    issues = [(2,'Unsupported operating system','Support status was entered manually for this demo; confirm lifecycle and any extended support before making a real assessment.','Critical','Open',''),
        (3,'Endpoint protection needs review','Technician reported that protection was disabled. Verify settings and re-enable approved protection.','High','In Progress','Review started; waiting for access to the device.'),
        (1,'Pending security updates','A technician recorded outstanding updates during a manual review.','Medium','Open',''),
        (4,'Backup restoration check due','Schedule and document a sample restore test.','Low','Open',''),
        (5,'Screen lock setting corrected','Workstation did not automatically lock during the initial review.','Low','Resolved','Enabled automatic locking and verified the setting.')]
    for asset,title,description,severity,status,resolution in issues:
        id=db.execute('''INSERT INTO issues(asset_id,title,description,severity,status,owner_id,reported_at,resolution,resolved_at)
            VALUES(?,?,?,?,?,1,?,?,?)''',(asset,title,description,severity,status,now(),resolution,now() if status=='Resolved' else None)).lastrowid
        db.execute("INSERT INTO activity(actor_id,action,entity,entity_id,happened_at) VALUES(1,'Seeded','issue',?,?)",(id,now()))
    db.commit()


if __name__ == '__main__':
    create_app().run(host='127.0.0.1',port=5000,debug=False)
