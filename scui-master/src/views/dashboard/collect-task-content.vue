<template>
  <div class="collect-root">
    <div class="collect-main-layout">
      <el-card class="collect-left-card" shadow="hover">
  <el-tabs v-model="activeTab" class="collect-tab-bar">
          <el-tab-pane label="手动 URL" name="url" />
          <el-tab-pane label="手动录入" name="input" />
          <el-tab-pane label="关键词问答" name="qa" />
          <el-tab-pane label="采集结果" name="result" />
        </el-tabs>
        <div v-if="activeTab === 'url'" class="collect-section">
          <div class="collect-section-title">手动 URL 任务</div>
          <el-form label-width="80px" :model="urlForm" :rules="urlRules" ref="urlFormRef" class="collect-form-block">
            <el-form-item label="任务名称" prop="name">
              <el-input v-model="urlForm.name" placeholder="例如：AI 行业新闻抓取" />
            </el-form-item>
            <el-form-item label="关键词" prop="keywords">
              <el-input v-model="urlForm.keywords" placeholder="大模型; 开源; 融资" />
            </el-form-item>
            <el-form-item label="URL 列表" prop="urls">
              <el-input v-model="urlForm.urls" type="textarea" :rows="3" placeholder="https://site1.com\nhttps://site2.com" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitUrlForm">提交任务</el-button>
              <el-button @click="resetUrlForm">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-if="activeTab === 'input'" class="collect-section">
          <div class="collect-section-title">手动录入任务</div>
          <el-form label-width="80px" :model="inputForm" :rules="inputRules" ref="inputFormRef" class="collect-form-block">
            <el-form-item label="文章标题" prop="title">
              <el-input v-model="inputForm.title" placeholder="请输入文章标题" />
            </el-form-item>
            <el-form-item label="任务名称" prop="name">
              <el-input v-model="inputForm.name" placeholder="例如：AI 行业新闻录入" />
            </el-form-item>
            <el-form-item label="关键词" prop="keywords">
              <el-input v-model="inputForm.keywords" placeholder="关键词1; 关键词2" />
            </el-form-item>
            <el-form-item label="内容" prop="content">
              <el-input v-model="inputForm.content" type="textarea" :rows="4" placeholder="请输入新闻内容..." />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitInputForm">提交录入</el-button>
              <el-button @click="resetInputForm">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-if="activeTab === 'qa'" class="collect-section">
          <div class="collect-section-title">关键词问答采集</div>
          <el-form label-width="80px" :model="qaForm" ref="qaFormRef" class="collect-form-block">
            <el-form-item label="问题">
              <el-input v-model="qaForm.question" placeholder="请输入要采集的问题" />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="qaForm.keywords" placeholder="关键词1; 关键词2" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitQaForm">提交采集</el-button>
              <el-button @click="resetQaForm">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-if="activeTab === 'result'" class="collect-section">
          <div class="collect-section-title">采集结果</div>
          <el-table
            :data="groupedResultList"
            style="width:100%"
            :row-key="(row) => row.task_name || row.taskName"
            border
            ref="resultTable"
            @selection-change="onSelectionChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column
              type="expand"
              width="40"
              v-slot="{ row }"
            >
              <el-table :data="row.articles" border style="width:100%;">
                <el-table-column prop="title" label="标题" width="180" />
                <el-table-column prop="keywords" label="关键词" width="100" />
                <el-table-column prop="date" label="日期" width="120" />
                <el-table-column prop="summary" label="摘要" />
                <el-table-column label="操作" width="140">
                  <template #default="scope2">
                    <el-button size="mini" @click="previewResult(scope2.row)">预览</el-button>
                    <el-button size="mini" type="danger" @click="removeResult(scope2.row)" style="margin-left:4px;">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-table-column>
            <el-table-column prop="task_name" label="任务名称" width="180">
              <template #default="scope">
                <span style="font-weight:bold;">{{scope.row.task_name}}</span>
                <el-link type="primary" style="margin-left:12px;" @click.stop="selectTaskGroup(scope.row)">全选本任务</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="count" label="文章数" width="80" />
          </el-table>
        </div>
      </el-card>
      <el-card class="collect-right-card" shadow="hover">
        <div class="collect-preview-title">最近运行预览</div>
        <div v-if="isRefreshingPreview" style="color:#909399;font-size:12px;margin-bottom:8px;">正在刷新...</div>
        <el-empty v-if="previewList.length === 0" description="暂无预览" />
        <div v-else>
          <div v-for="item in previewList" :key="item.title" class="collect-preview-item">
            <div class="collect-preview-item-title">{{item.title}}</div>
            <div class="collect-preview-item-meta">{{item.date}} · {{item.link}}</div>
            <div class="collect-preview-item-summary">{{item.summary}}</div>
            <el-button size="mini" @click="previewResult(item)">预览</el-button>
          </div>
        </div>
        <el-dialog v-model="previewDialogVisible" title="采集内容预览" width="500px">
          <div v-if="previewItem">
            <div class="collect-preview-dialog-title">{{previewItem.title}}</div>
            <div class="collect-preview-dialog-meta">{{previewItem.date}} · {{previewItem.link}}</div>
            <div class="collect-preview-dialog-summary">{{previewItem.summary}}</div>
          </div>
        </el-dialog>
        <!-- 开发调试面板已移除 -->
      </el-card>
    </div>
  </div>
