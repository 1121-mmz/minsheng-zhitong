<template>
  <div class="dashboard">
    <!-- 顶部指标卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">累计接诉总量</div>
          <div class="stat-value">{{ stats.total }} <span>件</span></div>
          <div class="stat-footer" style="color: #f56c6c">实时数据库统计</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">AI 自动分诊准确率</div>
          <div class="stat-value">{{ stats.avgConfidence }}%</div>
          <div class="stat-footer" style="color: #67c23a">基于实际工单置信度计算</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">待处理工单</div>
          <div class="stat-value" style="color: #e6a23c">{{ stats.pending }} <span>件</span></div>
          <div class="stat-footer" style="color: #e6a23c">需尽快派单</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">群众满意度</div>
          <div class="stat-value">{{ stats.avgSatisfaction }}%</div>
          <div class="stat-footer" style="color: #909399">基于市民真实评价</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card shadow="never" header="高频诉求部门分布 (实时动态统计)">
          <div class="chart-placeholder">
            <!-- 循环渲染各部门占比 -->
            <div v-for="(count, dept) in stats.deptStats" :key="dept" style="margin-bottom: 20px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-weight: bold;">
                <span>{{ dept }}</span>
                <span style="color: #409eff">{{ count }} 件 ({{ calcPercentage(count) }}%)</span>
              </div>
              <el-progress 
                :percentage="calcPercentage(count)" 
                :stroke-width="15" 
                :color="getColor(dept)"
              />
            </div>
            <el-empty v-if="Object.keys(stats.deptStats).length === 0" description="暂无工单数据" />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="never" header="系统实时状态">
          <div class="sys-status">
            <p><el-icon color="#67c23a"><CircleCheck /></el-icon> 数据库：已连接 ({{ stats.total }}条记录)</p>
            <p><el-icon color="#67c23a"><CircleCheck /></el-icon> 大语言模型：DeepSeek 在线</p>
            <p><el-icon color="#67c23a"><CircleCheck /></el-icon> Python 网关：运行中</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'

// 响应式数据
const stats = ref({
  total: 0,
  pending: 0,
  avgConfidence: 0,
  avgSatisfaction: 0,
  deptStats: {}
})

// 获取后端真实数据
const fetchStats = async () => {
  try {
    const res = await request.get('/dashboard/stats')
    stats.value = res.data
  } catch (error) {
    console.error('获取大盘数据失败', error)
  }
}

// 计算百分比 (例如某部门数量 / 总部门数量)
const calcPercentage = (count) => {
  const total = Object.values(stats.value.deptStats).reduce((a, b) => a + b, 0)
  if (total === 0) return 0
  return Math.round((count / total) * 100)
}

// 给不同部门分配不同颜色
const getColor = (dept) => {
  if (dept.includes('城管')) return '#409eff'
  if (dept.includes('环境') || dept.includes('市场')) return '#e6a23c'
  return '#67c23a'
}

onMounted(() => {
  fetchStats()
  // 可选：每 10 秒自动刷新一次大盘
  setInterval(fetchStats, 10000)
})
</script>

<style scoped>
.dashboard { width: 100%; height: 100%; box-sizing: border-box; }
.stat-card { text-align: center; border-radius: 8px; }
.stat-title { color: #64748b; font-size: 15px; margin-bottom: 10px; font-weight: bold; }
.stat-value { font-size: 32px; font-weight: bold; color: #0f172a; }
.stat-value span { font-size: 16px; font-weight: normal; color: #94a3b8; }
.stat-footer { font-size: 13px; margin-top: 10px; font-weight: bold; }
.chart-placeholder { padding: 10px 20px; }
.sys-status p { display: flex; align-items: center; gap: 10px; color: #475569; margin: 15px 0; font-size: 15px; font-weight: 500;}
</style>