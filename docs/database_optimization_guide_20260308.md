# Digital Twin SG 数据库优化指南

## 📅 优化时间
2026-03-08 15:08:45

## 🎯 优化目标
基于性能监控结果，优化172K Agent系统的数据库性能。

## 📊 性能问题识别
根据性能监控报告：
- 大样本查询 (5000行): 6.8秒 (需要优化)
- 条件过滤查询: 0.4秒 (良好)
- 分层抽样查询: 1.8秒 (可优化)

## 🔧 推荐优化措施

### 1. 索引优化
```sql
-- 执行以下索引创建语句
CREATE INDEX IF NOT EXISTS idx_agents_age ON agents(age);
CREATE INDEX IF NOT EXISTS idx_agents_residency ON agents(residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age ON agents(gender, age);
CREATE INDEX IF NOT EXISTS idx_agents_age_group ON agents(age_group);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age_group ON agents(gender, age_group);
CREATE INDEX IF NOT EXISTS idx_agents_planning_area ON agents(planning_area);
CREATE INDEX IF NOT EXISTS idx_agents_housing_type ON agents(housing_type);
CREATE INDEX IF NOT EXISTS idx_agents_age_residency ON agents(age, residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_residency ON agents(gender, residency_status);
```

### 2. 统计信息更新
```sql
ANALYZE agents;
```

### 3. 性能验证
运行性能监控脚本验证优化效果：
```bash
python3 -u scripts/20_performance_monitor.py
```

## 📈 预期效果

| 查询类型 | 优化前 | 优化后 | 提升幅度 |
|---------|--------|--------|----------|
| 大样本查询 | 6.8秒 | 3.5秒 | 50% |
| 条件过滤 | 0.4秒 | 0.2秒 | 50% |
| 分层抽样 | 1.8秒 | 1.2秒 | 33% |

## 🔍 监控指标

1. **查询响应时间**: 使用性能监控脚本
2. **索引使用率**: 检查pg_stat_user_indexes
3. **数据库负载**: 监控CPU和内存使用
4. **查询计划**: 使用EXPLAIN ANALYZE

## 🚀 下一步行动

1. **立即执行**: 在Supabase控制台运行优化SQL
2. **验证效果**: 运行性能监控对比结果
3. **持续监控**: 建立定期性能检查机制
4. **优化调整**: 根据实际使用调整索引策略

## 📞 技术支持
如有问题，请联系技术团队或参考性能监控报告。
