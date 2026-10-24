from pathlib import Path
import sqlite3
import subprocess
import pytest
from scripts.local_check import inspect_database
from scripts.git_preflight import inspect_repository


def run_git(root,*args):
    return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,text=True)


def repo(tmp_path):
    run_git(tmp_path,'init','-b','main')
    run_git(tmp_path,'config','user.name','Local tools test')
    run_git(tmp_path,'config','user.email','test@example.invalid')
    return tmp_path


def test_diagnostic_preserves_saved_records(tmp_path):
    p=tmp_path/'tracker.sqlite3'
    with sqlite3.connect(p) as db:
        for table in ['users','assets','issues']:
            db.execute(f'CREATE TABLE {table}(id INTEGER)')
            db.execute(f'INSERT INTO {table} VALUES(1)')
    original=p.read_bytes()
    assert inspect_database(p)==dict(users=1,assets=1,issues=1)
    assert p.read_bytes()==original


def test_diagnostic_missing_database_does_not_create_one(tmp_path):
    p=tmp_path/'missing.sqlite3'
    with pytest.raises(ValueError,match='missing'):inspect_database(p)
    assert not p.exists()


def test_diagnostic_empty_workspace_requires_account(tmp_path):
    p=tmp_path/'empty.sqlite3'
    with sqlite3.connect(p) as db:
        for name in ['users','assets','issues']:db.execute(f'CREATE TABLE {name}(id INTEGER)')
    with pytest.raises(ValueError,match='no accounts'):inspect_database(p)


@pytest.mark.parametrize('path',['instance/tracker.sqlite3','.env','local-results/results.xml'])
def test_preflight_detects_runtime_files_even_after_history_deletion(tmp_path,path):
    root=repo(tmp_path)
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('fictional-test-only')
    candidates,history=inspect_repository(root)
    assert path in candidates and not history
    run_git(root,'add',path);run_git(root,'commit','-m','Add test fixture')
    run_git(root,'rm',path);run_git(root,'commit','-m','Remove fixture from working tree')
    candidates,history=inspect_repository(root)
    assert path not in candidates and path in history


def test_preflight_ignores_local_state_without_hiding_source(tmp_path):
    root=repo(tmp_path)
    (root/'.gitignore').write_text('instance/\n.env\n')
    (root/'app.py').write_text('print("sample")\n')
    (root/'instance').mkdir();(root/'instance'/'tracker.sqlite3').write_text('local only')
    (root/'.env').write_text('local only')
    run_git(root,'add','.gitignore','app.py');run_git(root,'commit','-m','Source only')
    assert inspect_repository(root)==([],[])


def test_preflight_rejects_parent_repository(tmp_path):
    root=repo(tmp_path);child=root/'project';child.mkdir()
    with pytest.raises(ValueError,match='parent repository'):inspect_repository(child)
