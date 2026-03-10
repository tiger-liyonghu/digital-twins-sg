
-- ============================================
-- Digital Twin SG 数据库优化脚本
-- 生成时间: 2026-03-08 15:08:45
-- 目标: 优化172K Agent系统性能
-- ============================================

-- 1. 创建缺失的索引
CREATE INDEX IF NOT EXISTS idx_agents_age ON agents(age);
CREATE INDEX IF NOT EXISTS idx_agents_residency ON agents(residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age ON agents(gender, age);
CREATE INDEX IF NOT EXISTS idx_agents_age_group ON agents(age_group);
CREATE INDEX IF NOT EXISTS idx_agents_gender_age_group ON agents(gender, age_group);
CREATE INDEX IF NOT EXISTS idx_agents_planning_area ON agents(planning_area);
CREATE INDEX IF NOT EXISTS idx_agents_housing_type ON agents(housing_type);
CREATE INDEX IF NOT EXISTS idx_agents_age_residency ON agents(age, residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_gender_residency ON agents(gender, residency_status);

-- 2. 分析表统计信息
ANALYZE agents;

-- 3. 查询现有索引状态
-- SELECT * FROM pg_indexes WHERE tablename = 'agents';

-- 4. 性能监控查询
-- 检查大样本查询性能
EXPLAIN ANALYZE SELECT * FROM agents LIMIT 5000;

-- 检查条件过滤查询性能  
EXPLAIN ANALYZE SELECT * FROM agents WHERE age BETWEEN 25 AND 45 AND residency_status = 'Citizen' LIMIT 200;

-- 5. 索引使用情况监控
-- SELECT * FROM pg_stat_user_indexes WHERE relname = 'agents';
