"""Minimal debug Flask backend for local testing.

Provides three endpoints:
- GET  /api/validate-env
- POST /api/test-models
- GET/POST /api/generate-report-debug

This file intentionally keeps minimal dependencies and falls back to mocks
if internal modules are unavailable.
"""
import os
import json
import datetime
import tempfile
from flask import Flask, request, jsonify, send_file
import logging

import sys

# Replace file with a single, minimal implementation to remove legacy code.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
PARENT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

try:
    from wechat_report_agent.ai_api import call_ai
except Exception as e:
    # will use a local fallback if ai_api not available
    call_ai = None
    # defer logging setup until logger exists
    _import_callai_err = str(e)

try:
    from wechat_report_agent.src.render_word_report import generate_ai_report
except Exception as e:
    generate_ai_report = None
    _import_generate_err = str(e)

app = Flask(__name__)

# Setup structured logging for this module
logger = logging.getLogger('prompt_qdrant_api')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Emit import warnings if imports failed
if ' _import_callai_err' in globals():
    logger.warning('cannot import call_ai: %s', globals().get('_import_callai_err'))
if ' _import_generate_err' in globals():
    logger.warning('cannot import generate_ai_report: %s', globals().get('_import_generate_err'))


# Local fallback for call_ai when the real provider is not installed/available.
def local_call_ai_fallback(model, prompt):
    """Simple deterministic fallback that attempts to extract bullet points or
    create small simulated responses so downstream code can be tested offline.
    """
    logger.info('local_call_ai_fallback invoked for model=%s', model)
    # If prompt contains a JSON schema request, return a minimal JSON string
    if '请严格返回JSON' in (prompt or '') or '严格转换为可解析的JSON' in (prompt or ''):
        # return empty schema JSON
        schema = {
            "core_news": [],
            "技术前沿": [],
            "产业动态": [],
            "政策法规": [],
            "应用实例": []
        }
        return json.dumps(schema, ensure_ascii=False)

    # try to pull lines that look like bullet points
    lines = []
    for ln in (prompt or '').splitlines():
        s = ln.strip()
        if not s:
            continue
        if s[0].isdigit() or s.startswith('-') or s.startswith('*'):
            lines.append(s.lstrip('-*0123456789. ').strip())
        elif len(s) < 120:
            lines.append(s)
    if lines:
        return '\n'.join(lines[:8])

    # default short message
    return '这是本地模拟的模型响应。'

# If call_ai wasn't imported, point it to the fallback so code doesn't need branching
if call_ai is None:
    call_ai = local_call_ai_fallback


# --- Authentication decorator -------------------------------------------------
from functools import wraps
def require_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        expected = os.environ.get('REPORT_API_TOKEN')
        if not expected:
            # Enforce token presence
            return jsonify({'status':'error','error':'server_misconfigured_missing_token'}), 500
        # check Authorization header
        auth = request.headers.get('Authorization', '')
        token = None
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1].strip()
        # fallback to query param
        if not token:
            token = request.args.get('token')
        if token != expected:
            return jsonify({'status':'error','error':'invalid_or_missing_token'}), 401
        return func(*args, **kwargs)
    return wrapper

# --- Simple docx generator (module-level so tests can import) -----------------
def simple_generate_docx(content_dict, out_path):
    try:
        from docx import Document
    except Exception as e:
        logger.debug('python-docx not available: %s', e)
        raise
    doc = Document()
    doc.add_heading('AI 生成的报告（简易版）', level=1)
    for k, items in content_dict.items():
        doc.add_heading(k, level=2)
        if not items:
            doc.add_paragraph('(无内容)')
        else:
            for it in items:
                doc.add_paragraph(str(it), style=None)
    doc.save(out_path)


