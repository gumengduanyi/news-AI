# ai_api.py
"""
AI模型统一调用接口示例：支持豆包、DeepSeek
注：使用环境变量配置 API 地址与 KEY
DOUBAO_API_URL, DOUBAO_API_KEY1
DEEPSEEK_API_URL, DEEPSEEK_API_KEY
"""

import os
import requests
import json

# 获取AI接口超时时间，优先环境变量，否则默认120秒
def get_ai_timeout():
    try:
        return int(os.environ.get('AI_API_TIMEOUT', '120'))
    except Exception:
        return 120

# 豆包API示例（假设为POST，需替换为实际API地址和参数）
def call_doubao(prompt, apikey=None):
    url = os.environ.get('DOUBAO_API_URL', 'https://api.doubao.com/v1/chat/completions')
    key = apikey or os.environ.get('DOUBAO_API_KEY')
    if not key:
        raise RuntimeError('缺少 DOUBAO_API_KEY')
    headers = {'Authorization': f'Bearer {key}'}
    data = {
        'model': 'doubao',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7
    }
    resp = requests.post(url, json=data, headers=headers, timeout=get_ai_timeout())
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']

# DeepSeek API示例（假设为POST，需替换为实际API地址和参数）
def call_deepseek(prompt, apikey=None):
    url = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    key = apikey or os.environ.get('DEEPSEEK_API_KEY')
    print("[DEBUG] DEEPSEEK_API_KEY:", os.environ.get("DEEPSEEK_API_KEY"))  # Debug line
    if not key:
        raise RuntimeError('缺少 DEEPSEEK_API_KEY')
    headers = {'Authorization': f'Bearer {key}'}
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=get_ai_timeout())
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] 请求错误: {req_err}")
        return "AI接口调用失败，请检查网络或API配置。"
    except Exception as e:
        print(f"[ERROR] 未知错误: {e}")
        return "AI接口调用发生未知错误。"

# 智谱AI（GLM/ChatGLM）API调用
def call_zhipuai(prompt, apikey=None):
    url = os.environ.get('ZHIPUAI_API_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
    key = apikey or os.environ.get('ZHIPUAI_API_KEY')
    if not key:
        raise RuntimeError('缺少 ZHIPUAI_API_KEY')
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'glm-4',  # 可根据实际模型名调整，如glm-3-turbo、chatglm_turbo等
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7
    }
    resp = requests.post(url, json=data, headers=headers, timeout=get_ai_timeout())
    resp.raise_for_status()
    # 智谱AI返回格式：{"choices": [{"content": "..."}]}
    result = resp.json()
    if 'choices' in result and result['choices']:
        # glm-4返回content字段
        return result['choices'][0].get('content', '')
    elif 'data' in result and result['data'] and 'choices' in result['data'] and result['data']['choices']:
        # 兼容旧版接口
        return result['data']['choices'][0].get('content', '')
    else:
        raise RuntimeError(f'智谱AI返回内容异常: {result}')

# 统一AI调用入口
def call_ai(model, prompt, apikey=None):
    if model == '豆包':
        response = call_doubao(prompt, apikey)
    elif model == 'DeepSeek-R1':
        response = call_deepseek(prompt, apikey)
    elif model in ('智谱AI', 'GLM', 'ChatGLM', 'GLM-4', 'chatglm_turbo'):
        response = call_zhipuai(prompt, apikey)
    else:
        raise ValueError(f'不支持的模型: {model}')

    # 尝试将返回值解析为 JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print(f"[ERROR] AI返回值无法解析为JSON: {response}")
        return {
            "core_news": [],
            "技术前沿": [],
            "产业动态": [],
            "政策法规": [],
            "应用实例": []
        }
