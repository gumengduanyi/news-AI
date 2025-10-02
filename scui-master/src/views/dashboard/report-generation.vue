
<template>
  <div class="report-gen-root">
    <div class="param-log-wrap">
      <el-card class="param-select-card" shadow="hover">
        <div class="param-title">参数选择</div>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" label-position="left" class="param-form">
          <el-form-item label="任务名称" prop="taskName">
            <el-input v-model="form.taskName" placeholder="请输入任务名称" />
          </el-form-item>
          <el-form-item label="模型" prop="model">
            <el-select v-model="form.model" style="width: 200px" filterable placeholder="请选择模型">
              <el-option v-for="item in modelList" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="提示词" prop="prompt">
            <el-select v-model="form.prompt" style="width: 200px" filterable placeholder="请选择提示词">
              <el-option v-for="item in promptList" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <div style="color:#909399;font-size:12px;margin-top:6px;">
              提示：提示词将作为 AI 生成正文的关键条件，请选择与本次任务匹配的提示词模版。
            </div>
          </el-form-item>
          <el-form-item label="素材范围" prop="material">
            <el-select v-model="form.material" style="width: 300px" filterable multiple collapse-tags placeholder="请选择素材范围">
              <el-option-group
                v-for="group in materialGroups"
                :key="group.taskName"
                :label="group.taskName + (group.keywords ? '（' + group.keywords + '）' : '')"
              >
                <el-option
                  v-for="item in group.articles"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-option-group>
            </el-select>
            <div v-if="materialGroups.length" style="margin-top:4px;">
              <span v-for="group in materialGroups" :key="group.taskName" style="margin-right:12px;">
                <el-link type="primary" @click="selectGroup(group)">全选{{group.taskName}}</el-link>
              </span>
            </div>
          </el-form-item>
          <!-- 输出模板选择已删除 -->
          <el-form-item>
            <el-checkbox v-model="form.withCitation">附带引用</el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.scanSensitive">敏感词扫描</el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-button class="gen-btn" type="primary" :loading="generating" @click="onGenerate">开始生成</el-button>
            <el-button @click="onClearLog" style="margin-left:12px;">清空日志</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      <el-card class="log-block-card" shadow="hover">
        <div class="log-title">生成日志</div>
        <div class="log-content">
          <pre>{{ log }}</pre>
        </div>
      </el-card>
    </div>
    <el-dialog v-model="previewVisible" title="报告预览" width="800px">
      <div v-html="previewHtml" style="min-height:300px;" />
    </el-dialog>
    <el-button type="danger" style="position:fixed;right:40px;bottom:40px;z-index:1001;" @click="onClearAllData">清空所有数据</el-button>
  </div>
</template>


