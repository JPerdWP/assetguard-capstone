import csv
import io
import sqlite3
import pytest
from bs4 import BeautifulSoup
from werkzeug.security import check_password_hash
from app import create_app

@pytest.fixture
def app(tmp_path):
    a=create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.sqlite3'),'SECRET_KEY':'test-secret'})
    r=a.test_cli_runner().invoke(args=['init-db','--demo'])
    assert r.exit_code==0,r.output
    return a
@pytest.fixture
def client(app): return app.test_client()
def token(c):
    with c.session_transaction() as s: return s['csrf']
def post(c,path,data=None): return c.post(path,data={**(data or {}),'csrf':token(c)})
def login(c,role='admin'):
    c.get('/login')
    r=post(c,'/login',{'username':role,'password':'CapstoneAdmin!2026' if role=='admin' else 'CapstoneViewer!2026'})
    assert r.status_code==302

def one(a,sql,params=()):
    with a.app_context(): return a.db().execute(sql,params).fetchone()
def asset(c,**changes):
    return post(c,'/assets/new',{**dict(tag='AST-007',name='Test laptop',employee='Test employee',os='Windows 11',support='Supported'),**changes})
def issue(c,**changes):
    return post(c,'/issues/new',{**dict(asset_id=1,title='Test finding',description='Manual finding',severity='High',owner_id=1),**changes})

def test_seed_password_hash(app):
    assert one(app,'SELECT COUNT(*) FROM assets')[0]==6
    assert one(app,'SELECT COUNT(*) FROM issues')[0]==5
    h=one(app,"SELECT password_hash FROM users WHERE username='admin'")[0]
    assert h!='CapstoneAdmin!2026' and check_password_hash(h,'CapstoneAdmin!2026')
@pytest.mark.parametrize('path',['/','/assets','/assets/1','/issues','/issues/1','/export/assets.csv'])
def test_anonymous_redirect(client,path):
    r=client.get(path); assert r.status_code==302 and '/login' in r.location

def test_bad_login_rotation_logout(client):
    client.get('/login'); old=token(client)
    assert post(client,'/login',dict(username='admin',password='wrong')).status_code==401
    login(client); assert token(client)!=old
    assert client.get('/').status_code==200
    assert post(client,'/logout').status_code==302
    assert client.get('/').status_code==302

def test_throttle(client):
    client.get('/login')
    for _ in range(5): assert post(client,'/login',dict(username='missing',password='wrong')).status_code==401
    assert post(client,'/login',dict(username='admin',password='CapstoneAdmin!2026')).status_code==429
@pytest.mark.parametrize('path',['/assets/new','/assets/1/edit','/issues/new'])
def test_viewer_form_denied(client,path):
    login(client,'viewer'); assert client.get(path).status_code==403
@pytest.mark.parametrize('path',['/assets/new','/assets/1/edit','/issues/new','/issues/1'])
def test_viewer_post_denied(app,client,path):
    login(client,'viewer'); before=one(app,'SELECT COUNT(*) FROM activity')[0]
    assert post(client,path,{'name':'changed'}).status_code==403
    assert one(app,'SELECT COUNT(*) FROM activity')[0]==before

def test_viewer_reads(client):
    login(client,'viewer')
    for p in ['/','/assets','/assets/1','/issues','/issues/1','/export/assets.csv']: assert client.get(p).status_code==200
    assert b'Add asset' not in client.get('/assets').data
@pytest.mark.parametrize('path',['/login','/logout','/assets/new','/issues/1'])
def test_csrf(client,path):
    login(client); assert client.post(path,data={}).status_code==400

def test_asset_create_edit_search_persistence(app,client):
    login(client); assert asset(client).status_code==302
    row=one(app,"SELECT * FROM assets WHERE tag='AST-007'")
    assert row['employee']=='Test employee'
    assert b'Test laptop' in client.get('/assets?q=AST-007').data
    assert post(client,f"/assets/{row['id']}/edit",dict(tag='AST-007',name='Renamed laptop',employee='New owner',os='Ubuntu',support='Unknown')).status_code==302
    other=app.test_client(); login(other)
    assert b'Renamed laptop' in other.get('/assets?q=Renamed').data
@pytest.mark.parametrize('change',[{'tag':'ast-001'},{'tag':''},{'name':'x'*101},{'support':'Fake'},{'employee':' '}])
def test_invalid_asset(app,client,change):
    login(client); assert asset(client,**change).status_code==422
    assert one(app,'SELECT COUNT(*) FROM assets')[0]==6

