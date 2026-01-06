"""API-related routes for the refactored backend.

Provides a small subset of protected endpoints migrated from the monolithic
module so they can be tested and extended independently.
"""
from flask import Blueprint, jsonify, request
import os
import json
import logging

from wechat_report_agent.backend.auth import require_token, write_instance_config
from wechat_report_agent.backend.ai_utils import _last_ai_debug

logger = logging.getLogger('backend.routes.api')

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/debug-ai-output', methods=['GET'])
@require_token
def api_debug_ai_output():
    """Return last AI raw output and normalized content for debugging."""
    return jsonify({'status': 'ok', 'last': _last_ai_debug})


@api_bp.route('/api/set-keys', methods=['POST'])
@require_token
def api_set_keys():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'error': 'invalid_payload'}), 400
    allowed_prefixes = ('DEEPSEEK', 'DOUBAO', 'ZHIPUAI', 'REPORT', 'QDRANT', 'DEEPSEEK_EMBED')
    updates = {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str) and any(k.startswith(p) for p in allowed_prefixes)}
    if not updates:
        return jsonify({'status': 'error', 'error': 'no_valid_keys_provided'}), 400
    try:
        write_instance_config(updates)
        return jsonify({'status': 'ok', 'written': list(updates.keys())})
    except Exception as e:
        logger.exception('failed to write instance config')
        return jsonify({'status': 'error', 'error': str(e)}), 500


@api_bp.route('/api/reload-instance-config', methods=['POST', 'GET'])
@require_token
def api_reload_instance_config():
    inst_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'config.json')
    inst_path = os.path.abspath(inst_path)
    if not os.path.exists(inst_path):
        return jsonify({'status': 'error', 'error': 'config_not_found', 'path': inst_path}), 404
    try:
        with open(inst_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception as e:
        logger.exception('failed to read instance config')
        return jsonify({'status': 'error', 'error': 'read_failed', 'details': str(e)}), 500

    injected = {}
    for k, v in cfg.items():
        if isinstance(k, str) and isinstance(v, str):
            os.environ[k] = v
            if len(v) > 12:
                masked = v[:4] + '...' + v[-4:]
            else:
                masked = v[:2] + '...' if len(v) > 4 else '***'
            injected[k] = masked

    logger.info('Reloaded instance config and injected keys: %s', ','.join(list(injected.keys())))
    return jsonify({'status': 'ok', 'injected': injected})
