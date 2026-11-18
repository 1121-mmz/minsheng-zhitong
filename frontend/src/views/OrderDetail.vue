<template>
  <div class="detail-page">
    <el-card shadow="never" class="detail-card">
      <template #header>
        <div class="header-content">
          <div class="title">
            <el-button link @click="goBack" style="margin-right: 15px;">
              <el-icon><Back /></el-icon> 返回
            </el-button>
            <span>工单处理台</span>
          </div>
          <el-tag :type="orderForm.status === '已派单' ? 'success' : 'warning'" size="large" effect="dark">
            {{ orderForm.status }}
          </el-tag>
        </div>
      </template>

      <el-empty v-if="!orderForm.id" description="工单不存在或加载失败" />
      
      <el-form v-else :model="orderForm" label-position="top" class="glass-form">
        <!-- 只读区：市民提交的信息 -->
        <div class="section-title">市民诉求信息</div>
        <el-form-item label="诉求摘要">
          <el-input v-model="orderForm.summary" type="textarea" :rows="3" readonly class="readonly-input" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="AI 推荐主办单位">
              <el-input v-model="orderForm.mainDept" readonly />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="AI 推荐协办单位">
              <el-input v-model="orderForm.assistDept" readonly />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="AI 检索依据 (RAG)">
          <el-input v-model="orderForm.basis" type="textarea" :rows="2" readonly class="basis-input" />
        </el-form-item>

        <el-divider />

        <!-- 可编辑区：管理员操作 -->
        <div class="section-title">人工审核与派发</div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最终主办单位 (可修改)">
              <el-input v-model="orderForm.mainDept" :disabled="orderForm.status === '已派单'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最终协办单位 (可修改)">
              <el-input v-model="orderForm.assistDept" :disabled="orderForm.status === '已派单'" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="action-bar">
          <el-button 
            type="primary" 
            size="large" 
            class="submit-btn" 
            :disabled="orderForm.status === '已派单'" 
            @click="confirmDispatch"
          >
            {{ orderForm.status === '已派单' ? '该工单已处理完成' : '审核通过并正式派发' }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '../api/request'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const orderForm = ref({})

// 页面加载时，根据路由里的 ID 获取数据
onMounted(async () => {
  const id = route.params.id
  try {
    const res = await request.get('/orders')
    // 从列表中找到当前点击的那一条
    const current = res.data.find(item => item.id == id)
    if (current) {
      orderForm.value = current
    }
  } catch (e) {
    console.error('获取详情失败', e)
  }
})

const goBack = () => {
  router.push('/orders')
}

const confirmDispatch = async () => {
  try {
    // 调用后端的 PUT 接口更新状态
    await request.put(`/orders/${orderForm.value.id}`, orderForm.value)
    ElMessage.success('工单已成功派发！')
    orderForm.value.status = '已派单'
  } catch (error) {
    ElMessage.error('派单失败')
  }
}
</script>

<style scoped>
.detail-page { height: 100%; padding: 20px; box-sizing: border-box; background: #f1f5f9; display: flex; justify-content: center; }
.detail-card { width: 100%; max-width: 900px; border-radius: 8px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 18px; font-weight: bold; display: flex; align-items: center; color: #303133; }
.section-title { font-size: 15px; font-weight: bold; color: #409eff; margin-bottom: 16px; padding-left: 8px; border-left: 4px solid #409eff; }
.glass-form { padding: 10px; }
:deep(.el-form-item__label) { font-weight: bold; color: #475569; }
.readonly-input :deep(.el-textarea__inner) { background-color: #f8fafc; cursor: not-allowed; color: #64748b; }
.basis-input :deep(.el-textarea__inner) { background-color: #f0f9eb; color: #529b2e; border: 1px solid #e1f3d8; cursor: not-allowed; }
.action-bar { margin-top: 30px; text-align: center; }
.submit-btn { width: 50%; height: 48px; font-size: 16px; font-weight: bold; border-radius: 8px; background: linear-gradient(135deg, #409eff, #79bbff); border: none; }
</style>