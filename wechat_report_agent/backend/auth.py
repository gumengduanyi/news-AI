import os
import json
import logging
from flask import request, jsonify

logger = logging.getLogger('backend.auth')


def require_token(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        # 本地开发绕过
        if os.environ.get('DEV_AUTH_DISABLED') == '1':
            remote = request.remote_addr or ''
            if remote.startswith('127.') or remote == '::1' or remote == 'localhost':
                logger.warning('DEV_AUTH_DISABLED=1: skipping auth checks for local request from %s', remote)
                return func(*args, **kwargs)
            else:
                logger.info('DEV_AUTH_DISABLED=1 present but request remote_addr=%s not local; enforcing auth', remote)

        expected = os.environ.get('REPORT_API_TOKEN')
        if not expected:
            logger.error('REQUEST REJECTED: server missing REPORT_API_TOKEN (server misconfigured)')
            return jsonify({'status': 'error', 'error': 'server_misconfigured_missing_token'}), 500

        auth = request.headers.get('Authorization', '')
        token = None
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1].strip()

        if not token:
            token = request.args.get('token')
            if not token:
                try:
                    token = request.cookies.get('TOKEN')
                except Exception:
                    token = None

        if token != expected:
            provided = token or '<none>'
            masked = (provided[:4] + '...' + provided[-4:]) if len(provided) > 8 else provided
            logger.warning('AUTH FAILED: provided token=%s expected=***', masked)
            return jsonify({'status': 'error', 'error': 'invalid_or_missing_token'}), 401
        return func(*args, **kwargs)

    return wrapper


def write_instance_config(updates: dict):
    """Write selected keys to instance/config.json and set file perms to 600.

    Only string values are written. Existing keys will be updated/added.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inst_dir = os.path.join(base_dir, '..', 'instance')
    inst_dir = os.path.abspath(inst_dir)
    os.makedirs(inst_dir, exist_ok=True)
    cfg_path = os.path.join(inst_dir, 'config.json')
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cur = json.load(f)
        else:
            cur = {}
    except Exception:
        cur = {}
    for k, v in updates.items():
        if isinstance(v, str):
            cur[k] = v
    tmp = cfg_path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)
    os.replace(tmp, cfg_path)
    try:
        os.chmod(cfg_path, 0o600)
    except Exception:
        logger.debug('failed to chmod %s', cfg_path)
    for k, v in cur.items():
        if isinstance(v, str):
            os.environ[k] = v
