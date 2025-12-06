"""
AI 模型统一调用接口：支持豆包、DeepSeek、智谱AI。
注意：使用环境变量配置 API 地址与 KEY，例如：
DOUBAO_API_URL, DOUBAO_API_KEY
DEEPSEEK_API_URL, DEEPSEEK_API_KEY
ZHIPUAI_API_URL, ZHIPUAI_API_KEY
"""

import os
import requests
import json
import logging

# 使用模块级 logger，避免直接在 stdout 打印敏感信息
logger = logging.getLogger('wechat_report_agent.ai_api')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# helper to mask long tokens/keys in snippets
import re
def _mask_snippet(s, length=500):
    try:
        t = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    except Exception:
        t = str(s)
    snippet = t[:length]
    return re.sub(r"\b[A-Za-z0-9\-_]{20,}\b", '<REDACTED>', snippet)

# 获取 AI 接口超时时间，优先读取环境变量；若无效则返回默认 120 秒
def get_ai_timeout():
    try:
        return int(os.environ.get('AI_API_TIMEOUT', '120'))
    except Exception:
        return 120

# 豆包 API 示例（假设为 POST，请根据实际 API 调整地址和参数）
def call_doubao(prompt, apikey=None):
    url = os.environ.get('DOUBAO_API_URL', 'https://api.doubao.com/v1/chat/completions')
    key = apikey or os.environ.get('DOUBAO_API_KEY')
    if not key:
        raise RuntimeError('缺少 DOUBAO_API_KEY，请在环境变量中设置 DOUBAO_API_KEY')
    headers = {'Authorization': f'Bearer {key}'}
    data = {
        'model': 'doubao',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=get_ai_timeout())
        resp.raise_for_status()
        j = resp.json()
        logger.debug('call_doubao response snippet: %s', _mask_snippet(j))
        return j['choices'][0]['message']['content']
    except requests.exceptions.RequestException as req_err:
        logger.error('call_doubao request error: %s', req_err)
        return {'error': 'call_doubao_request_failed', 'details': str(req_err)}
    except Exception as e:
        logger.exception('call_doubao unexpected error')
        return {'error': 'call_doubao_failed', 'details': str(e)}

# DeepSeek API 示例（假设为 POST，请根据实际 API 调整地址和参数）
def call_deepseek(prompt, apikey=None):
    url = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    key = apikey or os.environ.get('DEEPSEEK_API_KEY')
    # 不要打印明文 API key 到 stdout，使用 logger.debug 记录是否存在（不包含值）
    logger.debug('DEEPSEEK_API_KEY present=%s', bool(os.environ.get('DEEPSEEK_API_KEY')))
    if not key:
        raise RuntimeError('缺少 DEEPSEEK_API_KEY，请在环境变量中设置 DEEPSEEK_API_KEY')
    headers = {'Authorization': f'Bearer {key}'}
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=get_ai_timeout())
        resp.raise_for_status()
        j = resp.json()
        logger.debug('call_deepseek response snippet: %s', _mask_snippet(j))
        return j['choices'][0]['message']['content']
    except requests.exceptions.RequestException as req_err:
        logger.error('call_deepseek request error: %s', req_err)
        return {'error': 'call_deepseek_request_failed', 'details': str(req_err)}
    except Exception as e:
        logger.exception('call_deepseek unexpected error')
        return {'error': 'call_deepseek_failed', 'details': str(e)}

# 智谱 AI（GLM / ChatGLM）API 调用
def call_zhipuai(prompt, apikey=None):
    url = os.environ.get('ZHIPUAI_API_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
    key = apikey or os.environ.get('ZHIPUAI_API_KEY')
    if not key:
        raise RuntimeError('缺少 ZHIPUAI_API_KEY，请在环境变量中设置 ZHIPUAI_API_KEY')
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'glm-4',  # 可根据实际模型名调整，如glm-3-turbo、chatglm_turbo等
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=get_ai_timeout())
        resp.raise_for_status()
        result = resp.json()
        logger.debug('call_zhipuai response snippet: %s', _mask_snippet(result))
        if 'choices' in result and result['choices']:
            return result['choices'][0]['content']
        return {'error': 'call_zhipuai_empty_response', 'details': 'choices missing or empty'}
    except requests.exceptions.RequestException as req_err:
        logger.error('call_zhipuai request error: %s', req_err)
        return {'error': 'call_zhipuai_request_failed', 'details': str(req_err)}
    except Exception as e:
        logger.exception('call_zhipuai unexpected error')
        return {'error': 'call_zhipuai_failed', 'details': str(e)}

