import time
import json
import logging
from flask import request, jsonify, Blueprint

logger = logging.getLogger('backend.routes.debug_client')

# Blueprint for debug client snapshot endpoints
debug_client_bp = Blueprint('debug_client', __name__)
debug_client_bp = debug_client_bp

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


# route handlers (register at module top-level so Blueprint sees them on import)
@debug_client_bp.route('/api/debug/client-menu', methods=['POST'])
def route_debug_client_menu_post():
    return handle_debug_client_menu_post(request)


@debug_client_bp.route('/api/debug/client-menu', methods=['GET'])
def route_debug_client_menu_get():
    return handle_debug_client_menu_get()
