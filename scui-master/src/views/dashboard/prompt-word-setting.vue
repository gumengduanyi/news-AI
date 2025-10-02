<template>
  <div class="prompt-word-root">
    <div class="prompt-word-main-layout">
      <el-card class="prompt-word-left-card" shadow="hover">
        <div class="prompt-word-list-title">模版列表</div>
        <el-input v-model="search" placeholder="搜索主题" clearable class="prompt-word-search" />
        <el-table :data="filteredList" class="prompt-word-table" size="small" border>
          <el-table-column prop="title" label="主题" width="100" />
          <el-table-column prop="content" label="模版正文" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="90">
            <template #default="scope">
              <el-button size="mini" @click="editTemplate(scope.row)">编辑</el-button>
              <el-button size="mini" type="danger" @click="deleteTemplate(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button type="primary" @click="addTemplate" class="prompt-word-add-btn">新建模版</el-button>
      </el-card>
      <el-card v-if="showForm" class="prompt-word-right-card" shadow="hover" header="提示词模版设置">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" class="prompt-word-form-block">
          <el-form-item label="主题" prop="topic">
            <el-input v-model="form.topic" placeholder="请输入主题" />
          </el-form-item>
          <el-form-item label="模版正文" prop="template">
            <el-input
              v-model="form.template"
              type="textarea"
              :rows="8"
              placeholder="请输入模版内容"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="save">保存</el-button>
            <el-button @click="reset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
    </div>
  </template>

  <style scoped>
.prompt-word-root {
  width: 100vw;
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0;
}
.prompt-word-main-layout {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  width: 100%;
  margin-top: 48px;
  margin-bottom: 40px;
  margin-left: 80px;
  gap: 40px;
}
.prompt-word-left-card {
  width: 380px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 24px 24px 24px;
  background: #fff;
  min-height: 600px;
}
.prompt-word-list-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #3a4a5b;
}
.prompt-word-search {
  margin-bottom: 16px;
  width: 90%;
}
.prompt-word-table {
  width: 90%;
  margin-bottom: 16px;
}
.prompt-word-add-btn {
  width: 90%;
}
.prompt-word-right-card {
  flex: 1;
  min-width: 320px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 32px 24px 32px;
  background: #fff;
  max-width: 700px;
}
.prompt-word-form-block {
  background: #fff;
  border-radius: 8px;
  padding: 18px 18px 8px 18px;
  margin-bottom: 0;
}
</style>

<script>
import axios from 'axios';
export default {
  name: "PromptWordSetting",
  data() {
    return {
      search: '',
      templateList: [],
      form: {
        id: null,
        topic: '',
        template: ''
      },
      rules: {
        topic: [{ required: true, message: '请输入主题', trigger: 'blur' }],
        template: [{ required: true, message: '请输入模版内容', trigger: 'blur' }]
      },
      showForm: false,
    }
  },
  computed: {
    filteredList() {
      if (!this.search) return this.templateList;
      return this.templateList.filter(t => t.topic.includes(this.search));
    }
  },
  created() {
    this.fetchTemplates();
  },
  methods: {
    fetchTemplates() {
      axios.get('/api/prompt_templates')
        .then(res => {
          // 判空和类型校验，避免 undefined/null 错误
          const data = Array.isArray(res.data) ? res.data : [];
          this.templateList = data
            .filter(t => t && t.id && t.title && typeof t.title === 'string' && t.title.trim() !== '')
            .filter(t => {
              // 只要 model 是输出模板类型就排除
              return !['word', 'html', 'xiaohongshu'].includes(t.model);
            })
            .map(t => ({
              ...t
            }));
        })
        .catch(err => {
          // 输出详细错误信息到控制台和页面
          console.error('获取模版列表失败:', err);
          this.$message.error(
            err?.response?.data?.msg || err?.response?.data?.error || '获取模版列表失败'
          );
          this.templateList = [];
        });
    },
    addTemplate() {
      this.reset();
      this.showForm = true;
    },
    editTemplate(row) {
      this.form = { ...row, topic: row.title, template: row.content };
      this.showForm = true;
    },
    deleteTemplate(row) {
      this.$confirm('确定删除该模版吗？', '提示', { type: 'warning' }).then(() => {
        axios.delete(`/api/prompt_templates/${row.id}`)
          .then(() => {
            this.$message.success('删除成功！');
            this.fetchTemplates();
            if (this.form.id === row.id) this.reset();
          })
          .catch(err => {
            if (err.response && err.response.status === 404) {
              this.$message.info('记录已删除，无需重复操作');
              this.fetchTemplates();
              if (this.form.id === row.id) this.reset();
            } else {
              this.$message.error(err.response?.data?.error || '删除失败');
            }
          });
      });
    },
    insertVar(v) {
      this.form.template += v;
    },
    save() {
      this.$refs.formRef.validate(valid => {
        if (!valid) return;
        const payload = {
          name: this.form.topic,
          content: this.form.template
        };
        if (this.form.id) {
          axios.put(`/api/prompt_templates/${this.form.id}`, payload)
            .then(() => {
              this.$message.success('修改成功！');
              this.fetchTemplates();
              this.reset();
            })
            .catch(err => {
              this.$message.error(err.response?.data?.error || '保存失败');
            });
        } else {
          axios.post('/api/prompt_templates', payload)
            .then(() => {
              this.$message.success('新增成功！');
              this.fetchTemplates();
              this.reset();
            })
            .catch(err => {
              this.$message.error(err.response?.data?.error || '新增失败');
            });
        }
      });
    },
    reset() {
      this.form = { id: null, topic: '', template: '' };
      if (this.$refs.formRef) this.$refs.formRef.resetFields();
      this.showForm = false;
    }
  }
};
</script>
