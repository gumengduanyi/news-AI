
<template>
  <div class="auto-release-root2">
    <div class="main2-layout">
      <!-- 主内容区 -->
      <el-card class="main2-content-card" shadow="hover">
        <div class="main2-title">自动发送设置</div>
        <div class="main2-section">
          <div class="main2-label">报告邮箱（可多项）</div>
          <div class="main2-email">a@org.com; b@org.com</div>
        </div>
        <div class="main2-section">
          <div class="main2-label">发送周期</div>
          <div class="main2-value">每天 06:00</div>
        </div>
        <div class="main2-section">
          <div class="main2-label2">固定参数</div>
          <div class="main2-row">
            <div class="main2-label3">模型：</div>
            <div class="main2-value2">DeepSeek-R1</div>
            <div class="main2-label3">提示词：</div>
            <div class="main2-value2">AI周报</div>
          </div>
          <div class="main2-row">
            <div class="main2-label3">模板：</div>
            <div class="main2-value2">HTML</div>
            <div class="main2-label3">素材：</div>
            <div class="main2-value2">最新采集</div>
          </div>
        </div>
        <div class="main2-btn-row">
          <el-button class="main2-btn-test" type="text">测试发送</el-button>
          <el-button class="main2-btn-save" type="primary" round>保存并启用</el-button>
        </div>
        <div class="main2-section main2-section-selftest">
          <div class="main2-label4">自检测试</div>
          <div class="main2-self-list">
            <span class="main2-self-item success">✔ Render literal mustache</span>
            <span class="main2-self-item success">✔ No double-brace expr in JSX</span>
            <span class="main2-self-item success">✔ Pages registered</span>
          </div>
        </div>
      </el-card>
      <!-- 日志区 -->
      <el-card class="main2-log-card" shadow="hover">
        <div class="main2-log-title">最近任务日志</div>
        <div class="main2-log-content">
          <div class="main2-log-line">[06:00] 触发 → 生成 → 发送至 6 位收件人：成功</div>
          <div class="main2-log-line">[06:00] 触发 → 生成 → 发送：1 失败（重试中）</div>
        </div>
      </el-card>
    </div>
  </div>
</template>


<script>
export default {
  name: 'AutomaticReleaseSettings'
}
</script>


<style lang="scss" scoped>
.auto-release-root2 {
  font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  background: #f6f8fa;
  min-height: 100vh;
  .main2-layout {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    padding: 48px 0 0 80px;
    gap: 40px;
    .main2-content-card {
      flex: 1;
      max-width: 800px;
      border-radius: 18px;
      box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
      border: none;
      padding: 40px 48px 32px 48px;
      background: #fff;
      .main2-title {
        font-size: 22px;
        font-weight: 700;
        color: #2a3a4a;
        margin-bottom: 18px;
      }
      .main2-section {
        background: #f9fafb;
        border-radius: 12px;
        box-shadow: 0 2px 8px 0 rgba(0,0,0,0.03);
        padding: 18px 24px 12px 24px;
        margin-bottom: 18px;
      }
      .main2-label {
        font-size: 15px;
        color: #7b8ba3;
        margin-bottom: 2px;
        margin-top: 0;
      }
      .main2-email {
        font-size: 16px;
        color: #bfc8d7;
        margin-bottom: 12px;
      }
      .main2-value {
        font-size: 16px;
        color: #222;
        margin-bottom: 12px;
      }
      .main2-label2 {
        font-size: 13px;
        color: #bfc8d7;
        margin-bottom: 6px;
      }
      .main2-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        .main2-label3 {
          font-size: 14px;
          color: #bfc8d7;
          min-width: 60px;
        }
        .main2-value2 {
          font-size: 16px;
          color: #222;
          min-width: 80px;
          margin-right: 18px;
        }
      }
      .main2-btn-row {
        margin-top: 12px;
        display: flex;
        gap: 12px;
        .main2-btn-test {
          font-size: 14px;
          color: #222;
          background: none;
          border: none;
          padding: 0 10px;
        }
        .main2-btn-save {
          font-size: 16px;
          font-weight: 700;
          border-radius: 18px;
          padding: 0 18px;
          height: 36px;
        }
      }
      .main2-section-selftest {
        margin-top: 32px;
        margin-bottom: 0;
      }
      .main2-label4 {
        font-size: 18px;
        font-weight: 700;
        color: #2a3a4a;
        margin-bottom: 8px;
      }
      .main2-self-list {
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        .main2-self-item {
          font-size: 14px;
          color: #00c080;
          &.success {
            font-weight: 700;
          }
        }
      }
    }
    .main2-log-card {
      width: 340px;
      border-radius: 18px;
      box-shadow: 0 4px 24px 0 rgba(0,0,0,0.07);
      border: none;
      padding: 32px 24px 24px 24px;
      background: #fff;
      .main2-log-title {
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 12px;
        color: #bfc8d7;
      }
      .main2-log-content {
        background: #f9fafb;
        border: none;
        border-radius: 8px;
        padding: 12px 12px 8px 12px;
        min-height: 60px;
        margin-bottom: 12px;
        .main2-log-line {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
          font-size: 14px;
          color: #222;
          margin-bottom: 6px;
        }
      }
    }
  }
}
</style>
