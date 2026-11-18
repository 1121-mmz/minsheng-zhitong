<template>
  <div class="login-container">
    <div class="login-box">
      <div class="title">
        <el-icon class="logo-icon"><Connection /></el-icon>
        <h2>民声直通 · 智能分诊系统</h2>
        <p>Multi-modal AI Citizen Service Platform</p>
      </div>
      
      <el-form :model="loginForm" class="login-form">
        <el-form-item>
          <!-- 👇 改这里：请输入账号 -->
          <el-input v-model="loginForm.username" placeholder="请输入账号" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <!-- 👇 改这里：请输入密码 -->
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" size="large" show-password @keyup.enter="handleLogin">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button type="primary" size="large" class="login-btn" @click="handleLogin" :loading="loading">
          登 录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Connection, User, Lock } from '@element-plus/icons-vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
// 为了演示方便，这里保留默认值，如果你想清空默认值，改成 { username: '', password: '' } 即可
const loginForm = ref({ username: 'admin', password: '123456' }) 

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  
  loading.value = true
  try {
    const res = await request.post('/auth/login', loginForm.value)
    if (res.data.success) {
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('username', res.data.username)
      localStorage.setItem('role', res.data.role)
      
      ElMessage.success('登录成功！')
      
      // 根据角色跳转
      if (res.data.role === 'ADMIN' || res.data.role === 'SUPER_ADMIN') {
        router.push('/dashboard') // 管理员去大盘
      } else {
        router.push('/triage')    // 普通市民去分诊台
      }
      
    } else {
      ElMessage.error(res.data.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('网络错误，请检查后端是否运行')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
  background-size: cover;
}
.login-box {
  width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
}
.title {
  text-align: center;
  margin-bottom: 30px;
}
.logo-icon {
  font-size: 48px;
  color: #38bdf8;
  margin-bottom: 10px;
}
.title h2 {
  margin: 0;
  color: #0f172a;
  font-size: 22px;
  letter-spacing: 1px;
}
.title p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
}
.login-btn {
  width: 100%;
  margin-top: 10px;
  background: linear-gradient(135deg, #409eff, #79bbff);
  border: none;
  font-weight: bold;
  letter-spacing: 2px;
}
</style>