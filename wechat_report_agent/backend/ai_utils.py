import os
import json
import logging

logger = logging.getLogger('backend.ai')

_last_ai_debug = {'ai_raw': None, 'ai_content': None, 'model': None}


def normalize_ai_content_for_render(ai_content):
    expected_sections = ["技术前沿", "产业动态", "政策法规", "应用实例"]
    out = {}
    core = ai_content.get('core_news') if isinstance(ai_content, dict) else []
    core_out = []
    for it in (core or []):
        if isinstance(it, str):
            core_out.append(it)
        elif isinstance(it, dict):
            title = it.get('title') or it.get('name') or it.get('headline') or it.get('summary') or ''
            if title:
                core_out.append(title)
            else:
                core_out.append(json.dumps(it, ensure_ascii=False))
        else:
            core_out.append(str(it))
    out['core_news'] = core_out

    for sec in expected_sections:
        sec_items = ai_content.get(sec) if isinstance(ai_content, dict) else []
        norm = []
        for it in (sec_items or []):
            if isinstance(it, str):
                item = {'title': it, 'summary': it}
                item['标题'] = it
                item['摘要'] = it
                norm.append(item)
            elif isinstance(it, dict):
                title = it.get('title') or it.get('name') or it.get('headline') or ''
                summary = it.get('summary') or it.get('content') or it.get('description') or ''
                if not title and summary:
                    title = summary if len(summary) <= 120 else summary[:120]
                item = {'title': title, 'summary': summary}
                item['标题'] = title
                item['摘要'] = summary
                norm.append(item)
            else:
                norm.append({'title': str(it), 'summary': ''})
        out[sec] = norm

    try:
        import re
        cm_text = ai_content.get('combined_material') if isinstance(ai_content, dict) else ''
        cm_sents = []
        if cm_text and isinstance(cm_text, str):
            cm = cm_text
            for sep in ('。', '.', '！', '!', '?', '？', ';', '；', '\n'):
                cm = cm.replace(sep, '。')
            cm_sents = [s.strip() for s in cm.split('。') if s.strip()]

        for sec in expected_sections:
            for item in out.get(sec, []):
                s = item.get('summary') or ''
                if not s:
                    continue
                s = re.sub(r'(AI\s*生成：|AI Generated:|相关片段：)\s*', '', s, flags=re.I)
                try:
                    for sent in cm_sents:
                        if sent and sent in s:
                            s = s.replace(sent, '').strip()
                    parts = re.split(r'([。\.\!\?\？\n])', s)
                    new_parts = []
                    seen = set()
                    for i in range(0, len(parts), 2):
                        sent = parts[i].strip()
                        sep = parts[i+1] if i+1 < len(parts) else ''
                        full = (sent + sep).strip()
                        if not full:
                            continue
                        if full in seen:
                            continue
                        seen.add(full)
                        new_parts.append(full)
                    s = ' '.join(new_parts).strip()
                except Exception:
                    pass
                if not s:
                    s = '（该条暂无详细摘要 — 请检查 AI 输出或后端日志）'
                item['summary'] = s
    except Exception:
        logger.exception('post-process summaries failed')

    logger.info('normalize_ai_content_for_render: counts=%s', {k: len(v) for k, v in out.items()})
    return out


