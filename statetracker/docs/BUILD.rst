Building the documentation
==========================

Install the package with the ``docs`` extra (from the ``statetracker`` directory)::

    pip install -e ".[docs]"

Then build the HTML docs:

- **Windows**: ``make.bat html``
- **Linux/macOS**: ``make html``

Output is in ``_build/html/``. Open ``_build/html/index.html`` in a browser.

Other targets: ``make.bat help`` (or ``make help``) lists all targets (e.g. ``clean``, ``html``, ``latexpdf``).
