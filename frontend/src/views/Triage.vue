<template>
  <div class="triage-page">
    <div class="triage-card">
      
      <!-- 左侧：对话区 -->
      <div class="chat-panel">
        <div class="panel-header">
          <div class="brand">
            <el-icon class="brand-icon"><ChatDotRound /></el-icon>
            <span>{{ role === 'ADMIN' ? '民声直通 · 智能座席' : '民声直通 · 市民通道' }}</span>
          </div>
          <el-tag effect="dark" type="success" round size="small">Agent Online</el-tag>
        </div>
        
        <div class="messages-container" ref="msgContainer">
          <div v-for="(msg, index) in store.messages" :key="index" :class="['message-row', msg.role]">
            <div class="avatar">
              <el-avatar v-if="msg.role === 'agent'" :size="32" class="agent-avatar">AI</el-avatar>
              <el-avatar v-else :size="32" class="user-avatar">市</el-avatar>
            </div>
            <div class="bubble">{{ msg.content }}</div>
          </div>
          
          <!-- AI 思考动画 -->
          <div v-if="store.isThinking" class="message-row agent">
            <div class="avatar"><el-avatar :size="32" class="agent-avatar">AI</el-avatar></div>
            <div class="bubble typing"><span></span><span></span><span></span></div>
          </div>
        </div>

        <div class="input-container">
          <el-input 
            v-model="inputText" 
            placeholder="输入诉求内容..." 
            size="large"
            clearable
            @keyup.enter="handleSend"
            class="custom-input"
          >
            <template #append>
              <el-button type="primary" :icon="Promotion" @click="handleSend" :disabled="store.isThinking" />
            </template>
          </el-input>
        </div>
      </div>

      <!-- 右侧：工单看板区 -->
      <div class="order-panel">
        <div class="panel-header order-header">
          <div class="title">{{ role === 'ADMIN' ? '智能分诊工单详情' : '诉求提交详情' }}</div>
          <el-tag v-if="store.activeOrder.summary" type="warning" effect="plain" round>
            置信度: {{ (store.activeOrder.confidence * 100).toFixed(0) }}%
          </el-tag>
        </div>
        
        <div class="order-content">
          <el-empty v-if="!store.activeOrder.summary" description="等待接入诉求..." :image-size="120" />
          
          <el-form v-else :model="store.activeOrder" label-position="top" class="glass-form">
            <el-form-item label="诉求摘要">
              <el-input v-model="store.activeOrder.summary" type="textarea" :rows="2" readonly class="readonly-input" />
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="推荐主办单位">
                  <el-input v-model="store.activeOrder.mainDept" readonly>
                    <template #prefix><el-icon><OfficeBuilding /></el-icon></template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="协办单位">
                  <el-input v-model="store.activeOrder.assistDept" readonly>
                    <template #prefix><el-icon><User /></el-icon></template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="派单依据 (AI 检索真实返回)">
              <el-input v-model="store.activeOrder.basis" type="textarea" :rows="3" readonly class="basis-input">
                <template #prefix><el-icon><DocumentChecked /></el-icon></template>
              </el-input>
            </el-form-item>

            <div class="status-section">
              <span class="label">当前工单状态：</span>
              <el-tag :type="store.activeOrder.status === '待派单' ? 'warning' : 'success'" effect="dark" size="large">
                {{ store.activeOrder.status }}
              </el-tag>
            </div>

            <!-- 👇 提交按钮区 -->
            <div class="action-bar">
              <el-button 
                type="primary" 
                size="large" 
                class="glow-btn" 
                :disabled="store.activeOrder.status !== '待派单'" 
                @click="submitOrder"
              >
                {{ role === 'ADMIN' ? '确认并派发工单' : '提交诉求工单' }}
              </el-button>
            </div>
          </el-form>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useTriageStore } from '../stores/triage'
import { ChatDotRound, Promotion, OfficeBuilding, User, DocumentChecked } from '@element-plus/icons-vue'
import request from '../api/request'

// 获取当前角色和用户名
const role = localStorage.getItem('role') || 'USER'
const username = localStorage.getItem('username') || '未知用户'

const store = useTriageStore()
const inputText = ref('')
const msgContainer = ref(null)

// 监听消息滚动到底部
watch(() => store.messages.length, () => {
  nextTick(() => {
    if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  })
})

