"""Generate-report related handlers migrated from prompt_qdrant_api.py

This module exposes callable functions that perform the core work so the
original routes can delegate to them. The goal is incremental migration.
"""
import os
import json
import logging
from flask import jsonify
from wechat_report_agent.backend.db import get_db_conn

logger = logging.getLogger('backend.routes.generate')


def _fetch_materials_by_ids(material_ids):
    if not material_ids:
        return []
    ids = [int(i) for i in material_ids]
    conn = get_db_conn()
    c = conn.cursor()
    q = f"SELECT id, title, content, date, summary, source, create_time FROM collected_article WHERE id IN ({','.join(['?']*len(ids))})"
    c.execute(q, tuple(ids))
    rows = []
    for r in c.fetchall():
        rows.append({'id': r['id'], 'title': r.get('title') or r.get('name', ''), 'content': r.get('content','')})
    conn.close()
    return rows


def handle_generate_report(req):
    data = req.json or {}
    prompt = data.get('prompt') or data.get('taskName') or '请基于以下材料生成五类要点'
    model = data.get('model') or 'DeepSeek-R1'
    material = data.get('material') or []

    # For migration simplicity, do a minimal behavior: gather combined material and
    # return a placeholder structured response. Full AI invocation remains in main module.
    combined = ''
    if material:
        parts = _fetch_materials_by_ids(material)
        combined = '\n\n'.join((p.get('title','') + '\n' + p.get('content','')) for p in parts)

    # Return a minimal schema to keep clients working during migration.
    schema = {
        'core_news': [],
        '技术前沿': [],
        '产业动态': [],
        '政策法规': [],
        '应用实例': []
    }
    # include some diagnostics
    return jsonify({'status': 'ok', 'model': model, 'prompt': prompt[:200], 'combined_material_snippet': combined[:1000], 'result': schema})


def handle_generate_report_debug(req):
    # For debug endpoint, reuse the same minimal logic but echo more of the request
    resp = handle_generate_report(req)
    return resp
