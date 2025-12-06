#!/usr/bin/env python3
"""简单的Flask服务器启动脚本"""

import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置环境变量
os.environ['DEBUG'] = '0'
os.environ['PORT'] = '5001'
os.environ['HOST'] = '127.0.0.1'

try:
    from prompt_qdrant_api import app, logger
    
    host = '127.0.0.1'
    port = 5001
    
    print(f"启动Flask服务器: http://{host}:{port}")
    logger.info(f'启动Flask应用在 {host}:{port}')
    
    # 简单启动，不使用reloader
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )
    
except Exception as e:
    print(f"启动失败: {e}")
    import traceback
    traceback.print_exc()