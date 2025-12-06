#!/usr/bin/env python3
"""简化的Flask测试服务器，用于调试API问题"""

import os
import sys
import json
import sqlite3
from flask import Flask, request, jsonify

# 添加路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

app = Flask(__name__)

# 加载配置
config_path = os.path.join(BASE_DIR, 'instance', 'config.json')
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
        for k, v in cfg.items():
            if isinstance(v, str) and not os.environ.get(k):
                os.environ[k] = v
    print(f"已加载配置: {config_path}")

# 数据库连接
def get_db_conn():
    db_path = os.path.join(BASE_DIR, 'prompt_templates.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    """将sqlite3.Row转换为字典"""
    return dict(row) if row else None

# 认证装饰器
def require_token(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
        
        expected_token = os.environ.get('REPORT_API_TOKEN', '1')
        if token != expected_token:
            return jsonify({'status': 'error', 'error': 'unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/prompt_templates', methods=['GET'])
@require_token
def api_prompt_templates():
    try:
        conn = get_db_conn()
        c = conn.cursor()
        # 返回时兼容旧的 'name' 列与新的 'title' 列，优先使用 title
        c.execute("SELECT id, COALESCE(title, name) as title, content FROM prompt_template ORDER BY id")
        rows = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)
    except Exception as e:
        print(f"API错误: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

if __name__ == '__main__':
    print("启动简化测试服务器...")
    app.run(host='127.0.0.1', port=5001, debug=True)