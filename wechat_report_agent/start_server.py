"""Simple entrypoint to run the backend via the new app factory.

Usage: `python wechat_report_agent/start_server.py`
"""
import os
from wechat_report_agent.backend.app import create_app


def main():
    app = create_app()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5001'))
    debug = os.environ.get('FLASK_DEBUG', '0') in ('1', 'true', 'True')
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    main()
