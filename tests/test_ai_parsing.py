import os
import sys
import json
import tempfile
from docx import Document
import pytest

# ensure repo root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wechat_report_agent import prompt_qdrant_api as api


def test_ensure_structured_with_dict():
    inp = {
        "core_news": ["a"],
        "技术前沿": "b",
    }
    out = api.ensure_structured_ai_response('m', inp)
    assert isinstance(out, dict)
    assert out['core_news'] == ['a']
    assert out['技术前沿'] == ['b']
    assert out['产业动态'] == []


def test_ensure_structured_with_json_string():
    s = json.dumps({"core_news": ["x"], "产业动态": ["y"]}, ensure_ascii=False)
    out = api.ensure_structured_ai_response('m', s)
    assert out['core_news'] == ['x']
    assert out['产业动态'] == ['y']


def test_simple_generate_docx_and_read():
    sample = {
        "core_news": ["新闻1"],
        "技术前沿": ["技术A"],
        "产业动态": [],
        "政策法规": ["政策X"],
        "应用实例": ["实例Y"]
    }
    fd, p = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    try:
        api.simple_generate_docx(sample, p)
        d = Document(p)
        texts = [para.text for para in d.paragraphs]
        # Ensure some key headings exist
        assert any('核心' in t or '核心' in t for t in texts) or any('AI 生成的报告' in t for t in texts)
    finally:
        try:
            os.remove(p)
        except Exception:
            pass


def test_require_token_decorator_enforces():
    # Ensure server errors if REPORT_API_TOKEN not set
    old = os.environ.pop('REPORT_API_TOKEN', None)
    try:
        # Use Flask test client
        app = api.app.test_client()
        rv = app.post('/api/generate-report-debug', json={'prompt':'x'})
        assert rv.status_code == 500
        data = rv.get_json()
        assert data['error'] == 'server_misconfigured_missing_token'
    finally:
        if old is not None:
            os.environ['REPORT_API_TOKEN'] = old