def test_search_sql_wildcards(client):
    login(client)
    for q in ["' OR 1=1 --",'%']: assert b'No assets match' in client.get('/assets',query_string={'q':q}).data

def test_xss_escaped(client):
    login(client); asset(client,name='<script>alert(1)</script>')
    text=client.get('/assets').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in text and '&lt;script&gt;' in text

def test_end_to_end(app,client):
    login(client); assert asset(client).status_code==302
    aid=one(app,"SELECT id FROM assets WHERE tag='AST-007'")[0]
    r=issue(client,asset_id=aid); assert r.status_code==302
    iid=int(r.location.rsplit('/',1)[-1])
    data=dict(status='In Progress',severity='High',owner_id=1,resolution='Review started')
    assert post(client,f'/issues/{iid}',data).status_code==302
    assert post(client,f'/issues/{iid}',{**data,'status':'Resolved','resolution':''}).status_code==422
    assert post(client,f'/issues/{iid}',{**data,'status':'Resolved','resolution':'Enabled and verified.'}).status_code==302
    row=one(app,'SELECT * FROM issues WHERE id=?',(iid,)); assert row['resolved_at'] and row['resolution']=='Enabled and verified.'
    soup=BeautifulSoup(client.get('/').data,'html.parser')
    assert [x.get_text(strip=True) for x in soup.select('.metrics strong')]==['7','4','2','2']
    assert 'AST-007' not in soup.select('.table-wrap')[0].get_text()
    assert post(client,f'/issues/{iid}',data).status_code==302
    assert one(app,'SELECT resolved_at FROM issues WHERE id=?',(iid,))[0] is None
@pytest.mark.parametrize('key,value',[('asset_id','9999'),('owner_id','2'),('severity','Urgent'),('title',''),('description','x'*3001)])
def test_invalid_issue(app,client,key,value):
    login(client); assert issue(client,**{key:value}).status_code==422
    assert one(app,'SELECT COUNT(*) FROM issues')[0]==5

def test_filters(client):
    login(client)
    text=client.get('/issues?severity=High&status=In+Progress').get_data(as_text=True)
    assert 'Endpoint protection needs review' in text and 'Pending security updates' not in text
    assert client.get('/issues?severity=Fake').status_code==400

def test_bad_update(app,client):
    login(client)
    assert post(client,'/issues/1',dict(status='Deleted',severity='High',owner_id=2,resolution='')).status_code==422
    r=one(app,'SELECT status,owner_id FROM issues WHERE id=1'); assert tuple(r)==('Open',1)

def test_csv_safe(client):
    login(client); asset(client,name='=1+1'); r=client.get('/export/assets.csv')
    rows=list(csv.reader(io.StringIO(r.get_data(as_text=True))))
    assert r.status_code==200 and 'attachment' in r.headers['Content-Disposition']
    assert len(rows)==8 and rows[-1][1]=="'=1+1"

def test_headers_cookie(client):
    login(client); r=client.get('/')
    assert r.headers['X-Frame-Options']=='DENY'
    assert r.headers['X-Content-Type-Options']=='nosniff'
    assert "script-src 'none'" in r.headers['Content-Security-Policy']
    assert r.headers['Cache-Control']=='no-store'
    cookie=post(client,'/logout').headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie

def test_404(client):
    login(client)
    for path in ['/assets/999','/issues/999','/assets/999/edit']: assert client.get(path).status_code==404

def test_db_constraints(app):
    with app.app_context():
        for sql in ["UPDATE issues SET status='Resolved' WHERE id=1",'UPDATE issues SET asset_id=999 WHERE id=1']:
            with pytest.raises(sqlite3.IntegrityError): app.db().execute(sql)
            app.db().rollback()

def test_cli(app):
    runner=app.test_cli_runner()
    assert runner.invoke(args=['init-db','--demo']).exit_code!=0
    assert one(app,'SELECT COUNT(*) FROM assets')[0]==6
    r=runner.invoke(args=['create-user','technician','--role','admin'],input='UniquePassword!2026\nUniquePassword!2026\n')
    assert r.exit_code==0,r.output
    assert one(app,"SELECT role FROM users WHERE username='technician'")[0]=='admin'
    assert runner.invoke(args=['create-user','weak','--role','viewer'],input='short\nshort\n').exit_code!=0
