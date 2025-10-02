"""
AI模型统一调用接口：支持豆包、DeepSeek、智谱AI
注：使用环境变量配置 API 地址与 KEY
DOUBAO_API_URL, DOUBAO_API_KEY1
DEEPSEEK_API_URL, DEEPSEEK_API_KEY
ZHIPUAI_API_URL, ZHIPUAI_API_KEY
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
        return result['choices'][0]['content']
    return "AI接口调用失败，返回内容为空。"

# 统一调用接口
def call_ai(model, prompt, apikey=None):
    print(f"[DEBUG] 调用AI接口，模型: {model}, 提示词: {prompt}")
    try:
        if model == '豆包':
            response = call_doubao(prompt, apikey)
        elif model == 'DeepSeek-R1':
            response = call_deepseek(prompt, apikey)
        elif model in ('智谱AI', 'GLM', 'ChatGLM', 'GLM-4', 'chatglm_turbo'):
            response = call_zhipuai(prompt, apikey)
        else:
            raise ValueError(f'不支持的模型: {model}')

        print(f"[DEBUG] AI接口返回原始内容: {response}")

        # 尝试将返回值解析为 JSON
        try:
            parsed_response = json.loads(response)
            print(f"[DEBUG] AI接口解析后的JSON: {parsed_response}")
            return parsed_response
        except json.JSONDecodeError as json_error:
            print(f"[WARNING] JSON解析失败，返回原始内容: {response}, 错误: {json_error}")
            return response

    except Exception as e:
        print(f"[ERROR] AI接口调用失败: {e}")
        return {"error": "AI接口调用失败，未知错误", "details": str(e)}