def ensure_structured_ai_response(model, ai_output):
    """Ensure ai_output becomes a dict with expected five keys, values are lists.

    Steps:
    - If ai_output is dict: fill missing keys with [] and return.
    - If ai_output is str: try json.loads; if fails, try to extract JSON substring.
    - If still fails and call_ai is available, ask model to convert the text to strict JSON.
    - If all fails, return empty schema.
    """
    expected_keys = ["core_news", "技术前沿", "产业动态", "政策法规", "应用实例"]

    # Helper to normalize dict
    def _normalize(d):
        out = {}
        for k in expected_keys:
            v = d.get(k, []) if isinstance(d, dict) else []
            if v is None:
                v = []
            # ensure list
            if not isinstance(v, list):
                v = [v]
            out[k] = v
        return out

    logger.info('ensure_structured_ai_response called for model=%s, ai_output_type=%s', model, type(ai_output).__name__)
    if isinstance(ai_output, dict):
        logger.info('ai_output is already dict; normalizing and returning')
        return _normalize(ai_output)

    text = '' if ai_output is None else (ai_output if isinstance(ai_output, str) else json.dumps(ai_output, ensure_ascii=False))

    # try direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            logger.info('direct json.loads succeeded')
            return _normalize(parsed)
        else:
            logger.debug('json.loads returned non-dict: %s', type(parsed).__name__)
    except Exception as e:
        logger.debug('direct json.loads failed: %s', e)

    # try extract first JSON object substring
    try:
        import re
        m = re.search(r"(\{[\s\S]*\})", text)
        if m:
            cand = m.group(1)
            logger.debug('found JSON substring candidate, attempting parse')
            try:
                parsed = json.loads(cand)
                if isinstance(parsed, dict):
                    logger.info('parsed JSON substring successfully')
                    return _normalize(parsed)
                else:
                    logger.debug('parsed substring is not dict')
            except Exception as e:
                logger.debug('parsing JSON substring failed: %s', e)
        else:
            logger.debug('no JSON substring found in text')
    except Exception as e:
        logger.debug('substring extraction failed: %s', e)

    # As last resort, ask model to convert to strict JSON
    if call_ai:
        conversion_prompt = (
            "请把下面的文本严格转换为可解析的JSON，返回一个包含五个键的字典：\n"
            "{\"core_news\": [], \"技术前沿\": [], \"产业动态\": [], \"政策法规\": [], \"应用实例\": []}\n"
            "每个键对应一个数组，数组内每个元素为字符串。不要添加其他文字，只返回JSON。\n\n"
            f"输入文本：\n{text}\n"
        )
        logger.info('attempting conversion via call_ai to coerce output to strict JSON')
        try:
            conv = call_ai(model, conversion_prompt)
            logger.debug('call_ai conversion returned type=%s', type(conv).__name__)
            if isinstance(conv, dict):
                logger.info('conversion produced dict; normalizing and returning')
                return _normalize(conv)
            if isinstance(conv, str):
                try:
                    parsed = json.loads(conv)
                    if isinstance(parsed, dict):
                        logger.info('conversion string parsed to dict successfully')
                        return _normalize(parsed)
                    else:
                        logger.debug('conversion string parsed but not dict')
                except Exception as e:
                    logger.debug('json.loads on conversion result failed: %s', e)
        except Exception as e:
            logger.error('conversion call_ai failed: %s', e)

    logger.warning('ensure_structured_ai_response falling back to empty schema')
    return {k: [] for k in expected_keys}


@app.route('/api/validate-env', methods=['GET'])
def validate_env():
    required_keys = ['DEEPSEEK_API_KEY', 'DOUBAO_API_KEY', 'ZHIPUAI_API_KEY']
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        return jsonify({'status': 'error', 'missing_keys': missing}), 400
    return jsonify({'status': 'success'})


@app.route('/api/test-models', methods=['POST'])
@require_token
def test_models():
    data = request.json or {}
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


@app.route('/api/generate-report-debug', methods=['GET', 'POST'])
@require_token
def generate_report_debug():
    data = request.json or {}
    prompt = data.get('prompt', '示例：请基于以下材料生成五类要点')
    model = 'DeepSeek-R1'

    schema = {
        "core_news": [],
        "技术前沿": [],
        "产业动态": [],
        "政策法规": [],
        "应用实例": []
    }

    # 调用 AI 并确保输出为结构化五键 JSON
    ai_raw = None
    if call_ai:
        try:
            ai_raw = call_ai(model, f"请严格返回JSON:\n{json.dumps(schema, ensure_ascii=False)}\n\n{prompt}")
        except Exception as e:
            logger.warning('call_ai failed: %s', e)
            ai_raw = None

    ai_content = ensure_structured_ai_response(model, ai_raw)

    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out = os.path.join(tempfile.gettempdir(), f'debug_report_{now}.docx')

    if generate_ai_report:
        try:
            generate_ai_report(ai_content, out)
        except Exception as e:
            logger.error('generate_ai_report failed: %s', e)
            return jsonify({'status': 'error', 'error': str(e)}), 500
    else:
        try:
            simple_generate_docx(ai_content, out)
        except Exception as e:
            logger.warning('simple_generate_docx failed: %s', e)
            return jsonify({'status': 'ok', 'ai_content': ai_content})

    return send_file(out, as_attachment=True, download_name=os.path.basename(out))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