</template>

<script>

import collectApi from '@/api/model/collect'

export default {
  name: 'CollectTaskContent',
  data() {
    return {
      activeTab: 'url',
      urlForm: { name: '', keywords: '', urls: '' },
      urlRules: {
        name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
        keywords: [{ required: true, message: '请输入关键词', trigger: 'blur' }],
        urls: [{ required: true, message: '请输入URL列表', trigger: 'blur' }],
      },
  inputForm: { title: '', name: '', keywords: '', content: '' },
      inputRules: {
        title: [{ required: true, message: '请输入文章标题', trigger: 'blur' }],
        name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
        content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
      },
      qaForm: { question: '', keywords: '' },
  resultList: [], // 采集结果（原始）
  groupedResultList: [], // 按任务分组
  selectedRows: [],
      previewList: [], // 右侧预览
      previewDialogVisible: false,
      previewItem: null,
      // 为防止并发请求的响应乱序覆盖最新数据，引入请求序号
      resultFetchSeq: 0,
      pollingTimer: null,
      isRefreshingPreview: false,
  lastPreviewCount: 0
    }
  },
  beforeUnmount() {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer)
      this.pollingTimer = null
    }
  },
  created() {
    this.fetchCollectResults();
  },
  methods: {
    startPreviewPolling(expectTaskName = '') {
      // 清理旧的
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
      this.isRefreshingPreview = true
      const start = Date.now()
      const timeout = 30 * 1000
      this.lastPreviewCount = this.resultList.length
      this.pollingTimer = setInterval(async () => {
        await this.fetchCollectResults()
        const gotNew = this.resultList.length > this.lastPreviewCount
        const gotExpect = expectTaskName && this.resultList.some(it => it.task_name === expectTaskName)
        const overtime = Date.now() - start > timeout
        if (gotNew || gotExpect || overtime) {
          clearInterval(this.pollingTimer)
          this.pollingTimer = null
          this.isRefreshingPreview = false
        }
      }, 2000)
    },
    async fetchCollectResults() {
      // 递增请求序号，后返回的旧请求将被丢弃
      const currentSeq = ++this.resultFetchSeq;
      try {
        const res = await collectApi.collect.result.get();
        // 如果期间有更新触发新的请求，这里丢弃旧结果，避免覆盖最新数据
        if (currentSeq !== this.resultFetchSeq) return;
  // 开发调试：打印后端原始响应到控制台，UI 不再保存原始响应
  try { console.debug('[fetchCollectResults] api raw response:', res); } catch(e){ console.debug('[fetchCollectResults] console.debug error', e) }

        // 后端可能直接返回数组，也可能返回 { data: [...] }，统一规范为 items
        let items = [];
        if (Array.isArray(res)) {
          items = res;
        } else if (res && Array.isArray(res.data)) {
          items = res.data;
        }

        // 规范 items，items 可能为空
        if (items && items.length) {
          this.resultList = items.map(item => ({
            id: item.id,
            title: item.title,
            task_name: item.task_name || '未分组',
            keywords: item.keywords || '',
            date: item.date || item.create_time,
            summary: item.summary,
            link: item.source || item.create_time || '',
            content: item.content
          }));
          // 分组
          const groupMap = {};
          this.resultList.forEach(item => {
            if (!groupMap[item.task_name]) groupMap[item.task_name] = { task_name: item.task_name, articles: [], count: 0 };
            groupMap[item.task_name].articles.push(item);
            groupMap[item.task_name].count++;
          });
          this.groupedResultList = Object.values(groupMap);
          // 调试：打印分组信息，便于在浏览器控制台检查实际数据
          try { console.debug('[debug] groupedResultList', this.groupedResultList, this.groupedResultList.length); } catch(e){ console.debug('[debug] groupedResultList error', e) }
          // 右侧预览只显示前4条
          this.previewList = this.resultList.slice(0, 4);
        }
        else {
          // 如果没有 items，确保 groupedResultList 清空并记录调试信息
          this.groupedResultList = [];
          try { console.debug('[debug] fetchCollectResults no items, res:', res); } catch(e){ console.debug('[debug] fetchCollectResults no items error', e) }
        }
      } catch (e) {
        this.$message.error('采集结果获取失败');
      }
    },
    onSelectionChange(val) {
      this.selectedRows = val;
    },
    selectTaskGroup(group) {
      // 选中所有属于该任务的文章
      this.$refs.resultTable.clearSelection();
      this.groupedResultList.forEach(g => {
        if (g.task_name === group.task_name) {
          g.articles.forEach(row => {
            this.$refs.resultTable.toggleRowSelection(row, true);
          });
        }
      });
    },
    async submitUrlForm() {
      this.$refs.urlFormRef.validate(async valid => {
        if (valid) {
          try {
            // 直接调用 collectApi
            const res = await collectApi.collect.url.post(this.urlForm)
            this.$message.success(res.msg || 'URL任务已提交！')
            // 提交后立即刷新一次
            this.fetchCollectResults()
            // 短时轮询，直到出现新结果或超时
            this.startPreviewPolling(this.urlForm.name)
          } catch (e) {
            this.$message.error('采集任务提交失败')
          }
        }
      });
    },
    resetUrlForm() {
      this.$refs.urlFormRef.resetFields();
    },
    async submitInputForm() {
      this.$refs.inputFormRef.validate(async valid => {
        if (!valid) return;
        try {
          const payload = { ...this.inputForm };
          const res = await collectApi.collect.input.post(payload)
          this.$message.success(res.msg || '录入任务已提交！')
          this.fetchCollectResults()
          this.startPreviewPolling(this.inputForm.name)
        } catch (e) {
          this.$message.error('录入任务提交失败')
        }
      });
    },
    resetInputForm() {
      this.inputForm = { title: '', name: '', keywords: '', content: '' };
    },
    submitQaForm() {
      this.$message.success('关键词问答采集已提交！');
    },
    resetQaForm() {
      this.qaForm = { question: '', keywords: '' };
    },
    previewResult(item) {
      this.previewItem = item;
      this.previewDialogVisible = true;
    },
    async removeResult(item) {
      this.$confirm('确定要删除该采集结果吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          // 需传递 id
          const res = await collectApi.collect.remove.post({ id: item.id })
          if (res && res.code === 200) {
            this.$message.success('删除成功')
            this.fetchCollectResults()
          } else {
            this.$message.error(res.msg || '删除失败')
          }
        } catch (e) {
          this.$message.error('删除失败')
        }
  }).catch((err) => { console.debug('[fetchCollectResults] fetch error', err); });
    }
  }

  
}
</script>

