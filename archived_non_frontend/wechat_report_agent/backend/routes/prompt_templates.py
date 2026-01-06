from flask import request, jsonify, Blueprint, current_app, send_from_directory
import logging

from wechat_report_agent.backend.db import get_db_conn, row_to_dict
from wechat_report_agent.backend.auth import require_token

# Blueprint to expose prompt_templates endpoints
prompt_templates_bp = Blueprint('prompt_templates', __name__)
prompt_templates_bp = prompt_templates_bp

logger = logging.getLogger('backend.routes.prompt_templates')


def handle_prompt_template_modify(tpl_id):
    """Handle PUT/DELETE for a prompt template. Called from the monolithic wrapper.

    This function intentionally reads from `flask.request` so it can be used
    directly from the Flask view in `prompt_qdrant_api.py` without registering
    an additional route here (avoids duplicate route registration during
    incremental migration).
    """
    if request.method == 'DELETE':
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('DELETE FROM prompt_template WHERE id=?', (tpl_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok', 'deleted_id': tpl_id})

    # PUT -> update
    data = request.json or {}
    title = data.get('title') or data.get('topic')
    content = data.get('content') or data.get('template')
    conn = get_db_conn()
    c = conn.cursor()
    # build dynamic update
    sets = []
    vals = []
    if title is not None:
        sets.append('title=?')
        vals.append(title)
    if content is not None:
        sets.append('content=?')
        vals.append(content)
    if not sets:
        conn.close()
        return jsonify({'status': 'error', 'error': 'no_fields_provided'}), 400
    vals.append(tpl_id)

    try:
        c.execute("PRAGMA table_info(prompt_template)")
        cols = [r[1] for r in c.fetchall()]
    except Exception:
        cols = []

    if 'name' in cols and title is not None:
        sets_with_name = sets.copy()
        sets_with_name.insert(0, 'name=?')
        vals = [title] + vals
        c.execute(f"UPDATE prompt_template SET {', '.join(sets_with_name)} WHERE id=?", tuple(vals))
    else:
        c.execute(f"UPDATE prompt_template SET {', '.join(sets)} WHERE id=?", tuple(vals))

    conn.commit()
    c.execute('SELECT id, COALESCE(title, name) as title, content FROM prompt_template WHERE id=?', (tpl_id,))
    row = c.fetchone()
    conn.close()
    return jsonify(row_to_dict(row))
"""Handlers for prompt_template management migrated from the monolithic module.

These functions are plain callables (not routes) so the original module can
delegate to them while we gradually move logic out of `prompt_qdrant_api.py`.
"""
import os
import json
from werkzeug.utils import secure_filename
from flask import jsonify
from wechat_report_agent.backend.db import get_db_conn, row_to_dict


def handle_prompt_templates(req):
    # GET -> list
    if req.method == 'GET':
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT id, COALESCE(title, name) as title, content FROM prompt_template ORDER BY id")
        rows = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    # POST -> create
    data = req.json or {}
    title = data.get('title') or data.get('topic') or data.get('name') or 'untitled'
    content = data.get('content') or data.get('template') or ''
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(prompt_template)")
        cols = [r[1] for r in c.fetchall()]
    except Exception:
        cols = []
    if 'name' in cols:
        c.execute('INSERT INTO prompt_template (name, title, content) VALUES (?, ?, ?)', (title, title, content))
    else:
        c.execute('INSERT INTO prompt_template (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({'id': new_id, 'title': title, 'content': content}), 201


@prompt_templates_bp.route('/api/prompt_templates', methods=['GET', 'POST'])
def route_prompt_templates():
    return handle_prompt_templates(request)


@prompt_templates_bp.route('/api/prompt_templates/<int:tpl_id>', methods=['PUT', 'DELETE'])
@require_token
def route_prompt_template_modify(tpl_id):
    return handle_prompt_template_modify(tpl_id, request)


def handle_prompt_template_modify(tpl_id, req):
    if req.method == 'DELETE':
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('DELETE FROM prompt_template WHERE id=?', (tpl_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok', 'deleted_id': tpl_id})

    # PUT -> update
    data = req.json or {}
    title = data.get('title') or data.get('topic')
    content = data.get('content') or data.get('template')
    conn = get_db_conn()
    c = conn.cursor()
    sets = []
    vals = []
    if title is not None:
        sets.append('title=?')
        vals.append(title)
    if content is not None:
        sets.append('content=?')
        vals.append(content)
    if not sets:
        conn.close()
        return jsonify({'status': 'error', 'error': 'no_fields_provided'}), 400
    vals.append(tpl_id)
    try:
        c.execute("PRAGMA table_info(prompt_template)")
        cols = [r[1] for r in c.fetchall()]
    except Exception:
        cols = []
    if 'name' in cols and title is not None:
        sets_with_name = sets.copy()
        sets_with_name.insert(0, 'name=?')
        vals = [title] + vals
        c.execute(f"UPDATE prompt_template SET {', '.join(sets_with_name)} WHERE id= ?", tuple(vals))
    else:
        c.execute(f"UPDATE prompt_template SET {', '.join(sets)} WHERE id=?", tuple(vals))
    conn.commit()
    c.execute('SELECT id, COALESCE(title, name) as title, content FROM prompt_template WHERE id=?', (tpl_id,))
    row = c.fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


# Compatibility endpoints for older frontend
# - POST /api/upload-template : multipart/form-data, file field -> save file and create prompt_template row
# - GET  /api/list-templates  : list uploaded templates (rows in prompt_template where content points to uploaded_templates)
# - POST /api/delete-template : JSON {id: <id>} -> delete file and DB row
# - GET  /api/download-template/<id> : serve file by id


@prompt_templates_bp.route('/api/upload-template', methods=['POST'])
def upload_template():
    # Accept multipart/form-data; field name usually 'file' or first file
    if 'file' in request.files:
        f = request.files['file']
    else:
        # take first file available
        files = list(request.files.values())
        f = files[0] if files else None

    if f is None or f.filename == '':
        return jsonify({'code': 400, 'error': 'no_file'}), 400

    filename = secure_filename(f.filename)
    upload_dir = os.path.join(current_app.instance_path, 'uploaded_templates')
    os.makedirs(upload_dir, exist_ok=True)
    # make filename unique
    import time
    uniq = str(int(time.time() * 1000))
    saved_name = f"{uniq}_{filename}"
    dest_path = os.path.join(upload_dir, saved_name)
    f.save(dest_path)

    # store a relative path in DB so listing/download can find it
    rel_path = os.path.join('uploaded_templates', saved_name).replace('\\', '/')
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(prompt_template)")
        cols = [r[1] for r in c.fetchall()]
    except Exception:
        cols = []
    title = filename
    if 'name' in cols:
        c.execute('INSERT INTO prompt_template (name, title, content) VALUES (?, ?, ?)', (title, title, rel_path))
    else:
        c.execute('INSERT INTO prompt_template (title, content) VALUES (?, ?)', (title, rel_path))
    conn.commit()
    new_id = c.lastrowid
    conn.close()

    return jsonify({'code': 200, 'data': {'id': new_id, 'path': rel_path, 'name': title}})


@prompt_templates_bp.route('/api/list-templates', methods=['GET'])
def list_templates():
    conn = get_db_conn()
    c = conn.cursor()
    # list rows where content points to uploaded_templates/ (relative path)
    try:
        c.execute("SELECT id, COALESCE(title, name) as title, content FROM prompt_template WHERE content LIKE 'uploaded_templates/%' ORDER BY id")
        rows = [row_to_dict(r) for r in c.fetchall()]
    except Exception:
        rows = []
    conn.close()
    return jsonify({'code': 200, 'data': rows})


@prompt_templates_bp.route('/api/delete-template', methods=['POST'])
def delete_template():
    data = request.get_json(force=True, silent=True) or {}
    tpl_id = data.get('id') or data.get('tpl_id') or data.get('template_id')
    if tpl_id is None:
        return jsonify({'code': 400, 'error': 'missing id'}), 400

    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT content FROM prompt_template WHERE id=?', (tpl_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'code': 404, 'error': 'not_found'}), 404
    content = row[0] or ''
    # try to remove file if it's in uploaded_templates
    if content and 'uploaded_templates' in content:
        file_path = os.path.join(current_app.instance_path, content)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    c.execute('DELETE FROM prompt_template WHERE id=?', (tpl_id,))
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'deleted_id': tpl_id})


@prompt_templates_bp.route('/api/download-template/<int:tpl_id>', methods=['GET'])
def download_template(tpl_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT content, COALESCE(title, name) as title FROM prompt_template WHERE id=?', (tpl_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'code': 404, 'error': 'not_found'}), 404
    content, title = row[0], row[1]
    if not content:
        return jsonify({'code': 404, 'error': 'no_content'}), 404
    # if content points to uploaded_templates, serve the file
    if content.startswith('uploaded_templates/') or '/uploaded_templates/' in content:
        upload_dir = os.path.join(current_app.instance_path, 'uploaded_templates')
        filename = os.path.basename(content)
        file_path = os.path.join(upload_dir, filename)
        if os.path.exists(file_path):
            return send_from_directory(upload_dir, filename, as_attachment=True)
        else:
            return jsonify({'code': 404, 'error': 'file_missing'}), 404

    # otherwise return the content as plain text download
    from flask import Response
    resp = Response(content, mimetype='text/plain')
    resp.headers['Content-Disposition'] = f'attachment; filename="{secure_filename(title or "template.txt")}"'
    return resp
