<template>
  <el-container class="app-layout">
    <!-- 顶部导航栏 -->
    <el-header class="app-header" :class="{ 'scrolled': isScrolled }">
      <div class="header-content">
        <!-- Logo区域 -->
        <div class="logo-section" @click="goHome">
          <div class="logo-icon">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <div class="logo-text">
            <span class="logo-title">股票选股系统</span>
            <span class="logo-subtitle">Stock Trading System</span>
          </div>
        </div>

        <!-- 导航菜单 -->
        <nav class="header-nav">
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            :ellipsis="false"
            @select="handleMenuSelect"
            class="nav-menu"
          >
            <el-menu-item index="/dashboard">
              <el-icon><HomeFilled /></el-icon>
              <span>工作台</span>
            </el-menu-item>
            <el-menu-item index="/stocks">
              <el-icon><Document /></el-icon>
              <span>数据管理</span>
            </el-menu-item>
            <el-sub-menu index="strategies-menu">
              <template #title>
                <el-icon><MagicStick /></el-icon>
                <span>选股策略</span>
              </template>
              <el-menu-item index="/strategies/wizard">
                <el-icon><Guide /></el-icon>
                <span>策略向导</span>
              </el-menu-item>
              <el-menu-item index="/strategies">
                <el-icon><DataLine /></el-icon>
                <span>选股列表</span>
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/config">
              <el-icon><Setting /></el-icon>
              <span>策略配置</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <el-icon><Tools /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-menu>
        </nav>

        <!-- 头部操作区 -->
        <div class="header-actions">
          <el-tooltip content="刷新数据" placement="bottom">
            <el-button :icon="Refresh" circle @click="refreshData" />
          </el-tooltip>
          <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏'" placement="bottom">
            <el-button :icon="isFullscreen ? Crop : FullScreen" circle @click="toggleFullscreen" />
          </el-tooltip>
          <el-dropdown @command="handleUserAction">
            <div class="user-section">
              <el-avatar :size="36" :icon="UserFilled" />
              <span class="user-name">用户</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人信息
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  账号设置
                </el-dropdown-item>
                <el-dropdown-item divided command="about">
                  <el-icon><InfoFilled /></el-icon>
                  关于系统
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <!-- 主要内容区域 -->
    <el-main class="app-main">
      <div class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </el-main>

    <!-- 页脚 -->
    <el-footer class="app-footer" v-if="showFooter">
      <div class="footer-content">
        <div class="footer-info">
          <span>© 2024 股票选股系统 · Stock Trading System</span>
          <span class="separator">|</span>
          <span>个人投研学习平台</span>
        </div>
        <div class="footer-links">
          <el-link href="#" target="_blank">使用文档</el-link>
          <span class="separator">|</span>
          <el-link href="#" target="_blank">API文档</el-link>
          <span class="separator">|</span>
          <el-link href="#" target="_blank">GitHub</el-link>
        </div>
      </div>
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  HomeFilled,
  Document,
  MagicStick,
  Setting,
  Tools,
  Guide,
  DataLine,
  Refresh,
  FullScreen,
  Crop,
  UserFilled,
  User,
  InfoFilled,
  SwitchButton,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// ========== 状态 ==========
const isScrolled = ref(false)
const isFullscreen = ref(false)
const showFooter = ref(true)

// ========== 计算属性 ==========
const activeMenu = computed(() => {
  const path = route.path
  // 处理子菜单激活状态
  if (path.startsWith('/strategies')) {
    return path
  }
  return path
})

// ========== 方法 ==========
const goHome = () => {
  router.push('/dashboard')
}

const handleMenuSelect = (index: string) => {
  router.push(index)
}

const refreshData = () => {
  ElMessage.success('数据刷新成功')
  // 可以触发事件让子组件刷新数据
  window.location.reload()
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const handleUserAction = (command: string) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人信息功能开发中')
      break
    case 'settings':
      ElMessage.info('账号设置功能开发中')
      break
    case 'about':
      ElMessage.info('股票选股系统 v1.0.0')
      break
    case 'logout':
      ElMessage.success('已退出登录')
      router.push('/login')
      break
  }
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 10
}

// ========== 生命周期 ==========
onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;
@use '@/assets/styles/mixins.scss' as *;

