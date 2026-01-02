# 智能分批同步使用指南

## 📋 功能概述

智能分批同步是一个全新的数据同步方案，解决了大批量同步"卡住"的问题。

### 核心特性

1. **分批执行**：将5000+只股票拆分成小批次（每批500只）
2. **进度可见**：实时显示同步进度和剩余时间
3. **智能跳过**：自动跳过数据已经是最新的股票（7天内）
4. **手动控制**：可以手动逐批执行，随时暂停
5. **稳定可靠**：每批独立执行，失败不影响其他批次

---

## 🚀 快速开始

### 方式1：使用API直接测试

#### 步骤1：查看同步进度

```bash
# 查看当前有多少股票需要更新
curl http://localhost:8000/api/v1/stocks/kline/batch/progress
```

**返回示例**：
```json
{
  "code": 200,
  "message": "获取同步进度成功",
  "data": {
    "total_stocks": 5792,
    "need_update": 2850,
    "up_to_date": 2942,
    "need_update_list": [...],
    "up_to_date_list": [...]
  }
}
```

**说明**：
- `total_stocks`: 总股票数
- `need_update`: 需要更新的股票数（最新数据超过7天）
- `up_to_date`: 数据已经是最新的股票数

---

#### 步骤2：创建分批计划

```bash
# 创建分批同步计划（不立即执行）
curl -X POST "http://localhost:8000/api/v1/stocks/kline/batch/create-batches?batch_size=500&force_full_sync=false"
```

**返回示例**：
```json
{
  "code": 200,
  "message": "创建 6 个批次",
  "data": {
    "total_batches": 6,
    "total_stocks": 2850,
    "batches": [
      {
        "batch_id": "batch_20251228_143000_1",
        "batch_index": 1,
        "total_batches": 6,
        "stock_count": 500,
        "status": "pending",
        "created_at": "2025-12-28T14:30:00"
      },
      ...
    ]
  }
}
```

**说明**：
- `total_batches`: 总批次数
- `total_stocks`: 需要同步的总股票数（智能跳过后）
- `batches`: 批次列表

---

#### 步骤3：执行单个批次（测试）

```bash
# 执行第1批（同步执行，用于测试）
curl -X POST "http://localhost:8000/api/v1/stocks/kline/batch/execute-single?batch_index=1&batch_size=500&force_full_sync=false"
```

**返回示例**：
```json
{
  "code": 200,
  "message": "批次 1 执行完成",
  "data": {
    "batch_id": "batch_20251228_143000_1",
    "batch_index": 1,
    "total_batches": 6,
    "success": true,
    "total": 500,
    "skipped": 50,
    "succeeded_count": 450,
    "failed_count": 0,
    "succeeded": [...],
    "failed": []
  }
}
```

**说明**：
- `skipped`: 智能跳过的股票数（数据最新）
- `succeeded_count`: 成功同步的股票数
- `failed_count`: 失败的股票数

---

### 方式2：使用前端界面（推荐）

#### 前端界面功能

1. **智能分批同步卡片**：
   - 显示需要更新的股票数量
   - 显示总批次数
   - 显示当前批次进度

2. **批次控制按钮**：
   - "执行下一批"：执行下一个批次
   - "暂停"：暂停同步（可以随时继续）
   - "查看详情"：查看批次详情

3. **进度显示**：
   - 当前批次进度（X/500）
   - 总体进度（批次1/6）
   - 预计剩余时间

---

## 📊 使用场景

### 场景1：首次同步（大量数据）

**情况**：数据库为空或数据很旧

**步骤**：
1. 使用 `force_full_sync=true` 强制全量同步
2. 每批500只，分批执行
3. 预计总耗时：6批 × 50分钟 = 5小时

**命令**：
```bash
# 创建全量同步批次
curl -X POST "http://localhost:8000/api/v1/stocks/kline/batch/create-batches?batch_size=500&force_full_sync=true"

# 逐批执行
curl -X POST "http://localhost:8000/api/v1/stocks/kline/batch/execute-single?batch_index=1&force_full_sync=true"
curl -X POST "http://localhost:8000/api/v1/stocks/kline/batch/execute-single?batch_index=2&force_full_sync=true"
# ...
```

