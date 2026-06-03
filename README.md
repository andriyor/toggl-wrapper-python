# Native fullscreen Toggl timer (Qt / PySide6)

- **Idle** — pick a pinned project with **↑ / ↓** (wrap-around), **Enter** to
  start. The background reflects the selected project's color.
- **Running** — shows the project, description and a large elapsed-time clock.
  **Enter** (or the **Stop** button) stops the timer.
- **Esc** / **q** exits.

## Setup

```sh
cd native
uv sync
```

## Token

`TOGGL_TOKEN` environment variable

## Run

```sh
# from the native/ folder, with the venv active
uv run main.py        # or: python -m toggl

# or pass the token explicitly
TOGGL_API_TOKEN=your_token python toggl_timer.py
```

## Layout

`mian.py` is a thin launcher; the implementation lives in the `toggl`
package, split by concern:

| Module       | Responsibility                                                |
|--------------|---------------------------------------------------------------|
| `config.py`  | resolve the API token                                         |
| `api.py`     | blocking Toggl API v9 client                                  |
| `workers.py` | run blocking calls off the UI thread (`QThreadPool`)          |
| `utils.py`   | pure helpers (colour, time formatting)                        |
| `theme.py`   | colour scheme derived from a project's colour                 |
| `widgets.py` | the status / idle / running view pages                        |
| `window.py`  | controller wiring data, timers and views (a `QStackedWidget`) |
| `app.py`     | the `main()` entry point                                      |
