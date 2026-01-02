/**
 * Vue Router 路由配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 布局组件
import AppLayout from '@/components/common/AppLayout.vue'

// 页面组件
const Dashboard = () => import('@/views/Dashboard.vue')
const StockData = () => import('@/views/StockData.vue')
const StockKline = () => import('@/views/StockKline.vue')
const StrategySelect = () => import('@/views/StrategySelect.vue')
const StrategyConfig = () => import('@/views/StrategyConfig.vue')
const StrategyWizard = () => import('@/views/StrategyWizard.vue')
const Settings = () => import('@/views/Settings.vue')

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: AppLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘' },
      },
      {
        path: 'stocks',
        name: 'StockData',
        component: StockData,
        meta: { title: '数据管理' },
      },
      {
        path: 'stocks/:tsCode/kline',
        name: 'StockKline',
        component: StockKline,
        meta: { title: 'K线图表' },
      },
      {
        path: 'strategies',
        name: 'StrategySelect',
        component: StrategySelect,
        meta: { title: '选股策略' },
      },
      {
        path: 'strategies/wizard',
        name: 'StrategyWizard',
        component: StrategyWizard,
        meta: { title: '策略向导' },
      },
      {
        path: 'config',
        name: 'StrategyConfig',
        component: StrategyConfig,
        meta: { title: '策略配置' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings,
        meta: { title: '系统设置' },
      },
    ],
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 股票选股系统`
  }
  next()
})

export default router
