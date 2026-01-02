# 更新日志 (Changelog)

本项目的所有重要更新都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [未发布]

### 新增 (Added)
- 实时市场看板功能，显示指数数据、涨跌停统计
- 定时任务管理功能，支持Cron表达式配置
- 高性能同步模式，支持20并发请求
- GitHub Releases 自动备份功能
- 任务进度面板，实时显示同步进度
- 任务控制功能（暂停/恢复/取消）

### 优化 (Changed)
- **数据同步性能提升9倍**：5000只股票从90分钟缩短至10分钟
- 优化数据库写入，采用批量写入模式（50条/批）
- 改进任务队列，支持后台异步执行
- 统一前后端API文案和标签
- 更新README.md，添加详细功能说明

### 修复 (Fixed)
- 修复市场数据不准确问题（指数数据、涨跌停家数）
- 修复股票K线状态显示错误
- 修复前端控制台警告信息
- 修复TypeScript项目引用配置问题
- 修复has_data字段硬编码问题

---

## [1.0.0] - 2024-12-XX

### 新增 (Added)
- 基础股票数据管理功能
- 5种选股策略（少妇战法、SuperB1、补票战法、填坑战法、上穿60放量）
- K线图表展示
- 策略向导功能
- 策略配置管理
- 选股结果筛选和导出

### 技术栈
- 后端：FastAPI + SQLAlchemy + SQLite + AKShare
- 前端：Vue 3 + TypeScript + Element Plus + ECharts
- 数据同步：AKShare API

---

## 版本说明

### [未发布]
当前开发版本，包含所有最新功能和优化。

### [1.0.0]
初始发布版本，提供基础的股票选股和数据分析功能。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 联系方式

- GitHub: [kevin12369/StockTradebyZ](https://github.com/kevin12369/StockTradebyZ)
- Issue: [提交问题](https://github.com/kevin12369/StockTradebyZ/issues)