.app-layout {
  min-height: 100vh;
  background-color: $bg-base;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: $card-bg;
  box-shadow: $shadow-2;
  padding: 0;
  height: 64px;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: $z-index-sticky;
  transition: all $transition-base $easing-cubic;
  border-bottom: 1px solid $border-lighter;

  &.scrolled {
    box-shadow: $shadow-3;
  }

  .header-content {
    width: 100%;
    max-width: $container-max-width;
    margin: 0 auto;
    display: flex;
    align-items: center;
    padding: 0 $spacing-5;
  }

  // Logo区域
  .logo-section {
    display: flex;
    align-items: center;
    gap: $spacing-3;
    margin-right: $spacing-8;
    cursor: pointer;
    transition: all $transition-base $easing-cubic;

    &:hover {
      transform: scale(1.02);
    }

    .logo-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #1890ff 0%, #52c41a 100%);
      border-radius: $border-radius-md;
      @include flex-center;
      color: #fff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
    }

    .logo-text {
      display: flex;
      flex-direction: column;
      line-height: 1.2;

      .logo-title {
        font-size: $font-size-lg;
        font-weight: $font-weight-bold;
        background: linear-gradient(135deg, #1890ff 0%, #52c41a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }

      .logo-subtitle {
        font-size: $font-size-xs;
        color: $text-tertiary;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }
    }
  }

  // 导航菜单
  .header-nav {
    flex: 1;

    .nav-menu {
      flex: 1;
      border-bottom: none;
      background: transparent;

      :deep(.el-menu-item),
      :deep(.el-sub-menu__title) {
        height: 64px;
        line-height: 64px;
        padding: 0 $spacing-4;
        border-bottom: 2px solid transparent;
        font-size: $font-size-md;
        font-weight: $font-weight-medium;
        color: $text-secondary;
        transition: all $transition-base $easing-cubic;

        .el-icon {
          font-size: 18px;
          margin-right: $spacing-2;
        }

        &:hover {
          background-color: transparent;
          color: $primary-color;
        }
      }

      :deep(.el-menu-item.is-active) {
        background-color: transparent;
        color: $primary-color;
        border-bottom-color: $primary-color;

        &::after {
          display: none;
        }
      }

      :deep(.el-sub-menu) {
        .el-sub-menu__title {
          &:hover {
            background-color: transparent;
            color: $primary-color;
          }
        }

        &.is-active {
          .el-sub-menu__title {
            border-bottom-color: $primary-color;
            color: $primary-color;
          }
        }
      }
    }
  }

  // 头部操作区
  .header-actions {
    display: flex;
    align-items: center;
    gap: $spacing-3;

    :deep(.el-button) {
      border: 1px solid $border-light;
      background: $bg-base;
      color: $text-secondary;
      transition: all $transition-base $easing-cubic;

      &:hover {
        border-color: $primary-color;
        color: $primary-color;
        background: $primary-light;
        transform: translateY(-1px);
      }

      &.is-active {
        background: $primary-light;
        border-color: $primary-color;
        color: $primary-color;
      }
    }

    .user-section {
      display: flex;
      align-items: center;
      gap: $spacing-3;
      padding: $spacing-2 $spacing-3;
      border-radius: $border-radius-full;
      cursor: pointer;
      transition: all $transition-base $easing-cubic;

      &:hover {
        background-color: $bg-base;
      }

      .user-name {
        font-size: $font-size-sm;
        font-weight: $font-weight-medium;
        color: $text-primary;
        max-width: 80px;
        @include text-ellipsis;
      }

      :deep(.el-avatar) {
        background: linear-gradient(135deg, #1890ff 0%, #52c41a 100%);
      }
    }
  }
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: $container-max-width;
  width: $container-max-width;
  margin: 0 auto;
  padding: $spacing-5;
  min-height: calc(100vh - 64px - 60px);

  .main-content {
    width: 100%;
  }
}

.app-footer {
  background-color: $card-bg;
  border-top: 1px solid $border-lighter;
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0;

  .footer-content {
    width: 100%;
    max-width: $container-max-width;
    margin: 0 auto;
    padding: 0 $spacing-5;
    @include flex-between;

    .footer-info,
    .footer-links {
      display: flex;
      align-items: center;
      gap: $spacing-3;
      font-size: $font-size-sm;
      color: $text-tertiary;

      .separator {
        color: $border-base;
      }
    }

    .footer-links {
      :deep(.el-link) {
        font-size: $font-size-sm;
        color: $text-tertiary;

        &:hover {
          color: $primary-color;
        }
      }
    }
  }
}

// ========== 页面切换动画 ==========
.page-enter-active,
.page-leave-active {
  transition: all $transition-slow $easing-cubic;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(16px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-16px);
}

// ========== 响应式 ==========
@include respond-below('xl') {
  .app-header {
    .header-content {
      padding: 0 $spacing-4;
    }

    .logo-section {
      margin-right: $spacing-6;

      .logo-text {
        .logo-title {
          font-size: $font-size-md;
        }

        .logo-subtitle {
          display: none;
        }
      }
    }

    .header-nav {
      .nav-menu {
        :deep(.el-menu-item),
        :deep(.el-sub-menu__title) {
          padding: 0 $spacing-3;
          font-size: $font-size-base;

          span {
            display: inline;
          }
        }
      }
    }
  }

  .app-main {
    padding: $spacing-4;
  }
}

@include respond-below('lg') {
  .app-header {
    .header-actions {
      .user-name {
        display: none;
      }
    }
  }
}

@include respond-below('md') {
  .app-header {
    .header-content {
      padding: 0 $spacing-3;
    }

    .logo-section {
      margin-right: $spacing-4;

      .logo-icon {
        width: 40px;
        height: 40px;
      }

      .logo-text {
        .logo-title {
          font-size: $font-size-base;
        }
      }
    }

    .header-nav {
      .nav-menu {
        :deep(.el-menu-item),
        :deep(.el-sub-menu__title) {
          padding: 0 $spacing-2;

          span {
            display: none;
          }

          .el-icon {
            margin-right: 0;
          }
        }
      }
    }

    .header-actions {
      gap: $spacing-2;

      :deep(.el-button) {
        padding: 8px;
      }
    }
  }

  .app-footer {
    .footer-content {
      flex-direction: column;
      gap: $spacing-2;
      padding: $spacing-3;

      .footer-info,
      .footer-links {
        font-size: $font-size-xs;
      }
    }
  }
}

// 小屏幕下隐藏页脚
@include respond-below('sm') {
  .app-footer {
    display: none;
  }
}
</style>
