<template>
  <div class="app-wrapper">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="logo">
        <el-icon><Connection /></el-icon>
        <span>民声直通</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#0f172a"
        text-color="#94a3b8"
        active-text-color="#38bdf8"
        class="custom-menu"
      >
        <!-- 管理员/超级管理员可见：数据大盘 -->
        <el-menu-item index="/dashboard" v-if="isAdmin">
          <el-icon><DataLine /></el-icon>
          <span>数据大盘</span>
        </el-menu-item>
        
        <!-- 管理员/超级管理员可见：用户管理 -->
        <el-menu-item index="/user-manage" v-if="isAdmin">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        
        <!-- 管理员/超级管理员可见：工单中心 (带角标) -->
        <el-menu-item index="/orders" v-if="isAdmin">
          <el-icon><Tickets /></el-icon>
          <span>工单流转中心</span>
          <span v-if="pendingCount > 0" class="custom-badge">{{ pendingCount }}</span>
        </el-menu-item>

        <!-- 👇 以下是市民专属菜单，管理员不可见 -->
        <el-menu-item index="/my-orders" v-if="role === 'USER'">
          <el-icon><Tickets /></el-icon>
          <span>我的诉求</span>
        </el-menu-item>
        
        <el-menu-item index="/triage" v-if="role === 'USER'">
          <el-icon><ChatDotRound /></el-icon>
          <span>提交诉求</span>
        </el-menu-item>
        
      </el-menu>
    </div>

    <!-- 右侧主体内容 -->
    <div class="main-content">
      <div class="top-header">
        <div class="breadcrumb">当前位置：{{ route.meta.title }}</div>
        
        <el-dropdown>
          <div class="user-info" style="cursor: pointer; outline: none;">
            <!-- 👇 头像动态显示：超管显示超，普通管理员显示管，市民显示市 -->
            <el-avatar :size="30" style="background:#38bdf8; font-size: 14px;">
              {{ role === 'SUPER_ADMIN' ? '超' : (role === 'ADMIN' ? '管' : '市') }}
            </el-avatar>
            <span>{{ username }}</span>
            <el-icon style="margin-left: 5px; font-size: 12px;"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <!-- 路由出口 -->
      <div class="page-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, User } from '@element-plus/icons-vue'
import request from '../api/request'

const route = useRoute()
const router = useRouter()

const username = ref(localStorage.getItem('username') || '未知用户')
const role = ref(localStorage.getItem('role') || 'USER')

// 👇 核心：统一判断管理员身份
const isAdmin = computed(() => role.value === 'ADMIN' || role.value === 'SUPER_ADMIN')

// 待派单的角标数量
const pendingCount = ref(0)
let timer = null

const fetchPendingCount = async () => {
  if (!isAdmin.value) return
  try {
    const res = await request.get('/orders')
    const pendingList = res.data.filter(item => item.status === '待派单')
    pendingCount.value = pendingList.length
  } catch (error) {
    console.error('获取角标数据失败', error)
  }
}

onMounted(() => {
  fetchPendingCount()
  timer = setInterval(() => {
    fetchPendingCount()
  }, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  ElMessage.success('已安全退出')
  router.push('/login')
}
</script>

<style scoped>
.app-wrapper { display: flex; width: 100vw; height: 100vh; background: #f1f5f9; overflow: hidden; }
.sidebar { width: 220px; background: #0f172a; display: flex; flex-direction: column; flex-shrink: 0; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold; letter-spacing: 2px; border-bottom: 1px solid #1e293b; }
.logo .el-icon { margin-right: 8px; color: #38bdf8; font-size: 24px; }
.custom-menu { border-right: none; flex: 1; }
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.top-header { height: 60px; background: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); z-index: 10; flex-shrink: 0; }
.breadcrumb { color: #64748b; font-weight: 500; }
.user-info { display: flex; align-items: center; gap: 10px; color: #334155; font-size: 14px; }
.page-content { flex: 1; padding: 20px; overflow-y: auto; overflow-x: hidden; box-sizing: border-box; width: 100%; }

/* 👇 完美对齐的自定义红点 */
.custom-badge {
  background-color: #f56c6c;
  color: #fff;
  font-size: 12px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
  border-radius: 9px;
  margin-left: auto; 
  margin-right: 15px; 
  box-sizing: border-box;
  font-weight: bold;
  display: inline-block;
  text-align: center;
  min-width: 18px;
}
</style>