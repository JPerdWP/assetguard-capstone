"""Read-only Git check for accidental runtime files; not a general secret scanner."""
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def runtime_file(name):
    parts=PurePosixPath(name.replace('\\','/')).parts
    if any(p in {'instance','.venv','venv','__pycache__','.pytest_cache','local-results','exports','backups'} for p in parts):
        return True
    leaf=parts[-1].lower() if parts else ''
    return (leaf in {'.env','session.key'} or leaf.startswith('.env.') and leaf!='.env.example'
            or leaf.endswith(('.sqlite3','.sqlite','.db','.pem','.key')))


def git(root,*args):
    return subprocess.run(['git','-C',str(root),*args],text=True,capture_output=True,check=True).stdout


def inspect_repository(root):
    top=Path(git(root,'rev-parse','--show-toplevel').strip()).resolve()
    if top!=root.resolve():
        raise ValueError('Run this from the project repository, not a parent repository containing other work.')
    candidates=set(filter(None,git(root,'ls-files','-z','--cached','--others','--exclude-standard').split('\0')))
    leaked=sorted(p for p in candidates if runtime_file(p))
    history=[]
    try:
        objects=git(root,'rev-list','--objects','--all').splitlines()
    except subprocess.CalledProcessError:
        objects=[]
    for item in objects:
        pieces=item.split(' ',1)
        if len(pieces)==2 and runtime_file(pieces[1]):history.append(pieces[1])
    return leaked,sorted(set(history))


def main():
    try:
        candidate,history=inspect_repository(ROOT)
        if candidate or history:
            for path in candidate:print('Runtime file in candidate/tracked files:',path)
            for path in history:print('Runtime file in Git history:',path)
            print('CHECK FAILED. Do not push until those files are reviewed. No Git files were changed.')
            return 1
        print('Runtime-file check passed for candidate files and reachable Git history.')
        print('Review git diff --cached yourself for credentials and real data; this is not a full secret scanner.')
        return 0
    except FileNotFoundError:
        print('Install Git, then open a new terminal.')
    except (ValueError,subprocess.CalledProcessError) as error:
        print('CHECK FAILED:',str(error))
        print('Use the local-to-Git guide to initialize this folder or clone the bundle first.')
    return 1

if __name__=='__main__':
    raise SystemExit(main())
