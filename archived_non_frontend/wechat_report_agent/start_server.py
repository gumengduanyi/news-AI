"""Simple entrypoint to run the backend via the new app factory.

Usage: `python wechat_report_agent/start_server.py` (works from repo root
or from inside the `wechat_report_agent/` directory).
"""
import os
import sys

# Make running the script directly from inside the package directory work.
# When executed as a script from `wechat_report_agent/`, the package
# parent (repo root) is not on sys.path, so `wechat_report_agent` cannot
# be imported. Ensure the repository root is on sys.path first.
_THIS_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Prefer explicit package import; fall back to a direct subpackage import
# so the script works regardless of current working directory.
try:
    from wechat_report_agent.backend.app import create_app
except Exception:
    from backend.app import create_app


def main():
    app = create_app()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5001'))
    debug = os.environ.get('FLASK_DEBUG', '0') in ('1', 'true', 'True')
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    main()
