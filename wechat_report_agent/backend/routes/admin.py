from flask import request, jsonify, Blueprint
import logging

from wechat_report_agent.backend.db import get_db_conn
from wechat_report_agent.backend.auth import require_token

# Blueprint exported so app scanner can register routes
admin_bp = Blueprint('admin', __name__)
admin_bp = admin_bp
try:
    from wechat_report_agent.backend.ai_utils import call_ai
except Exception:
    call_ai = None

logger = logging.getLogger('backend.routes.admin')


def handle_clear_all_data(req):
    # wipe collected_article and collect_task, optionally prompt_template
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('DELETE FROM collected_article')
        c.execute('DELETE FROM collect_task')
        if req.json and req.json.get('wipe_templates'):
            c.execute('DELETE FROM prompt_template')
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.exception('clear all data failed: %s', e)
        return jsonify({'status': 'error', 'error': str(e)}), 500


def handle_test_models(req):
    data = req.json or {}
    prompt = data.get('prompt', '测试提示词')
    models = ['DeepSeek-R1', '豆包', '智谱AI']
    results = {}
    for m in models:
        try:
            if call_ai:
                results[m] = call_ai(m, prompt)
            else:
                results[m] = 'mock-response'
        except Exception as e:
            results[m] = f'error: {e}'
    return jsonify(results)


@admin_bp.route('/api/clear-all-data', methods=['POST'])
@require_token
def route_clear_all_data():
    return handle_clear_all_data(request)


@admin_bp.route('/api/test-models', methods=['POST'])
@require_token
def route_test_models():
    return handle_test_models(request)
