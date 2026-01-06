<template>
  <div class="wechat-state">
    <el-card>
      <h3>登录态管理（wechat_state.json）</h3>
      <p>此界面仅用于获取项目内保存的 `wechat_state.json` 文件。</p>
      <el-button type="primary" @click="downloadState" :loading="loading">下载登录态</el-button>
      <el-button @click="helpVisible = true">如何保存登录态</el-button>
      <el-button type="primary" @click="startSave" :loading="saving">开始保存登录态</el-button>

      <!-- Inline save panel: shown when saveVisible to avoid dialog being hidden by other windows -->
      <div v-if="saveVisible" class="inline-save-panel" style="margin-top:12px; padding:12px; border:1px dashed #dcdfe6; border-radius:6px; background:#fbfbfb">
        <div style="display:flex; align-items:center; justify-content:space-between">
          <div>
            <strong>保存登录态进行中</strong>
            <div style="margin-top:6px">请在服务器打开的浏览器中完成登录。当前状态：
              <span v-if="saveResult && saveResult.status==='pending'">检测到登录，待确认（会话: {{ saveSessionId }})</span>
              <span v-else-if="saveError" style="color:#f56c6c">{{ saveError }}</span>
              <span v-else>等待登录...</span>
            </div>
          </div>
          <div>
            <el-button v-if="saveResult && saveResult.status==='pending'" type="primary" @click="confirmSave" :loading="saving">确认保存</el-button>
            <el-button v-if="saveResult && saveResult.status==='pending'" @click="cancelSaveSession" :disabled="saving" style="margin-left:8px">取消</el-button>
            <el-button v-else @click="saveVisible=false" style="margin-left:8px">关闭</el-button>
          </div>
        </div>
      </div>

      <el-dialog title="如何保存登录态" v-model:visible="helpVisible">
        <div>
          <p>两种保存方式：在本机运行交互脚本，或在服务器上启动保存流程（会打开一个可视化浏览器窗口，请在服务器所在机器上完成扫码/登录）。</p>
          <p>在本机运行（示例）：</p>
          <el-input type="textarea" :rows="3" :readonly="true" v-model="cmd" />
          <p>在服务器上保存：点击页面上的“开始保存登录态”按钮，后台将在服务器上打开浏览器窗口并等待登录（默认超时 <strong>{{ timeout }}</strong> 秒）。</p>
        </div>
        <template #footer>
          <el-button @click="helpVisible = false">关闭</el-button>
        </template>
      </el-dialog>

      <el-dialog title="保存登录态" v-model:visible="saveVisible">
        <div>
          <p>超时时间（秒）：</p>
          <el-input-number v-model="timeout" :min="30" :max="3600" />
          <div style="margin-top:12px">
            <el-alert v-if="saveError" :title="saveError" type="error" show-icon />
            <el-alert v-if="saveResult && saveResult.status==='ok'" title="保存成功，已写入实例目录" type="success" show-icon />
            <div v-if="saveResult && saveResult.status==='ok'" style="margin-top:8px">
              <el-button type="primary" @click="downloadState">下载 wechat_state.json</el-button>
            </div>
            <div v-if="!saveResult && !saveError" style="margin-top:8px">
              <el-progress :percentage="progressPercent" :status="saving ? 'active' : 'exception'" />
              <p style="margin-top:8px">等待登录并保存...（请在服务器打开的浏览器中完成扫码/登录）</p>
            </div>
            <div v-if="saveResult && saveResult.status==='pending'" style="margin-top:8px">
              <el-alert title="检测到登录，等待您确认是否保存当前登录态" type="info" show-icon />
              <p style="margin-top:8px">会话 ID: {{ saveSessionId }}</p>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button v-if="!(saveResult && saveResult.status==='pending')" @click="cancelSave" :disabled="saving">关闭</el-button>
          <div v-else>
            <el-button type="primary" @click="confirmSave" :disabled="saving">确认保存</el-button>
            <el-button @click="cancelSaveSession" :disabled="saving" style="margin-left:8px">取消并关闭</el-button>
          </div>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'WechatState',
  data() {
    return {
      loading: false,
      helpVisible: false,
      cmd: "curl -X POST '/api/wechat/save' -H 'Content-Type: application/json' -d '{\"timeout\":300}'",
      saveVisible: false,
      saving: false,
      saveResult: null,
      saveError: '',
      saveSessionId: null,
      timeout: 300,
      progressPercent: 0
    }
  },
  methods: {
    async downloadState() {
      this.loading = true
      try {
        const res = await fetch('/api/wechat/state', { method: 'GET', credentials: 'include' })
        if (!res.ok) {
          const j = await res.json().catch(()=>({msg:'无法下载'}))
          this.$message.error('下载失败: '+(j.msg||res.status))
          return
        }
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'wechat_state.json'
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
        this.$message.success('已开始下载')
      } catch (e) {
        this.$message.error('请求失败: '+e.message)
      } finally {
        this.loading = false
      }
    },
    async confirmSave() {
      if (!this.saveSessionId) return
      this.saving = true
      try {
        const res = await fetch('/api/wechat/save/confirm', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ session_id: this.saveSessionId, action: 'confirm' })
        })
        if (!res.ok) {
          const j = await res.json().catch(()=>({msg:'确认保存失败'}))
          this.saveError = j.msg || `确认保存失败: ${res.status}`
        } else {
          const j = await res.json()
          this.saveResult = j
          this.$message.success('已保存登录态')
        }
      } catch (e) {
        this.saveError = e.message || String(e)
      } finally {
        this.saving = false
        this.progressPercent = this.saveResult ? 100 : 0
      }
    },
    async cancelSaveSession() {
      if (!this.saveSessionId) return this.cancelSave()
      this.saving = true
      try {
        const res = await fetch('/api/wechat/save/confirm', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ session_id: this.saveSessionId, action: 'cancel' })
        })
        if (!res.ok) {
          const j = await res.json().catch(()=>({msg:'取消失败'}))
          this.saveError = j.msg || `取消失败: ${res.status}`
        } else {
          this.saveResult = null
          this.saveSessionId = null
          this.saveVisible = false
          this.$message.info('已取消保存会话')
        }
      } catch (e) {
        this.saveError = e.message || String(e)
      } finally {
        this.saving = false
      }
    },
    showHelp() { this.helpVisible = true },
    cancelSave() { this.saveVisible = false; this.saveResult = null; this.saveError = ''; this.progressPercent = 0 },
    async startSave() {
      this.saveVisible = true
      this.saving = true
      this.saveResult = null
      this.saveError = ''
      this.progressPercent = 10
      try {
        const controller = new AbortController()
        const timeoutMs = (this.timeout + 20) * 1000
        const timer = setTimeout(() => controller.abort(), timeoutMs)
        const res = await fetch('/api/wechat/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ timeout: this.timeout }),
          signal: controller.signal
        })
        clearTimeout(timer)
        this.progressPercent = 70
        if (!res.ok) {
          const j = await res.json().catch(()=>({msg:'保存失败'}))
          this.saveError = j.msg || `保存失败: ${res.status}`
        } else {
          const j = await res.json()
          this.saveResult = j
          if (j.status === 'pending') this.saveSessionId = j.session_id
        }
      } catch (e) {
        if (e.name === 'AbortError') this.saveError = '保存超时或被取消'
        else this.saveError = e.message || String(e)
      } finally {
        this.saving = false
        this.progressPercent = this.saveResult ? 100 : 0
      }
    }
  }
}
</script>

<style scoped>
.wechat-state pre { background:#f6f8fa; padding:12px; border-radius:6px }
</style>
