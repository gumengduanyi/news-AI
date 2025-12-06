#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的提示词数据库集成功能
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5001"
TOKEN = "1"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_create_default_prompt():
    """测试创建默认提示词"""
    print("1. 创建默认提示词模板...")
    response = requests.post(f"{BASE_URL}/api/create-default-prompt", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    return response.json()

def test_get_prompt_templates():
    """测试获取提示词模板列表"""
    print("\n2. 获取提示词模板列表...")
    response = requests.get(f"{BASE_URL}/api/prompt_templates", headers=headers)
    print(f"状态码: {response.status_code}")
    templates = response.json()
    print(f"模板数量: {len(templates)}")
    for template in templates:
        print(f"  ID: {template['id']}, 标题: {template['title']}")
    return templates

def test_generate_report_with_template(template_id):
    """测试使用模板ID生成报告"""
    print(f"\n3. 使用模板ID {template_id} 生成报告...")
    
    # 测试材料
    test_material = """
    阿里云发布全球首个全模态AI模型Qwen3-Omni并开源。该模型实现了原生端到端的全模态处理能力，能够处理文本、图像、音频和视频等多种数据类型。
    
    智元机器人开源全球首个通用具身智能模型GO-1。这是全球首个采用ViLLA架构的具身智能模型，能让机器人更好理解人类意图并精确执行动作。
    
    ChatGPT曝出"ShadowLeak"漏洞，OpenAI已修复。Radware安全研究人员披露了这一安全问题，该漏洞可能使攻击者窃取Gmail账户敏感数据。
    """
    
    payload = {
        "prompt_template_id": template_id,
        "model": "DeepSeek-R1",
        "combined_material": test_material,
        "download": False
    }
    
    response = requests.post(f"{BASE_URL}/api/generate-report", 
                           headers=headers, 
                           json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"生成状态: {result.get('status')}")
        
        if 'ai_content' in result:
            ai_content = result['ai_content']
            print("\n生成的内容结构:")
            for section, items in ai_content.items():
                print(f"  {section}: {len(items)}条")
                for i, item in enumerate(items[:2]):  # 只显示前2条
                    print(f"    {i+1}. {item}")
        
        if 'quality_report' in result:
            quality = result['quality_report']
            print(f"\n质量评分: {quality.get('overall_score', 0)}/100")
            if quality.get('issues'):
                print("发现问题:")
                for issue in quality['issues']:
                    print(f"  - {issue}")
    else:
        print(f"错误: {response.text}")

def main():
    print("开始测试新的提示词数据库集成功能\n")
    
    try:
        # 1. 创建默认提示词
        default_result = test_create_default_prompt()
        
        # 2. 获取提示词列表
        templates = test_get_prompt_templates()
        
        # 3. 使用第一个模板生成报告
        if templates and len(templates) > 0:
            template_id = templates[0]['id']
            test_generate_report_with_template(template_id)
        else:
            print("没有找到可用的提示词模板")
            
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到后端服务器，请确保服务正在运行在 http://127.0.0.1:5001")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()