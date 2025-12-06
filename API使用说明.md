# AI周报生成系统 API 使用说明

## 新的工作流程

### 1. 提示词管理（前端操作）

#### 创建默认提示词模板
```http
POST /api/create-default-prompt
```
创建基于第12期标准的默认提示词模板

#### 获取所有提示词模板
```http
GET /api/prompt_templates
```

#### 创建新提示词模板
```http
POST /api/prompt_templates
Content-Type: application/json

{
  "title": "自定义提示词名称",
  "content": "提示词内容..."
}
```

#### 修改提示词模板
```http
PUT /api/prompt_templates/{id}
Content-Type: application/json

{
  "title": "修改后的标题",
  "content": "修改后的内容..."
}
```

#### 删除提示词模板
```http
DELETE /api/prompt_templates/{id}
```

### 2. 报告生成（使用数据库提示词）

#### 方式1：使用提示词模板ID
```http
POST /api/generate-report
Content-Type: application/json

{
  "prompt_template_id": 1,  // 使用数据库中的提示词
  "model": "DeepSeek-R1",
  "material": [1, 2, 3],    // 文章ID列表
  "download": false         // 是否下载DOCX文件
}
```

#### 方式2：直接传入材料文本
```http
POST /api/generate-report
Content-Type: application/json

{
  "prompt_template_id": 1,
  "model": "DeepSeek-R1", 
  "combined_material": "原始新闻材料文本...",
  "download": false
}
```

#### 方式3：临时提示词（兼容旧版）
```http
POST /api/generate-report
Content-Type: application/json

{
  "prompt": "临时提示词内容...",
  "model": "DeepSeek-R1",
  "combined_material": "原始新闻材料文本...",
  "download": false
}
```

### 3. 响应格式

报告生成API返回：
```json
{
  "status": "ok",
  "ai_content": {
    "core_news": ["标题1", "标题2"],
    "技术前沿": ["条目1", "条目2"],
    "产业动态": ["条目1", "条目2"],
    "政策法规": ["条目1"],
    "应用实例": ["条目1", "条目2"]
  },
  "ai_content_validated": {
    // 每个条目的验证信息，包含来源匹配和相似度
  },
  "ai_counts": {
    "core_news": 2,
    "技术前沿": 2,
    // 各栏目条目数量
  },
  "quality_report": {
    "overall_score": 85,
    "section_scores": {},
    "issues": [],
    "recommendations": []
  }
}
```

## 前端集成指南

### 1. 提示词管理界面
- 提供提示词模板的CRUD功能
- 支持从默认模板开始创建
- 提供预览功能查看提示词效果

### 2. 报告生成界面  
- 下拉选择提示词模板
- 上传或输入材料文本
- 选择AI模型
- 显示生成进度和结果

### 3. 推荐使用流程
1. 首次使用：调用 `/api/create-default-prompt` 创建默认模板
2. 用户可以基于默认模板修改创建自己的提示词
3. 生成报告时选择合适的提示词模板
4. 系统自动生成符合第12期格式的报告并保存为Markdown文件

### 4. 优势
- ✅ 提示词与代码分离，便于管理和调整
- ✅ 支持多个提示词模板，适应不同需求
- ✅ 保持向后兼容，支持临时提示词
- ✅ 自动质量评估和格式验证
- ✅ 智能材料验证和来源追溯