<script>
export default {
  name: 'ReportGeneration',
  computed: {
    // 根据所选模型类型动态筛选模板类型
    filteredTemplateList() {
      // 这里假设模型和模板类型一一对应，如“豆包”->word，“DeepSeek-R1”->html，可根据实际业务调整
      const modelTypeMap = {
        '豆包': 'word',
        'DeepSeek-R1': 'html'
      };
      const type = modelTypeMap[this.form.model];
      if (!type) return this.templateList;
      return this.templateList.filter(t => t.type === type);
    }
  },
  data() {
    return {
      form: {
        taskName: '',
        model: '',
        prompt: '',
        material: [], // 多选
        template: '',
        withCitation: true,
        scanSensitive: true
      },
      rules: {
        taskName: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
        model: [{ required: true, message: '请选择模型', trigger: 'change' }],
        prompt: [{ required: true, message: '请选择提示词', trigger: 'change' }],
        material: [{ required: true, type: 'array', min: 1, message: '请选择素材范围', trigger: 'change' }],
  template: [], // 输出模板非必填，可为空
      },
      modelList: [
  { label: '豆包', value: '豆包' },
  { label: 'DeepSeek-R1', value: 'DeepSeek-R1' },
  { label: '智谱AI(GLM-4)', value: 'GLM-4' }
      ],
  promptList: [],
  materialList: [], // 动态采集结果
  materialGroups: [], // 按任务分组
      templateList: [], // 动态加载输出模板
      log: '',
      generating: false,
      reportReady: false,
      previewVisible: false,
      previewHtml: ''
    }
  },
  mounted() {
    this.fetchPromptList();
    this.fetchMaterialList();
    this.fetchTemplateList();
  },
  methods: {
    async fetchTemplateList() {
      // 动态获取输出模板，改为新版接口 /api/prompt_templates
      try {
        const res = await fetch('/api/prompt_templates', { credentials: 'include' });
        const data = await res.json();
        // 适配后端返回数组结构
        if (Array.isArray(data)) {
          this.templateList = data.map(item => ({
            label: item.title || item.name || '',
            value: item.id,
            type: item.model || '', // 后端字段为 model
            path: item.content || '' // 后端字段为 content
          }));
        } else {
          this.templateList = [];
        }
      } catch (e) {
        this.templateList = [];
        console.error('fetchTemplateList error:', e);
        this.log += '模板获取失败：' + (e && e.message ? e.message : JSON.stringify(e)) + '\n';
      }
    },

    async fetchMaterialList() {
      // 动态获取采集结果，分组
      try {
        const res = await fetch('/api/collect/result', { credentials: 'include' });
        const data = await res.json();
        if (data && Array.isArray(data.data)) {
          // 分组：task_name -> [{label, value, ...}]
          const groupMap = {};
          data.data.forEach(item => {
            const group = item.task_name || '未分组';
            if (!groupMap[group]) groupMap[group] = { taskName: group, keywords: item.keywords, articles: [] };
            groupMap[group].articles.push({
              label: (item.title || ''),
              value: item.id
            });
          });
          this.materialGroups = Object.values(groupMap);
          // 扁平化 materialList 供兼容旧用法
          this.materialList = data.data.map(item => ({
            label: (item.task_name ? item.task_name + ' - ' : '') + (item.title || ''),
            value: item.id
          }));
        } else {
          this.materialGroups = [];
          this.materialList = [];
        }
      } catch (e) {
        this.materialGroups = [];
        this.materialList = [];
        console.error('fetchMaterialList error:', e);
        this.log += '素材获取失败：' + (e && e.message ? e.message : JSON.stringify(e)) + '\n';
      }
    },
    selectGroup(group) {
      // 全选某个任务下所有文章
      this.form.material = Array.from(new Set([...(this.form.material || []), ...group.articles.map(a => a.value)]));
    },
    async fetchPromptList() {
      // 修正接口路径为 /api/prompt_templates，并增加健壮性处理
      try {
  const res = await fetch('/api/prompt_templates', { credentials: 'include' });
        let data = await res.json();
        // 兼容后端返回数组或对象
        if (Array.isArray(data)) {
          this.promptList = data.map(item => ({
            label: item.title || item.name || '',
            value: (item.id != null ? item.id : (item.title || item.name || '')),
            id: item.id,
            title: item.title || item.name || ''
          }));
        } else if (Array.isArray(data.data)) {
          this.promptList = data.data.map(item => ({
            label: item.title || item.name || '',
            value: (item.id != null ? item.id : (item.title || item.name || '')),
            id: item.id,
            title: item.title || item.name || ''
          }));
        } else {
          this.promptList = [];
        }
      } catch (e) {
        this.promptList = [
          { label: 'AI 新闻周报', value: 'AI 新闻周报' },
          { label: '行业快讯', value: '行业快讯' }
        ];
        console.error('fetchPromptList error:', e);
        this.log += '提示词获取失败：' + (e && e.message ? e.message : JSON.stringify(e)) + '\n';
      }
    },
    async onGenerate() {
      this.$refs.formRef.validate(async valid => {
        if (!valid) return;
        this.generating = true;
        this.log = '正在生成报告，请稍候...\n';
        this.reportReady = false;
        try {
          const selectedPrompt = this.promptList.find(p => p.value === this.form.prompt) || {};
          const promptTitle = selectedPrompt.title || selectedPrompt.label || this.form.prompt;
          const promptId = selectedPrompt.id != null ? selectedPrompt.id : undefined;
          const res = await fetch('/api/generate-report', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              taskName: this.form.taskName,
              model: this.form.model,
              // 为兼容后端旧字段，仍然发送 prompt（使用标题字符串）；同时补充 promptId/promptTitle
              prompt: promptTitle,
              promptId: promptId,
              promptTitle: promptTitle,
              material: this.form.material, // 传数组
              template: this.form.template
            })
          });
          if (!res.ok) throw new Error('生成失败');
          const blob = await res.blob();
          // 自动识别后端返回的文件名
          let filename = 'report.docx';
          const disposition = res.headers.get('content-disposition');
          if (disposition) {
            const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^;"]+)"?/i);
            if (match) {
              filename = decodeURIComponent(match[1] || match[2]);
            }
          }
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          a.remove();
          window.URL.revokeObjectURL(url);
          this.log += '报告已生成并下载！\n';
          this.generating = false;
          this.reportReady = true;
        } catch (e) {
          console.error('onGenerate error:', e);
          this.log += '生成失败：' + (e && e.message ? e.message : JSON.stringify(e)) + '\n';
          this.generating = false;
        }
      });
    },
    onClearLog() {
      this.log = '';
    },
    // 预览/下载功能已移除
    async onClearAllData() {
      this.$confirm('此操作将清空所有采集、模板等数据，且不可恢复，是否继续？', '警告', { type: 'warning' })
        .then(async () => {
          try {
            const res = await fetch('/api/clear-all-data', { method: 'POST', credentials: 'include' });
            const data = await res.json();
            if (data && data.code === 200) {
              this.$message.success('所有数据已清空！');
              this.fetchMaterialList && this.fetchMaterialList();
              this.fetchPromptList && this.fetchPromptList();
            } else {
              this.$message.error(data.msg || '清空失败');
            }
          } catch (e) {
            console.error('onClearAllData error:', e);
            this.$message.error('清空失败：' + (e && e.message ? e.message : JSON.stringify(e)));
          }
        });
    }
  }
}
</script>

<style scoped>


.report-gen-root {
  width: 100vw;
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.param-log-wrap {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  width: 100%;
  margin-top: 48px;
  margin-bottom: 40px;
  margin-left: 80px;
  gap: 40px;
}
.param-select-card {
  width: 400px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 32px 24px 32px;
  background: #fff;
}
.param-title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #3a4a5b;
}
.param-form {
  width: 100%;
}
.gen-btn {
  width: 100%;
  height: 40px;
  font-size: 16px;
  border-radius: 20px;
  background: #000;
  color: #fff;
  border: none;
}
.log-block-card {
  flex: 1;
  min-width: 600px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 32px 24px 32px;
  background: #fff;
}
.log-title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #3a4a5b;
}
.log-content {
  background: #f9fafb;
  border-radius: 12px;
  min-height: 120px;
  font-size: 16px;
  color: #222;
  padding: 18px 18px 8px 18px;
  box-shadow: 0 1px 4px 0 rgba(0,0,0,0.03);
}
.log-content pre {
  font-family: inherit;
  font-size: 16px;
  margin: 0;
  background: none;
  color: #222;
}

</style>
