import os
import json
from flask import jsonify


def handle_token():
    # prefer environment REPORT_API_TOKEN, then instance/config.json, else default '1'
    token = os.environ.get('REPORT_API_TOKEN')
    if not token:
        try:
            cfg_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'config.json')
            cfg_path = os.path.abspath(cfg_path)
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    token = cfg.get('REPORT_API_TOKEN')
        except Exception:
            token = None

    if not token:
        token = '1'

    userInfo = {
        'username': 'admin',
        'role': ['admin'],
        'name': 'Developer'
    }

    return jsonify({'code': 200, 'data': {'token': token, 'userInfo': userInfo}})
