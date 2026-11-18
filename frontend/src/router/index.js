import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/Layout.vue'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '数据大盘', role: 'ADMIN' }
      },
      {
        path: 'triage',
        name: 'Triage',
        component: () => import('../views/Triage.vue'),
        meta: { title: '智能分诊', role: 'USER' } // 👈 修复：只有市民能进，管理员走后台
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('../views/OrderList.vue'),
        meta: { title: '工单中心', role: 'ADMIN' }
      },
      {
        path: 'order-detail/:id',
        name: 'OrderDetail',
        component: () => import('../views/OrderDetail.vue'),
        meta: { title: '工单处理台', role: 'ADMIN' }
      },
      {
        path: 'my-orders',
        name: 'MyOrders',
        component: () => import('../views/MyOrders.vue'),
        meta: { title: '我的诉求', role: 'USER' }
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: () => import('../views/UserManage.vue'),
        meta: { title: '用户管理', role: 'ADMIN' }
      },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 👇 核心：全局前置路由守卫（权限拦截）
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  
  // 👇 核心修改：把 SUPER_ADMIN 和 ADMIN 统称为管理员
  const isAdmin = role === 'ADMIN' || role === 'SUPER_ADMIN'
  
  // 1. 如果没登录，且去往的不是登录页，强制踢回登录页
  if (to.path !== '/login' && !token) {
    next('/login')
  } 
  // 2. 如果已经登录了，还想去登录页，根据角色送回各自的首页
  else if (to.path === '/login' && token) {
    next(isAdmin ? '/dashboard' : '/triage')
  } 
  // 3. 正常放行，但检查权限
  else {
    // 如果目标页面需要 ADMIN 权限，但当前用户不是管理员
    if (to.meta.role === 'ADMIN' && !isAdmin) {
      ElMessage.error('您没有权限访问该页面！')
      next('/triage')
    } 
    // 如果目标页面需要 USER 权限，但当前用户是管理员（防止管理员乱入市民页面）
    else if (to.meta.role === 'USER' && isAdmin) {
      ElMessage.error('管理员请使用后台管理功能！')
      next('/dashboard')
    } 
    else {
      next()
    }
  }
})

export default router