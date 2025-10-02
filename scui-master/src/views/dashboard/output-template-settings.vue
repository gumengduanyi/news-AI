<template>
  <div class="output-template-root">
    <div class="output-template-main-layout">
      <el-card class="output-template-left-card" shadow="hover">
        <div class="output-template-section-title">输出模板设置</div>
        <el-form :model="form" ref="formRef" label-width="80px" class="output-template-form-block">
          <el-form-item label="模板名称">
            <el-input v-model="form.name" placeholder="请输入模板名称" />
          </el-form-item>
          <el-form-item label="上传模板">
            <el-upload
              class="upload-demo"
              drag
              :show-file-list="false"
              :http-request="customUpload"
              :on-change="handleFileChange"
              ref="uploadRef"
            >
              <i class="el-icon-upload"></i>
              <div class="el-upload__text">将模板拖到此处，或 <em>点击上传</em></div>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSave">保存模板</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="output-template-right-card" shadow="hover">
        <div class="output-template-list-title">模板列表</div>
        <el-table :data="templateList" style="width:100%" row-key="id" border>
          <el-table-column prop="name" label="模板名称" min-width="160" />
          <el-table-column prop="type" label="类型" width="120" />
          <el-table-column prop="create_time" label="上传时间" min-width="160" />
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <el-button size="mini" @click.stop="downloadTemplate(scope.row)">下载</el-button>
              <el-popconfirm title="确定删除该模板？" @confirm="deleteTemplate(scope.row)">
                <template #reference>
                  <el-button size="mini" type="danger" style="margin-left:6px;">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.output-template-root {
  width: 100vw;
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0;
}
.output-template-main-layout {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  width: 100%;
  margin-top: 48px;
  margin-bottom: 40px;
  margin-left: 80px;
  gap: 40px;
}
.output-template-left-card {
  width: 600px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 32px 24px 32px;
  background: #fff;
}
.output-template-section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #3a4a5b;
}
.output-template-form-block {
  background: #fff;
  border-radius: 8px;
  padding: 18px 18px 8px 18px;
  margin-bottom: 0;
}
.output-template-right-card {
  flex: 1;
  min-width: 320px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 24px 24px 24px;
  background: #fff;
}
.output-template-list-title {
  color: #888;
  font-weight: bold;
  margin-bottom: 12px;
  font-size: 16px;
}
</style>

<script>
export default {
  name: 'OutputTemplateSettings',
  data() {
    return {
      activeTab: 'word',
      form: {
        name: ''
      },
      tabTitleMap: {
        word: 'Word 模板',
        html: 'HTML 模板',
        xiaohongshu: '小红书模板'
      },
      tabVars: {
        word: ['title', 'date', 'items', 'org', 'issue'],
        html: ['title', 'date', 'items', 'summary'],
        xiaohongshu: ['title', 'date', 'content', 'author']
      },
      uploadFile: null,
      templateList: [],
      selectedTemplate: null
    }
  },
  mounted() {
    this.loadTemplates();
  },
  methods: {
    onRowClick(row) {
      this.selectedTemplate = row;
    },
    getFileName(path) {
      if (!path) return '';
      return path.split('/').pop();
    },
    downloadTemplate(row) {
      if (!row || !row.id) return;
      window.open(`/api/download-template/${row.id}`);
    },
    onSave() {
      if (!this.form.name) {
        this.$message.warning('请填写模板名称');
        return;
      }
      if (!this.uploadFile) {
        this.$message.warning('请先选择文件');
        return;
      }
      this.$refs.uploadRef.submit();
    },
    onPreview() {
      this.$message.info('预览功能占位')
    },
    handleFileChange(file) {
      // 兼容 el-upload 传参格式，防止 raw 未定义
      this.uploadFile = (file && file.raw) || (file && file.file && file.file.raw) || file;
    },
    // 自定义上传方法
    customUpload(option) {
      const formData = new FormData();
      // 优先用 this.uploadFile，否则用 option.file.raw
      formData.append('file', this.uploadFile || (option.file && option.file.raw) || option.file);
      formData.append('name', this.form.name);
      formData.append('type', this.activeTab);
      fetch('/api/upload-template', {
        method: 'POST',
        body: formData
      })
        .then(async res => {
          if (!res.ok) throw new Error('上传失败');
          const data = await res.json();
          if (data.code === 200) {
            this.$message.success('上传成功');
            option.onSuccess && option.onSuccess(data);
            this.uploadFile = null;
            if (this.$refs.uploadRef) this.$refs.uploadRef.clearFiles();
            this.loadTemplates();
          } else {
            this.$message.error(data.msg || '上传失败');
            option.onError && option.onError(data);
          }
        })
        .catch(err => {
          this.$message.error('上传失败');
          option.onError && option.onError(err);
        });
    },
    loadTemplates() {
      fetch('/api/list-templates')
        .then(res => res.json())
        .then(data => {
          if (data.code === 200) {
            // 只显示 content 路径包含 uploaded_templates/ 的文件型模板
            this.templateList = (data.data || []).filter(t => t.path && t.path.indexOf('uploaded_templates/') !== -1);
            // 默认选中第一个模板
            this.selectedTemplate = this.templateList.length > 0 ? this.templateList[0] : null;
          }
        });
    },
    deleteTemplate(row) {
      fetch('/api/delete-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: row.id })
      })
        .then(res => res.json())
        .then(data => {
          if (data.code === 200) {
            this.$message.success('删除成功');
            this.loadTemplates();
          } else {
            this.$message.error(data.msg || '删除失败');
          }
        });
    }
  }
}
</script>

<!-- 移除旧布局样式，统一使用卡片布局样式（见上面的 <style scoped>） -->
