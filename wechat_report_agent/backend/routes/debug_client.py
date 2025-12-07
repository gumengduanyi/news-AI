import time
import json
import logging
from flask import request, jsonify

logger = logging.getLogger('backend.routes.debug_client')

# module-level storage for last client menu (keeps parity with monolith behavior)
_last_client_menu = None


def handle_debug_client_menu_post(req):
    global _last_client_menu
    try:
        payload = req.get_json(force=True)
    except Exception:
        payload = None
    try:
        payload_json = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        payload_json = None
    _last_client_menu = {
        'time': time.time(),
        'payload': payload,
        'payload_json': payload_json
    }
    return jsonify({'status': 'ok'})


def handle_debug_client_menu_get(req=None):
    try:
        if _last_client_menu is None:
            return jsonify({'status': 'empty', 'last': None})
        return jsonify({'status': 'ok', 'last': _last_client_menu})
    except Exception:
        return jsonify({'status': 'error', 'error': 'failed_to_return_snapshot'}), 500
