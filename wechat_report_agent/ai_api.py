"""AI adapter module.

Provides a `call_ai` entrypoint used by `wechat_report_agent.backend.ai_utils`.
"""
import logging
import json
import time
try:
    import requests
except Exception:
    requests = None

from wechat_report_agent.backend.ai_config import get_ai_adapter_settings

logger = logging.getLogger('ai_api')

def call_deepseek(model, prompt, mode=None, **kwargs):
    """Call a direct DeepSeek-compatible endpoint.

    This is a lightweight OpenAI-like client: POSTs a chat-completions style
    payload to the configured `DEEPSEEK_API_URL` with `Authorization: Bearer`.
    """
    from wechat_report_agent.backend.ai_config import get_deepseek_config
    cfg = get_deepseek_config()
    if not cfg.get('enabled'):
        return None
    if requests is None:
        logger.warning('requests not available, cannot call deepseek via HTTP')
        return None

    base = (cfg.get('url') or '').rstrip('/')
    # Build a reasonable chat completions endpoint. If the configured URL
    # points to a /v1 base, append the /chat/completions path; otherwise
    # append the common /v1/chat/completions path if not already present.
    if base.endswith('/v1') or base.endswith('/v1/'):
        url = base.rstrip('/') + '/chat/completions'
    elif base.endswith('/chat/completions'):
        url = base
    else:
        url = base + '/v1/chat/completions'
    headers = {'Content-Type': 'application/json'}
    if cfg.get('api_key'):
        ak = str(cfg.get('api_key') or '')
        if not ak.lower().startswith('bearer '):
            headers['Authorization'] = f'Bearer {ak}'
        else:
            headers['Authorization'] = ak

    # DeepSeek API expects the model name in the `mode` field (OpenAI-compatible clients
    # sometimes use `model`). Use `mode` for DeepSeek and include `messages` for chat.
    payload = {'messages': [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": str(prompt)}], 'stream': False}
    try:
        # DeepSeek HTTP API accepts `model` (model name) and a `mode` flag
        # (e.g., 'dialog' or 'think'). Prefer explicit `model`, but do not
        # set `mode` to the same model-name string — prefer the provided
        # `mode` argument or derive a sensible value from the model name.
        mv = None
        if model and isinstance(model, str) and model.strip():
            mv = str(model).strip()
            payload['model'] = mv
        elif mode and isinstance(mode, str) and mode.strip():
            # when caller provides only mode but not model, use mode as model
            mv = str(mode).strip()
            payload['model'] = mv

        # determine payload['mode'] separately: prefer explicit mode param,
        # otherwise derive from model name (chat -> dialog, reasoner -> think).
        if mode and isinstance(mode, str) and mode.strip():
            payload['mode'] = str(mode).strip()
        elif mv:
            lm = mv.lower()
            if 'chat' in lm:
                payload['mode'] = 'dialog'
            elif 'reason' in lm:
                payload['mode'] = 'think'
            else:
                payload['mode'] = mv
    except Exception:
        pass
    if kwargs:
        try:
            payload.update(kwargs)
        except Exception:
            pass

    # Add retry with exponential backoff for transient errors (429/5xx) and
    # robust logging of status/text for diagnostics.
    max_attempts = int(cfg.get('retries', 3))
    backoff_base = float(cfg.get('backoff_base', 0.5))
    for attempt in range(max_attempts):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=cfg.get('timeout', 20))
        except Exception as e:
            logger.exception('deepseek HTTP request exception (attempt %d/%d): %s', attempt + 1, max_attempts, e)
            if attempt < max_attempts - 1:
                time.sleep(backoff_base * (2 ** attempt))
                continue
            return None

        status = getattr(resp, 'status_code', None)
        text = None
        try:
            text = resp.text
        except Exception:
            text = ''

        # Log a short excerpt for debugging
        logger.info('deepseek response status=%s body_snippet=%s', status, (text or '')[:500])

        # Retry on rate limit / server errors
        if status in (429, 502, 503, 504) or (status and 500 <= status < 600):
            logger.warning('deepseek transient error status=%s (attempt %d/%d)', status, attempt + 1, max_attempts)
            if attempt < max_attempts - 1:
                time.sleep(backoff_base * (2 ** attempt))
                continue
            # final attempt: try to parse and return whatever we can
            try:
                return resp.json()
            except Exception:
                return text

        # Non-retryable path: try to parse JSON then fall back to text
        try:
            j = resp.json()
            # try common OpenAI-like response shapes
            if isinstance(j, dict):
                choices = j.get('choices')
                if choices and isinstance(choices, list):
                    c0 = choices[0]
                    if isinstance(c0, dict):
                        m = c0.get('message') or c0.get('text') or {}
                        if isinstance(m, dict):
                            return m.get('content') or j
                        return c0.get('text') or j
            return j
        except Exception:
            return text

def call_ai(model, prompt, mode=None, **kwargs):
    """Primary AI entrypoint used by ai_utils.call_ai.

    If DeepSeek is configured and model indicates DeepSeek, forward the
    request. Otherwise return None to let the caller fall back.
    """
    settings = get_ai_adapter_settings()
    m = str(model or '').lower()
    # Prefer DeepSeek when configured (use it for deepseek models or as primary
    # provider). If DeepSeek call fails, return None to let callers handle fallback.
    deep_cfg = settings.get('deepseek', {}) or {}
    if deep_cfg.get('enabled'):
        try:
            # Decide which DeepSeek model to call based on explicit model or mode.
            # If caller already specified a deepseek model name (e.g. 'deepseek-chat' or
            # 'deepseek-reasoner'), honor it. Otherwise map `mode` (dialog/think)
            # to the appropriate DeepSeek model name.
            target_model = None
            # Normalize incoming model string
            try:
                mm = str(model or '').strip()
            except Exception:
                mm = ''

            if mm and mm.lower().startswith('deepseek'):
                target_model = mm
            else:
                # If a default_model is configured in DeepSeek settings, prefer it
                dm = (deep_cfg.get('default_model') or '').strip()
                if dm:
                    target_model = dm
                else:
                    # determine mode preference: explicit `mode` param > instance default
                    _mode = None
                    if mode and isinstance(mode, str):
                        _mode = mode.strip().lower()
                    else:
                        _mode = (deep_cfg.get('default_mode') or '').strip().lower()

                    if _mode and _mode in ('think', 'reason', 'reasoner'):
                        target_model = 'deepseek-reasoner'
                    else:
                        # default to chat-oriented model
                        target_model = 'deepseek-chat'
            return call_deepseek(target_model, prompt, mode=mode or deep_cfg.get('default_mode'), **(kwargs or {}))
        except Exception:
            logger.exception('call_deepseek failed')
            return None

    # No other providers configured here; return None.
    return None
