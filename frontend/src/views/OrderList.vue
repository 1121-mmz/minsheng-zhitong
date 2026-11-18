<template>
  <div class="order-page">
    <el-card shadow="never" class="box-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: bold; font-size: 16px;">工单流水记录</span>
          
          <el-radio-group v-model="filterStatus" size="small">
            <el-radio-button label="全部" />
            <el-radio-button label="待派单" />
            <el-radio-button label="已派单" />
          </el-radio-group>
        </div>
      </template>
      
      <div class="table-wrapper">
        <el-table :data="filteredData" style="width: 100%; height: 100%;" stripe>
          <el-table-column prop="id" label="工单号" width="90" />
          <el-table-column prop="summary" label="诉求摘要" show-overflow-tooltip min-width="180" />
          
          <el-table-column prop="submitter" label="提交人" width="110">
            <template #default="scope">
              <span style="font-weight: bold; color: #409eff;">{{ scope.row.submitter || '市民用户' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="mainDept" label="主办单位" width="140" />
          
          <el-table-column prop="confidence" label="AI置信度" width="100">
            <template #default="scope">
              <el-tag 
                :type="scope.row.confidence >= 0.8 ? 'success' : 'warning'" 
                effect="light" 
                size="small"
              >
                {{ (scope.row.confidence * 100).toFixed(0) }}%
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === '已派单' ? 'success' : 'warning'" effect="plain">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="createTime" label="提交时间" width="170">
            <template #default="scope">
              {{ scope.row.createTime ? scope.row.createTime.replace('T', ' ') : '' }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <!-- 👇 操作列：去处理 + 删除 -->
              <el-button link type="primary" size="small" @click="$router.push('/order-detail/' + scope.row.id)">
                去处理
              </el-button>
              <el-button link type="danger" size="small" @click="handleDelete(scope.row.id)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '../api/request'
import { ElMessage, ElMessageBox } from 'element-plus' // 👈 引入弹窗组件

const tableData = ref([])
const filterStatus = ref('全部')

// 动态过滤数据
const filteredData = computed(() => {
  if (filterStatus.value === '全部') {
    return tableData.value
  }
  return tableData.value.filter(item => item.status === filterStatus.value)
})

// 获取数据
const fetchOrders = async () => {
  try {
    const res = await request.get('/orders')
    tableData.value = res.data
  } catch (e) {
    console.error('获取列表失败', e)
  }
}

// 👇 删除逻辑（带二次确认）
const handleDelete = (id) => {
  ElMessageBox.confirm(
    '确定要永久删除这条工单吗？删除后不可恢复。',
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await request.delete(`/orders/${id}`)
      ElMessage.success('工单已成功删除')
      fetchOrders() // 刷新列表
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }).catch(() => {
    // 用户点击取消，什么都不做
  })
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.order-page { height: 100%; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; }
.box-card { flex: 1; display: flex; flex-direction: column; border-radius: 8px; }
:deep(.el-card__body) { flex: 1; padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.table-wrapper { flex: 1; padding: 20px; height: 100%; box-sizing: border-box; overflow: hidden; }
</style>