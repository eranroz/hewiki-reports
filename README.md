This repository includes simple python scripts to create reports on pages in Hebrew Wikipedia.

# Reports
Scripts that requires access to database:
* sandboxMove.py - Pages moved from sandbox namespace to main namespace.
* workTemplate2.py - Pages that were marked with work template and no longer marked as so.


# Install
Set up virtual env: (recommended)
```console
python3 -m venv venv
. ./venv/bin/activate
```

Install dependencies:
```console
pip install -r requirements.txt
```

To set up database settings - see settings.py and [Toolforge/Database](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database)

To run on [Toolforge](https://wikitech.wikimedia.org/wiki/Help:Toolforge) you see example jobs.yaml