// 发送诉求给 AI
const handleSend = () => {
  if (!inputText.value || store.isThinking) return
  store.fetchTriage(inputText.value)
  inputText.value = ''
}

// 👇 核心修改：统一处理提交逻辑，并记录提交人
const submitOrder = async () => {
  // 如果市民提交，状态设为 '待派单'；如果管理员，设为 '已派单'
  const targetStatus = role === 'ADMIN' ? '已派单' : '待派单'
  
  const payload = {
    summary: store.activeOrder.summary,
    mainDept: store.activeOrder.mainDept,
    assistDept: store.activeOrder.assistDept,
    basis: store.activeOrder.basis,
    confidence: Number(store.activeOrder.confidence),
    status: targetStatus,
    submitter: username // 👈 关键：记录是谁提交的
  }
  
  try {
    await request.post('/orders', payload)
    
    if (role === 'ADMIN') {
      alert('工单已成功派发并入库！')
      store.activeOrder.status = '已派单' // 更新本地状态，让按钮变灰
    } else {
      alert('诉求已成功提交！请等待政务人员审核。')
      store.activeOrder.status = '已提交' // 更新本地状态，让按钮变灰
    }
    
  } catch (error) {
    console.error('保存工单失败:', error)
    alert('提交失败！请检查后端是否运行')
  }
}
</script>

<style scoped>
/* 外层页面：撑满高度，加上浅灰背景和内边距 */
.triage-page {
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
  background-color: #f1f5f9;
}

/* 内部大卡片：左右弹性布局 */
.triage-card {
  height: 100%;
  display: flex;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

/* ---------------- 左侧对话区 ---------------- */
.chat-panel {
  width: 380px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #ebeef5;
}

/* ---------------- 右侧工单区 ---------------- */
.order-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* 公共头部样式 */
.panel-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #ebeef5;
  background: #fafafa;
}
.brand { display: flex; align-items: center; font-size: 16px; font-weight: 600; }
.brand-icon { font-size: 20px; color: #409eff; margin-right: 8px; }
.order-header .title { font-size: 18px; font-weight: bold; color: #303133; }

/* 滚动内容区 */
.messages-container, .order-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 聊天气泡样式 */
.message-row { display: flex; margin-bottom: 20px; align-items: flex-start; }
.message-row.user { flex-direction: row-reverse; }
.avatar { margin: 0 10px; flex-shrink: 0; }
.agent-avatar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-size: 12px; }
.user-avatar { background: #f56c6c; font-size: 12px; }
.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-all;
}
.message-row.agent .bubble { background: #f8fafc; border: 1px solid #ebeef5; border-top-left-radius: 2px; }
.message-row.user .bubble { background: #409eff; color: #fff; border-top-right-radius: 2px; }

/* 输入框区域 */
.input-container { padding: 16px 20px; background: #fff; border-top: 1px solid #ebeef5; }
.custom-input :deep(.el-input-group__append) { background-color: #409eff; color: white; }

/* 打字动画 */
.typing span { display: inline-block; width: 6px; height: 6px; background: #a0a5b0; border-radius: 50%; margin: 0 2px; animation: bounce 1.4s infinite ease-in-out both; }
.typing span:nth-child(1) { animation-delay: -0.32s; } .typing span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* ---------------- 右侧表单样式 ---------------- */
.order-content { padding: 24px; }
:deep(.el-form-item__label) { font-weight: bold; color: #475569; padding-bottom: 4px; }
:deep(.el-input__wrapper), :deep(.el-textarea__inner) { border-radius: 6px; }
.readonly-input :deep(.el-textarea__inner) { background-color: #f1f5f9; cursor: not-allowed; color: #64748b; }
.basis-input :deep(.el-textarea__inner) { background-color: #f0f9eb; color: #529b2e; border: 1px solid #e1f3d8; }

.status-section {
  margin: 24px 0;
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}
.status-section .label { font-size: 15px; color: #475569; margin-right: 16px; font-weight: bold; }
.action-bar { margin-top: 10px; }
.glow-btn {
  width: 100%;
  background: linear-gradient(135deg, #409eff, #79bbff);
  border: none;
  font-weight: bold;
  letter-spacing: 1px;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
}
</style>