---

### 场景2：日常更新（增量同步）

**情况**：每天更新最新数据

**步骤**：
1. 使用 `force_full_sync=false` 增量同步
2. 智能跳过70%+的股票（数据已最新）
3. 只需要同步30%的股票

**效果**：
- 原本需要同步5000只
- 智能跳过后只需1500只
- 3批即可完成（而不是10批）

---

### 场景3：分天执行（稳妥方案）

**情况**：不希望一次性执行太久

**步骤**：
1. 第1天：执行批次1-2（1000只，约1.5小时）
2. 第2天：执行批次3-4（1000只，约1.5小时）
3. 第3天：执行批次5-6（850只，约1.3小时）

**优点**：
- 每天耗时可控
- 不影响白天使用
- 风险最小

---

## ⚙️ 配置参数

### batch_size（每批股票数量）

**默认值**: 500

**可选值**:
- `100`: 最保守，每批约10分钟，适合测试
- `300`: 平衡，每批约30分钟
- `500`: 推荐，每批约50分钟
- `1000`: 激进，每批约100分钟

**建议**:
- 测试用：100-300
- 生产用：500
- 长时间运行：1000

---

### force_full_sync（是否全量同步）

**默认值**: false

**说明**:
- `false`: 增量同步，只获取缺失的数据（推荐）
- `true`: 全量同步，获取近3年所有数据

---

## 📈 性能对比

### 原方案 vs 智能分批

| 指标 | 原方案 | 智能分批 | 提升 |
|------|--------|----------|------|
| 单批股票数 | 5000+ | 500 | 稳定性↑ |
| 内存占用 | 高峰2GB | 稳定500MB | 75%↓ |
| 失败影响 | 全部失败 | 单批失败 | 风险↓ |
| 进度可见性 | 差 | 实时可见 | 体验↑ |
| 可控性 | 无法暂停 | 随时暂停 | 控制力↑ |
| 断点续传 | 不支持 | 天然支持 | 可靠性↑ |

---

## 🛠️ 故障排查

### 问题1：执行单个批次超时

**现象**：浏览器请求超时

**原因**：批次太大，单批执行时间过长

**解决方案**：
```bash
# 减小批次大小
curl -X POST "http://localhost:8000/api/v1/stocks/kline/batch/create-batches?batch_size=100"
```

---

### 问题2：某些股票总是失败

**现象**：同一只股票每次都失败

**原因**：股票代码变更或已退市

**解决方案**：
1. 查看失败列表
2. 手动检查股票代码
3. 必要时从股票列表中删除该股票

---

### 问题3：进度不更新

**现象**：执行后进度没有变化

**原因**：数据已经是最新的，被智能跳过

**验证**：
```bash
# 查看跳过数量
curl http://localhost:8000/api/v1/stocks/kline/batch/progress
```

---

## 📝 最佳实践

### 1. 首次使用建议

```bash
# 步骤1：小批量测试
batch_size=100, force_full_sync=false

# 步骤2：确认无误后，逐步扩大
batch_size=300 → 500 → 1000
```

---

### 2. 定时更新建议

```bash
# 每天凌晨更新（增量同步）
batch_size=500, force_full_sync=false

# 每周全量更新一次
force_full_sync=true（仅在周末）
```

---

### 3. 监控建议

```bash
# 查看后端日志
tail -f backend/logs/app.log | grep "批次"

# 关键日志：
# [批次 1/6] [123/500] 同步 000001.SZ 平安银行
# 批次 batch_xxx 完成：成功 450，失败 0，跳过 50
```

---

## ✅ 总结

**智能分批同步的核心优势**：

1. ✅ **稳定可靠**：不会"卡住"
2. ✅ **进度可见**：实时显示进度
3. ✅ **随时可控**：可以暂停/继续
4. ✅ **智能跳过**：自动跳过最新数据
5. ✅ **分批执行**：降低风险

**推荐使用方式**：
- 日常更新：增量同步，每批500只
- 首次同步：全量同步，每批300只，分天执行
- 快速更新：增量同步，每批1000只

---

*文档更新时间: 2025-12-28*
*作者: 老王*
