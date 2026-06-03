"""Native fullscreen Toggl timer (Qt / PySide6).

A standalone desktop port of the web app's fullscreen mode. The package is
split by concern:

- :mod:`toggl.config`  — resolving the API token
- :mod:`toggl.api`     — the blocking Toggl API v9 client
- :mod:`toggl.workers` — running blocking calls off the UI thread
- :mod:`toggl.utils`   — pure helpers (colour, time formatting)
- :mod:`toggl.theme`   — colour scheme derived from a project's colour
- :mod:`toggl.widgets` — the idle / running / status view pages
- :mod:`toggl.window`  — the controller wiring data, timers and views together
- :mod:`toggl.app`     — the ``main()`` entry point

Unlike the browser version there is no ``/toggl`` proxy: a desktop app can call
the Toggl API directly, so requests go straight to https://api.track.toggl.com
with HTTP Basic auth (``token:api_token``).
"""
