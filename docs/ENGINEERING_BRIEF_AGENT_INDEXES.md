# Engineering Brief: agents 表性能优化 & 系统架构升级

## 一、问题摘要

agents 表（172,173 条记录）缺少数据库索引，导致：
- 组合过滤查询超时（500 错误，statement timeout）
- `Prefer: count=exact` 在组合过滤时超时
- 所有 simulation 脚本被迫全量拉取 172K 行（3-4 分钟）

## 二、诊断结果

| 查询条件 | 结果 |
|---------|------|
| `select agent_id`（无过滤） | 200 OK, 172,173 条 |
| `gender=eq.M` | 206 OK, 85,182 条 |
| `age_group=eq.25-29` | 206 OK, 12,972 条 |
| `age_group=25-29 & gender=M`（数据） | 200 OK |
| `age_group=25-29 & gender=M` + `count=exact` | **500 超时** |
| `residency_status=eq.Citizen` | **500 超时** |
| `age=gte.21` | **500 超时** |

**结论**：单列简单过滤勉强可用，但 `count=exact` + 组合过滤 = 超时。

## 三、修复方案：数据库索引

在 **Supabase Dashboard → SQL Editor** 中执行：

```sql
-- 1. 核心复合索引（覆盖所有 simulation 的分层抽样查询）
CREATE INDEX IF NOT EXISTS idx_agents_strata
  ON agents (age_group, gender, residency_status);

-- 2. 单列索引（覆盖各种单独过滤 + count 场景）
CREATE INDEX IF NOT EXISTS idx_agents_residency_status ON agents (residency_status);
CREATE INDEX IF NOT EXISTS idx_agents_age ON agents (age);
CREATE INDEX IF NOT EXISTS idx_agents_age_group ON agents (age_group);
CREATE INDEX IF NOT EXISTS idx_agents_gender ON agents (gender);

-- 3. 数值 age 复合索引（覆盖 age 范围 + gender 查询）
CREATE INDEX IF NOT EXISTS idx_agents_age_gender_res
  ON agents (age, gender, residency_status);

-- 4. 验证
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'agents';
```

### 预期效果
- 组合过滤 + count=exact：**<100ms**（从超时变秒回）
- 分层抽样 N=1000：**<5 秒**（从 3-4 分钟变秒级）
- 索引创建：**<30 秒**，不影响读写

### 可选：调整 statement timeout

```sql
-- 查看当前 timeout
SHOW statement_timeout;
-- 建议调整到 15 秒（付费版默认可能是 8s）
ALTER ROLE authenticator SET statement_timeout = '15s';
```

## 四、系统架构升级（已完成）

### 问题
4 个脚本各自重复编写了：Supabase 配置、agent 加载、分层抽样、persona 生成、LLM 调用。
每个实现略有不同，bug 各不相同。新增 case 需要再抄一遍。

### 解决方案：共享 `lib/` 模块

```
lib/
├── __init__.py
├── config.py      # Supabase URL/Key, DeepSeek Key, AGENT_FIELDS
├── sampling.py    # 服务端分层抽样（stratified_sample, simple_sample）
├── persona.py     # agent_to_persona（Reformulated Prompting）
├── llm.py         # ask_agent（VS+RP）, redistribute_non_candidate
└── analysis.py    # compute_distribution, compute_mae, print_breakdown
```

### 两种抽样模式

| 模式 | 函数 | 适用场景 |
|------|------|---------|
| 分层抽样 | `stratified_sample(n, strata, residency)` | 选举回测（Census 比例加权）|
| 简单抽样 | `simple_sample(n, age_min, gender, residency)` | 客户 simulation、政策测试 |

### 预设 Strata

| 名称 | 描述 |
|------|------|
| `CITIZEN_VOTER_STRATA` | 公民 21+ 选民（12 个 age×gender 层）|
| `ADULT_STRATA` | 全部成年居民 18+（12 个 age×gender 层）|

### 使用示例

```python
# 选举回测
from lib.sampling import stratified_sample, CITIZEN_VOTER_STRATA
from lib.persona import agent_to_persona, agent_response_meta
from lib.llm import ask_agent

df, meta = stratified_sample(n=1000, strata=CITIZEN_VOTER_STRATA, residency="Citizen")

for i in range(len(df)):
    agent = df.iloc[i].to_dict()
    persona = agent_to_persona(agent)
    result = ask_agent(persona, question, options, context)
    result.update(agent_response_meta(agent))

# 客户 simulation
from lib.sampling import simple_sample
df = simple_sample(n=200, age_min=25, age_max=45, residency="Citizen")
```

### Fallback 机制

`sampling.py` 内置 fallback：
1. 如果 `residency_status` 过滤导致 500（无索引），自动退回到仅 `age_group + gender` 过滤
2. 在 Python 端过滤 residency
3. 日志打印 WARNING，不中断流程

**建索引后 fallback 不再触发**，查询直接走索引。

## 五、验证测试（已通过）

**无索引状态下测试通过**（fallback 机制工作正常）：

| 测试 | 结果 |
|------|------|
| `stratified_sample(n=50)` 无 residency | 3.3s, 50 agents |
| `stratified_sample(n=50, residency="Citizen")` | 3.8s, 50 agents, 100% Citizen |
| `stratified_sample(n=1000, residency="Citizen")` | 16.9s, 1000 agents, 100% Citizen |
| `simple_sample(n=30, age_min=18)` | 0.4s, 30 agents |

**建索引后预期**：N=1000 从 17s 降至 <5s。

## 六、架构师审查要点

1. **索引策略**：agents 表读多写少（仅 seeding 时写入），索引开销可忽略
2. **statement timeout**：当前默认值过短，建议确认并调整到 15s
3. **age vs age_group**：统一用 `age_group`（离散值，索引更高效），`age` 仅用于精确年龄过滤
4. **Prefer: count=exact 风险**：即使有索引，count 查询在大表上仍可能较慢。`lib/sampling.py` 已移除 count 依赖
5. **分页上限**：付费版确认 Range header 上限（默认 1000？是否已调高？）
6. **RLS**：当前 anon key SELECT 正常，无需调整

## 七、操作步骤

1. 登录 Supabase Dashboard → SQL Editor
2. 执行第三节的 CREATE INDEX 语句
3. 运行验证查询确认索引存在
4. 运行测试：`python3 -u -c "from lib.sampling import stratified_sample; stratified_sample(50)"`
5. 确认组合过滤不再触发 fallback（无 WARNING 日志）
6. 运行 GE2025 backtest：`python3 -u scripts/12_backtest_ge2025.py`
