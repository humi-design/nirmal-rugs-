"""Phusion Passenger WSGI entrypoint for cPanel.

cPanel requirement: this file must sit in the application root
(the same folder as app.py) and expose a callable named ``application``.
The virtualenv and app root are configured in "Setup Python App".
Environment variables are loaded from .env when present.
"""

import os

try:
    from dotenv import load_dotenv
    basedir = os.path.dirname(os.path.abspath(__file__)) or "."
    load_dotenv(os.path.join(basedir, ".env"))
except Exception:
    pass

from app import create_app

application = create_app()

# Useful for cPanel support to verify the deploy.
if __name__ == "__main__":
    application.run()
