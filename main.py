#!/usr/bin/env python3
"""Entry point for the native fullscreen Toggl timer.

The implementation lives in the :mod:`toggl` package; this thin launcher keeps
the documented ``python toggl_timer.py`` command working. You can also run the
package directly with ``python -m toggl``.
"""

from toggl.app import main

if __name__ == "__main__":
    main()
