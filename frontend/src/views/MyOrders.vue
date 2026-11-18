<template>
  <div class="order-page">
    <el-card shadow="never" class="box-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: bold; font-size: 16px;">我的诉求记录</span>
        </div>
      </template>
      
      <div class="table-wrapper">
        <el-table :data="tableData" style="width: 100%; height: 100%;" stripe>
          <el-table-column prop="id" label="工单号" width="100" />
          <el-table-column prop="summary" label="诉求摘要" show-overflow-tooltip min-width="200" />
          <el-table-column prop="mainDept" label="处理单位" width="150" />
          <el-table-column prop="status" label="当前状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === '已派单' ? 'success' : 'warning'" effect="plain">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="提交时间" width="180">
            <template #default="scope">
              {{ scope.row.createTime ? scope.row.createTime.replace('T', ' ') : '' }}
            </template>
          </el-table-column>
          <el-table-column label="满意度评价" width="220" fixed="right">
            <template #default="scope">
              <!-- 👇 如果已经评价过，显示星星；如果没评价，显示星星供点击 -->
              <el-rate 
                v-model="scope.row.satisfaction" 
                :disabled="scope.row.status !== '已派单' || scope.row.satisfaction > 0"
                @change="(val) => handleRate(scope.row.id, val)"
                show-score
                score-template="{value} 星"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

const tableData = ref([])
const username = localStorage.getItem('username')

const fetchMyOrders = async () => {
  try {
    const res = await request.get(`/orders/my/${username}`)
    tableData.value = res.data
  } catch (e) {
    console.error('获取列表失败', e)
  }
}

// 点击星星进行评价
const handleRate = async (id, score) => {
  if (!score) return
  try {
    await request.put(`/orders/rate/${id}/${score}`)
    ElMessage.success('感谢您的评价！')
    fetchMyOrders() // 刷新数据
  } catch (e) {
    ElMessage.error('评价失败')
  }
}

onMounted(() => {
  fetchMyOrders()
})
</script>

<style scoped>
.order-page { height: 100%; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; }
.box-card { flex: 1; display: flex; flex-direction: column; border-radius: 8px; }
:deep(.el-card__body) { flex: 1; padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.table-wrapper { flex: 1; padding: 20px; height: 100%; box-sizing: border-box; overflow: hidden; }
</style>