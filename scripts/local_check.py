"""Read-only local diagnostic. Does not initialize, reset, or change the database."""
import importlib.metadata
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]

def inspect_database(path):
    if not path.is_file():
        raise ValueError('Database is missing. Run SETUP_WINDOWS.bat or the documented init-db command.')
    try:
        with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as db:
            counts = {name:db.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                      for name in ('users','assets','issues')}
            if not counts['users']:
                raise ValueError('Database has no accounts. Use the create-user CLI; no records were changed.')
            return counts
    except sqlite3.DatabaseError as error:
        raise ValueError('Database is unreadable or incomplete. Preserve it and check the setup instructions.') from error

def main():
    print('AssetGuard local diagnostic')
    print('Python:',sys.version.split()[0])
    print('Project folder:',ROOT)
    try:
        if sys.version_info[:2] != (3,12):
            raise ValueError('Use Python 3.12 for the verified configuration.')
        print('Flask:',importlib.metadata.version('Flask'))
        counts=inspect_database(ROOT/'instance'/'tracker.sqlite3')
        print('Saved records:',', '.join(f'{key}={value}' for key,value in counts.items()))
        print('Local checks passed. Start the server, then open http://127.0.0.1:5000.')
        return 0
    except (ValueError,importlib.metadata.PackageNotFoundError) as error:
        print('CHECK FAILED:',error)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
