/**
 * Pinia 状态管理入口
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 应用状态
  const loading = ref(false)
  const collapsed = ref(false)

  // 设置加载状态
  function setLoading(value: boolean) {
    loading.value = value
  }

  // 切换侧边栏
  function toggleCollapsed() {
    collapsed.value = !collapsed.value
  }

  return {
    loading,
    collapsed,
    setLoading,
    toggleCollapsed,
  }
})
