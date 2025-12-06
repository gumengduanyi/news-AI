#!/usr/bin/env python3
"""测试JSON结构修复是否生效"""

import json

def test_normalize_function():
    """测试修复后的normalize函数"""
    # 模拟AI返回的嵌套结构
    ai_response = {
        "核心要闻": {
            "技术前沿": [
                "⚫ 阿里云发布全球首个全模态AI模型Qwen3-Omni并开源",
                "⚫ 智元机器人开源全球首个通用具身智能模型GO-1"
            ],
            "产业动态": [
                "⚫ Dyna Robotics获英伟达等1.2亿美元A轮融资",
                "⚫ 华为鸿蒙操作系统5全面进击AI全场景"
            ],
            "政策法规": [
                "⚫ H-1B签证政策变动引发AI人才流失担忧"
            ],
            "应用实例": [
                "⚫ 钉钉AI表格助理正式上线降低使用门槛"
            ]
        }
    }
    
    # 期望的平铺结构
    expected_keys = ["core_news", "技术前沿", "产业动态", "政策法规", "应用实例"]
    
    def _normalize(d):
        """复制修复后的normalize函数逻辑"""
        out = {}
        
        # 处理嵌套的 "核心要闻" 结构
        if isinstance(d, dict) and "核心要闻" in d:
            print('检测到嵌套的"核心要闻"结构，正在解包')
            core_content = d["核心要闻"]
            if isinstance(core_content, dict):
                # 将嵌套结构平铺
                for section in ["技术前沿", "产业动态", "政策法规", "应用实例"]:
                    if section in core_content:
                        d[section] = core_content[section]
                # 设置 core_news
                d["core_news"] = []
                # 如果有其他顶级键，也保留
                for k, v in d.items():
                    if k != "核心要闻":
                        d[k] = v
        
        for k in expected_keys:
            v = d.get(k, []) if isinstance(d, dict) else []
            if v is None:
                v = []
            # ensure list
            if not isinstance(v, list):
                v = [v]
            out[k] = v
        return out
    
    # 测试转换
    result = _normalize(ai_response)
    
    print("输入 (嵌套结构):")
    print(json.dumps(ai_response, ensure_ascii=False, indent=2))
    print("\n输出 (平铺结构):")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 验证结果
    print(f"\n验证结果:")
    for key in expected_keys:
        count = len(result.get(key, []))
        print(f"  {key}: {count} 条")
    
    total_items = sum(len(result.get(key, [])) for key in expected_keys if key != "core_news")
    print(f"\n总计内容项: {total_items}")
    
    return result

if __name__ == "__main__":
    test_normalize_function()