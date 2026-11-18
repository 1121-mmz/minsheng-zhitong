<template>
  <div class="user-page">
    <el-card shadow="never" class="box-card">
      
      <el-tabs v-model="activeTab" class="demo-tabs">
        
        <!-- 1. 管理员列表 Tab -->
        <el-tab-pane label="👨‍💼 管理员列表" name="ADMIN">
          <div class="tab-header">
            <span class="tab-title">系统管理员 (具备后台管理权限)</span>
            <!-- 👇 只有 admin 才能看到新增管理员按钮 -->
            <el-button type="primary" v-if="currentUsername === 'admin'" @click="openDialog('ADMIN')">
              新增普通管理员
            </el-button>
          </div>
          <el-table :data="filteredAdminData" style="width: 100%" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="登录账号">
              <template #default="scope">
                <span style="font-weight: bold; color: #409eff;">{{ scope.row.username }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="role" label="系统角色">
              <template #default="scope">
                <!-- 👇 区分显示超级管理员和普通管理员 -->
                <el-tag v-if="scope.row.role === 'SUPER_ADMIN'" type="danger" effect="dark">超级管理员</el-tag>
                <el-tag v-else type="primary">普通管理员</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="注册时间">
              <template #default="scope">
                {{ scope.row.createTime ? scope.row.createTime.replace('T', ' ') : '' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <!-- 👇 只有 admin 能删别人，且不能删自己 -->
                <el-button 
                  link 
                  type="danger" 
                  size="small" 
                  :disabled="currentUsername !== 'admin' || scope.row.username === 'admin'" 
                  @click="handleDelete(scope.row.id)"
                >
                  删除账号
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 2. 普通市民列表 Tab -->
        <el-tab-pane label="👥 普通市民列表" name="USER">
          <div class="tab-header">
            <span class="tab-title">普通市民账号 (仅可提交诉求与查看记录)</span>
            <el-button type="success" @click="openDialog('USER')">新增市民</el-button>
          </div>
          <el-table :data="filteredUserData" style="width: 100%" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="登录账号">
              <template #default="scope">
                <span style="font-weight: bold; color: #409eff;">{{ scope.row.username }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="role" label="系统角色">
              <template #default>
                <el-tag type="success">普通市民</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="注册时间">
              <template #default="scope">
                {{ scope.row.createTime ? scope.row.createTime.replace('T', ' ') : '' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button link type="danger" size="small" @click="handleDelete(scope.row.id)">
                  删除账号
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
      </el-tabs>
    </el-card>

    <!-- 新增用户弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.role === 'ADMIN' ? '新增普通管理员' : '新增市民'" width="400px">
      <el-form label-position="top">
        <el-form-item label="登录账号">
          <el-input v-model="form.username" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="登录密码">
          <el-input v-model="form.password" placeholder="默认 123456" />
        </el-form-item>
        <el-form-item label="账号角色">
          <el-radio-group v-model="form.role">
            <el-radio value="USER">普通市民</el-radio>
            <el-radio value="ADMIN">普通管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUser">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '../api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

// 👇 获取当前登录的用户名
const currentUsername = localStorage.getItem('username')

const tableData = ref([])
const dialogVisible = ref(false)
const activeTab = ref('ADMIN')

const form = ref({ username: '', password: '123456', role: 'ADMIN' })

// 👇 管理员列表中，把 SUPER_ADMIN 和 ADMIN 都包含进去
const filteredAdminData = computed(() => tableData.value.filter(item => item.role === 'ADMIN' || item.role === 'SUPER_ADMIN'))
const filteredUserData = computed(() => tableData.value.filter(item => item.role === 'USER'))

const fetchUsers = async () => {
  const res = await request.get('/users')
  tableData.value = res.data
}

const openDialog = (defaultRole) => {
  form.value = { username: '', password: '123456', role: defaultRole }
  dialogVisible.value = true
}

const submitUser = async () => {
  if (!form.value.username) return ElMessage.warning('请输入账号')
  try {
    // 👇 发送请求时，带上当前操作人
    await request.post('/users', form.value)
    ElMessage.success('账号创建成功')
    dialogVisible.value = false
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败，账号可能已存在')
  }
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除该账号吗？删除后该用户将无法登录。', '警告', { type: 'warning' }).then(async () => {
    try {
      // 👇 发送请求时，带上当前操作人
      await request.delete(`/users/${id}`)
      ElMessage.success('已删除')
      fetchUsers()
    } catch (e) {
      ElMessage.error(e.response?.data?.message || '删除失败')
    }
  })
}

onMounted(() => { fetchUsers() })
</script>

<style scoped>
.user-page { height: 100%; padding: 20px; box-sizing: border-box; }
.box-card { border-radius: 8px; min-height: 100%; }
.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  margin-top: 10px;
}
.tab-title {
  font-weight: bold;
  color: #64748b;
  font-size: 14px;
}
</style>