# 统一的 AI 调用入口，根据 model 字段分发到不同的提供者
def call_ai(model, prompt, apikey=None):
    logger.debug('调用 AI 接口，模型=%s', model)
    try:
        if model == '豆包':
            response = call_doubao(prompt, apikey)
        elif model == 'DeepSeek-R1':
            response = call_deepseek(prompt, apikey)
        elif model in ('智谱AI', 'GLM', 'ChatGLM', 'GLM-4', 'chatglm_turbo'):
            response = call_zhipuai(prompt, apikey)
        else:
            raise ValueError(f'不支持的模型: {model}')
        logger.debug('AI接口返回原始内容 type=%s', type(response).__name__)
        # 尝试将返回值解析为 JSON（如果服务返回字符串形式的 JSON）
        if isinstance(response, str):
            try:
                parsed_response = json.loads(response)
                logger.debug('AI 接口解析后的 JSON snippet: %s', _mask_snippet(parsed_response))
                return parsed_response
            except json.JSONDecodeError as json_error:
                logger.warning('JSON 解析失败，返回原始内容（masked snippet）: %s', _mask_snippet(response))
                return response
        else:
            # 如果返回已经是结构化数据（dict/list），直接返回
            logger.debug('AI接口返回结构化数据 snippet: %s', _mask_snippet(response))
            return response
    except RuntimeError as re:
        logger.error('AI call runtime error: %s', re)
        return {"error": "AI_runtime_error", "details": str(re)}
    except Exception as e:
        logger.exception('AI 接口调用失败')
        return {"error": "AI 接口调用失败，未知错误", "details": str(e)}


def call_deepseek_embed(inputs, apikey=None):
    """调用 DeepSeek 向量化（embeddings）接口，输入可以是单个字符串或字符串列表。

    优先使用环境变量 `DEEPSEEK_EMBED_URL`，其次尝试基于 `DEEPSEEK_API_URL` 推导的 embeddings 路径，最后使用默认地址。
    返回向量（list）。若缺少 key 或调用失败，会抛出 RuntimeError。
    """
    key = apikey or os.environ.get('DEEPSEEK_API_KEY')
    if not key:
        logger.error('call_deepseek_embed missing DEEPSEEK_API_KEY')
        return {'error': 'missing_deepseek_api_key', 'details': '缺少 DEEPSEEK_API_KEY，请在环境变量或 instance config 中设置 DEEPSEEK_API_KEY'}

    # 允许单个字符串的输入，并在返回时恢复为单个向量
    single = False
    if isinstance(inputs, str):
        inputs = [inputs]
        single = True

    url_candidates = [
        os.environ.get('DEEPSEEK_EMBED_URL'),
        os.environ.get('DEEPSEEK_API_URL') and os.environ.get('DEEPSEEK_API_URL').rstrip('/') + '/embeddings',
        'https://api.deepseek.com/v1/embeddings'
    ]
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    payload = {'input': inputs}

    last_err = None
    for url in url_candidates:
        if not url:
            continue
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=get_ai_timeout())
            resp.raise_for_status()
            j = resp.json()
            # Attempt to extract embeddings from common shapes
            if isinstance(j, dict) and 'data' in j and isinstance(j['data'], list):
                embs = []
                for item in j['data']:
                    if isinstance(item, dict) and 'embedding' in item:
                        embs.append(item['embedding'])
                    elif isinstance(item, dict) and 'vector' in item:
                        embs.append(item['vector'])
                if embs:
                    return embs[0] if single else embs
            # Some APIs return {'embeddings': [...]}
            if isinstance(j, dict) and 'embeddings' in j:
                return j['embeddings'][0] if single else j['embeddings']
            # If API returns plain list
            if isinstance(j, list) and all(isinstance(x, list) for x in j):
                return j[0] if single else j
            # otherwise, try to find embedding-like lists
            # fallback: search recursively for first list-of-numbers
            def find_vec(o):
                if isinstance(o, list) and o and isinstance(o[0], (int, float)):
                    return o
                if isinstance(o, dict):
                    for v in o.values():
                        res = find_vec(v)
                        if res is not None:
                            return res
                if isinstance(o, list):
                    for v in o:
                        res = find_vec(v)
                        if res is not None:
                            return res
                return None

            emb = find_vec(j)
            if emb is not None:
                return emb if single else [emb]

        except requests.exceptions.RequestException as req_err:
            last_err = str(req_err)
            logger.warning('call_deepseek_embed request exception for url=%s: %s', url, _mask_snippet(str(req_err)))
            continue
        except Exception as e:
            last_err = str(e)
            logger.exception('call_deepseek_embed unexpected exception for url=%s', url)
            continue

    logger.error('call_deepseek_embed all attempts failed, last_err=%s', _mask_snippet(last_err))
    return {'error': 'deepseek_embed_failed', 'details': str(last_err)}