<style scoped>
.collect-root {
  width: 100vw;
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0;
}
.collect-main-layout {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  width: 100%;
  margin-top: 48px;
  margin-bottom: 40px;
  margin-left: 80px;
  gap: 40px;
}
.collect-left-card {
  width: 600px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 32px 24px 32px;
  background: #fff;
}
.collect-tab-bar {
  margin-bottom: 24px;
}
.collect-section {
  background: #f9fafb;
  border-radius: 12px;
  box-shadow: 0 2px 8px 0 rgba(0,0,0,0.03);
  padding: 18px 24px 12px 24px;
  margin-bottom: 18px;
}
.collect-section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #3a4a5b;
}
.collect-form-block {
  background: #fff;
  border-radius: 8px;
  padding: 18px 18px 8px 18px;
  margin-bottom: 0;
}
.collect-right-card {
  flex: 1;
  min-width: 320px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 24px 24px 24px;
  background: #fff;
}
.collect-preview-title {
  color: #888;
  font-weight: bold;
  margin-bottom: 12px;
  font-size: 16px;
}
.collect-preview-item {
  margin-bottom: 18px;
}
.collect-preview-item-title {
  font-weight: bold;
  font-size: 16px;
}
.collect-preview-item-meta {
  color: #aaa;
  font-size: 13px;
  margin-bottom: 2px;
}
.collect-preview-item-summary {
  color: #888;
  font-size: 14px;
}
.collect-preview-dialog-title {
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 8px;
}
.collect-preview-dialog-meta {
  color: #aaa;
  font-size: 13px;
  margin-bottom: 2px;
}
.collect-preview-dialog-summary {
  color: #888;
  font-size: 14px;
}
</style>
