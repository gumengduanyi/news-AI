<template>
  <div class="dashboard-home">
    <div class="dashboard-hero">
  <h1>首页</h1>
  <p>欢迎使用信息自动采集发布系统！</p>
    </div>
    <div class="dashboard-grid">
      <!-- placeholder for cards -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardHome',
}
</script>

<style scoped>
h1 {
  margin-top: 12px;
  text-align: center;
}
p {
  text-align: center;
  color: #888;
}

.dashboard-home { padding: 18px 24px }
.dashboard-hero { max-width: 820px; margin: 0 auto 18px; }
.dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; max-width: 1200px; margin: 0 auto }

@media (max-width: 600px){
  .dashboard-home { padding: 12px }
}
</style>
