from flask import request, jsonify, Blueprint
import logging

from wechat_report_agent.backend.db import get_db_conn, row_to_dict

# Blueprint for collect-related endpoints
collect_bp = Blueprint('collect', __name__)
collect_bp = collect_bp

logger = logging.getLogger('backend.routes.collect')


def handle_collect_result():
    """Return collected_article rows, optional filter by task query param.

    This mirrors the logic previously in the monolithic module so it can be
    called from the existing route during incremental migration.
    """
    task = request.args.get('task')
    conn = get_db_conn()
    c = conn.cursor()
    q = 'SELECT id, title, content, date, summary, source, create_time FROM collected_article'
    params = ()
    if task:
        q += " WHERE title LIKE ? OR content LIKE ?"
        like = f"%{task}%"
        params = (like, like)
    q += ' ORDER BY id DESC'
    try:
        c.execute(q, params)
        rows = [row_to_dict(r) for r in c.fetchall()]
    except Exception as e:
        logger.exception('failed to fetch collected_article: %s', e)
        rows = []
    finally:
        conn.close()
    return jsonify(rows)


@collect_bp.route('/api/collect/result', methods=['GET'])
def route_collect_result():
    return handle_collect_result()
