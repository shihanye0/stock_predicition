/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isGuest = ref(localStorage.getItem('isGuest') === 'true')

  // 计算属性
  const isLoggedIn = computed(() => !!token.value || isGuest.value)
  const username = computed(() => user.value?.username || (isGuest.value ? '游客' : ''))

  // 登录
  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await request.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (response.code === 200) {
      const { access_token, user: userData } = response.data
      token.value = access_token
      user.value = userData
      isGuest.value = false
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.removeItem('isGuest')
    } else {
      throw new Error(response.message || '登录失败')
    }
  }

  // 注册
  async function register(form) {
    const response = await request.post('/auth/register', {
      username: form.username,
      password: form.password,
      email: form.email || null,
      nickname: form.nickname || null
    })
    
    if (response.code !== 200) {
      throw new Error(response.message || '注册失败')
    }
  }

  // 游客登录
  function guestLogin() {
    token.value = ''
    user.value = { username: '游客', role: 'guest' }
    isGuest.value = true
    
    localStorage.removeItem('token')
    localStorage.setItem('user', JSON.stringify(user.value))
    localStorage.setItem('isGuest', 'true')
  }

  // 登出
  function logout() {
    token.value = ''
    user.value = null
    isGuest.value = false
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('isGuest')
  }

  // 获取用户信息
  async function fetchUserInfo() {
    if (!token.value) return
    
    try {
      const response = await request.get('/auth/me')
      if (response.code === 200) {
        user.value = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  return {
    token,
    user,
    isGuest,
    isLoggedIn,
    username,
    login,
    register,
    guestLogin,
    logout,
    fetchUserInfo
  }
})
