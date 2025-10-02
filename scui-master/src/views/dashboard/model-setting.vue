<template>
  <div class="model-setting-root">
    <div class="model-setting-main-layout">
      <el-card class="model-setting-card" shadow="hover">
        <div class="model-setting-title">模型设置</div>
        <div class="model-setting-section-title">模型提供商</div>
        <el-table :data="modelList" border style="width: 100%" class="model-setting-table">
          <el-table-column prop="provider" label="模型提供商" width="180"/>
          <el-table-column prop="api" label="API地址" />
          <el-table-column prop="modelId" label="模型ID" width="180"/>
          <el-table-column prop="status" label="连通性测试" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.status === '已启用' ? 'success' : 'info'">{{ scope.row.status }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="model-setting-section-title" style="margin-top:32px;">自检测试</div>
        <el-row style="margin-top: 8px;">
          <el-col :span="6"><el-tag type="success" effect="plain">Render literal mustache</el-tag></el-col>
          <el-col :span="6"><el-tag type="success" effect="plain">No double-brace expr in JSX</el-tag></el-col>
          <el-col :span="6"><el-tag type="success" effect="plain">Pages registered</el-tag></el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModelSetting',
  data() {
    return {
      modelList: [
        {
          provider: '豆包',
          api: 'https://open.bigmodel.cn/api/paas/v4',
          modelId: 'glm-4',
          status: '已启用'
        },
        {
          provider: 'DeepSeek',
          api: 'https://api.deepseek.com/v1',
          modelId: 'deepseek-r1',
          status: '已启用'
        }
      ]
    }
  }
}
</script>

<style scoped>
.model-setting-root {
  width: 100vw;
  min-height: 100vh;
  background: #f6f8fa;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0;
}
.model-setting-main-layout {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  width: 100%;
  margin-top: 48px;
  margin-bottom: 40px;
  margin-left: 80px;
}
.model-setting-card {
  width: 900px;
  border-radius: 18px;
  box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
  border: none;
  padding: 32px 32px 24px 32px;
  background: #fff;
}
.model-setting-title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #3a4a5b;
}
.model-setting-section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 18px;
  color: #3a4a5b;
}
.model-setting-table {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 0;
}
</style>