def sanitize_ai_content(ai_content):
    if not isinstance(ai_content, dict):
        return ai_content
    out = {}
    import re
    error_patterns = [r"call_deepseek_request_failed", r"HTTPSConnectionPool", r"SSLError", r"Traceback", r"error':", r"Exception"]
    DEEPSEEK_ERROR_RE = re.compile(r"\{\\'error\\':\s*'call_deepseek_request_failed'.*?\}", re.S)
    CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
    MULTI_EMPTY_RE = re.compile(r"\n{3,}")
    FULLWIDTH_DIGIT_RE = re.compile(r"[０-９]")

    def _fw2hw(m):
        return chr(ord(m.group(0)) - 0xFF10 + ord('0'))

    def _clean_str(s: str) -> str:
        try:
            if s is None:
                return ''
            t = str(s)
            t = DEEPSEEK_ERROR_RE.sub('', t)
            t = CONTROL_CHAR_RE.sub('', t)
            t = FULLWIDTH_DIGIT_RE.sub(lambda m: _fw2hw(m), t)
            t = MULTI_EMPTY_RE.sub('\n\n', t)
            lines = [ln.strip() for ln in t.splitlines()]
            lines = [ln for ln in lines if ln]
            t = '\n'.join(lines).strip()
            return t
        except Exception:
            return str(s or '')

    def _clean_obj(obj):
        if isinstance(obj, str):
            return _clean_str(obj)
        if isinstance(obj, dict):
            new = {}
            for kk, vv in obj.items():
                if kk and isinstance(kk, str) and kk.lower() in ('error', 'details', 'traceback', 'exception'):
                    continue
                new_v = _clean_obj(vv)
                if new_v == '' or new_v == [] or new_v == {}:
                    continue
                new[kk] = new_v
            return new
        if isinstance(obj, list):
            res = []
            for e in obj:
                ce = _clean_obj(e)
                if ce == '' or ce == [] or ce == {}:
                    continue
                res.append(ce)
            return res
        try:
            return _clean_str(str(obj))
        except Exception:
            return str(obj)

    for k, items in ai_content.items():
        new_items = []
        if not isinstance(items, list):
            items = [items]
        for it in items:
            try:
                if isinstance(it, dict):
                    keys_lower = {str(x).lower() for x in it.keys()}
                    if keys_lower & {'error', 'details', 'traceback', 'exception'}:
                        continue
                    cleaned = _clean_obj(it)
                    if cleaned:
                        new_items.append(cleaned)
                    continue

                s = _clean_str(it)
                if not s:
                    continue
                skip = False
                for p in error_patterns:
                    if re.search(p, s, flags=re.I):
                        skip = True
                        break
                if skip:
                    continue
                if re.match(r'^[\(\[【].{0,80}[\)\]】]$', s):
                    continue
                new_items.append(s)
            except Exception:
                continue
        out[k] = new_items
    return out


def ensure_structured_ai_response(model, ai_output):
    expected_keys = ["core_news", "技术前沿", "产业动态", "政策法规", "应用实例"]

    def _normalize(d):
        out = {}
        for k in expected_keys:
            v = d.get(k, []) if isinstance(d, dict) else []
            if v is None:
                v = []
            if not isinstance(v, list):
                v = [v]
            out[k] = v
        return out

    logger.info('ensure_structured_ai_response called for model=%s, ai_output_type=%s', model, type(ai_output).__name__)
    import re
    def _mask_snippet(s, length=1000):
        try:
            t = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
        except Exception:
            t = str(s)
        snippet = t[:length]
        return re.sub(r"\b[A-Za-z0-9]{20,}\b", '<REDACTED>', snippet)

    if isinstance(ai_output, dict):
        logger.info('ai_output is already dict; normalizing and returning')
        return _normalize(ai_output)

    text = '' if ai_output is None else (ai_output if isinstance(ai_output, str) else json.dumps(ai_output, ensure_ascii=False))

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            logger.info('direct json.loads succeeded')
            return _normalize(parsed)
    except Exception as e:
        logger.debug('direct json.loads failed: %s', e)

    try:
        import re
        m = re.search(r"(\{[\s\S]*\})", text)
        if m:
            cand = m.group(1)
            try:
                parsed = json.loads(cand)
                if isinstance(parsed, dict):
                    logger.info('parsed JSON substring successfully')
                    return _normalize(parsed)
            except Exception:
                pass
    except Exception:
        pass

    # 最后尝试调用模型强制转换（如可用）
    # 详细转换逻辑在主文件中可能会使用 call_ai；这里保留较轻的回退
    logger.warning('ensure_structured_ai_response 退化为空的 schema')
    return {k: [] for k in expected_keys}
