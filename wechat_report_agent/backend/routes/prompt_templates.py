"""Handlers for prompt_template management migrated from the monolithic module.

These functions are plain callables (not routes) so the original module can
delegate to them while we gradually move logic out of `prompt_qdrant_api.py`.
"""
import os
import json
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
