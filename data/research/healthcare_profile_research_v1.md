# 新加坡合成人口 Healthcare Domain Layer 深度研究报告

> 研究日期：2026-03-10
> 目标：为 172,173 个合成 Agent 设计 15-20 个医疗健康领域字段，基于新加坡官方数据源

---

## 一、数据源总览

| 数据源 | 简称 | 最新可用 | 覆盖 |
|--------|------|----------|------|
| National Population Health Survey | NPHS 2024 | 2023-2024 | 慢病、吸烟、运动、筛查、BMI、心理健康、疫苗 |
| Singapore Mental Health Study | SMHS 2016 | 2016 | 精神疾病终生患病率 |
| National Youth Mental Health Study | NYMHS 2024 | 2024 | 15-35岁抑郁/焦虑/压力 |
| Household Expenditure Survey | HES 2017/18 | 2017-2018 | 按收入五分位医疗支出 |
| National Adult Oral Health Survey | NAOHS 2019 | 2019 | 牙科就诊频率、口腔健康 |
| MOH Hospital Statistics | MOH Stats | 持续 | 公立/私立医院利用率 |
| data.gov.sg 健康数据集 | data.gov.sg | 至2023 | 慢病患病率时间序列 |
| WHO NCD Country Profile | WHO | 2023 | 高血压国家概况 |
| Healthier SG Enrolment Data | HSG | 2024 | 家庭医生注册率 |
| Duke-NUS 照护者研究 | TraCE | 2019-2020 | 非正式照护者比例 |
| BMC Psychiatry 2022 Web Panel | BMC 2022 | 2022 | 成人抑郁/焦虑症状患病率 |

---

## 二、逐字段研究

### 字段 1: `has_regular_gp` (boolean)
**含义**：是否有固定家庭医生/GP

**数据** [HARD]:
- Healthier SG 启动前，仅 **60%** 新加坡人有固定家庭医生（MOH White Paper on Healthier SG）
- 截至 2024年8月，约 **100万居民**（合格人口的 ~40%）已注册 Healthier SG，绑定固定 GP
- 约 712/1800 家 GP 诊所已加入 Healthier SG

**条件分布建议**：
- 年龄 > 50：更可能有（慢病管理需要）
- 收入越高：越可能有私人 GP
- 年轻人（18-29）：概率最低

**CPT 设计**: P(has_regular_gp | age_group, has_chronic_disease, income_quintile)
- 总体基准: 60%
- 有慢病: ~80%
- 年轻无慢病: ~40%

来源: MOH Healthier SG White Paper, Healthier SG Enrolment Data

---

### 字段 2: `gp_visit_frequency_annual` (int: 0-12+)
**含义**：年度 GP/polyclinic 门诊次数

**数据** [DERIVED]:
- 2023年 polyclinic 总就诊量：**690万次**（26家 polyclinic）
- Polyclinic 占所有初级保健就诊的 **22%**，GP 占 **78%**
- 推算全国初级保健总就诊量：~3,100万次/年，除以约 400万居民 ≈ **人均 7-8 次/年**
- 慢病患者（高血压/糖尿病）需每 3-4 个月复诊 = **3-4 次/年**仅慢病
- 年轻健康人：**1-2 次/年**（感冒等急性病）

**条件分布建议**：
- 有慢病: 4-6 次
- 无慢病年轻人: 1-3 次
- 老年多病: 6-12 次

**CPT 设计**: P(gp_visits | age, has_chronic_disease, health_status)

来源: MOH Primary Care, Healthier SG PMC Study

---

### 字段 3: `preferred_care_type` (enum: polyclinic / GP / TCM)
**含义**：首选初级保健类型

**数据** [HARD]:
- Polyclinic: 占初级保健的 **22%** — 主要服务低收入、慢病、老年人
- GP 私人诊所: **78%** — 有公司医疗福利的上班族首选
- TCM: **39.6%** 人口曾看过中医（NHS 2010）；占 CAM 使用的 **88%**

**条件分布建议**：
- 低收入 + 慢病: polyclinic（政府补贴）
- 有公司保险: GP
- 华人 + 年长: 更可能使用 TCM（作为补充）
- 马来/印度: TCM 使用率低

**CPT 设计**: P(preferred_care | income, ethnicity, has_chronic_disease, employment_type)
- 枚举值分布大致: GP 55%, polyclinic 30%, TCM 15%

来源: MOH Polyclinics, Annals TCM Study

---

### 字段 4: `has_diabetes` (boolean)
**含义**：是否患有糖尿病

**数据** [HARD]:
- 总体患病率: **8.5%**（NPHS 2023-2024），稳定于 2021-2022
- IDF 口径（20-79岁）: **11.4%**
- **按性别**: 男 8.9%, 女 7.6%
- **按族群**: 印度裔 **15.3%**, 马来裔 **11.0%**, 华人 **7.1%**
- **按年龄**: 30-39岁 1.9%, 60-69岁 **21.8%**, 70-74岁 **24.2%**

**CPT 设计**: P(has_diabetes | age_group, ethnicity, gender, bmi_category)

来源: NPHS 2024 MOH, IDF Diabetes Atlas Singapore

---

### 字段 5: `has_hypertension` (boolean)
**含义**：是否患有高血压

**数据** [HARD]:
- 总体患病率: **37.0%**（NPHS 2023-2024），长期上升趋势（2010年仅19.8%）
- **按性别**: 男 33.9%, 女 29.0%
- **按族群**: 马来裔 33.1%, 华人 31.5%, 印度裔 28.5%
- **按年龄**（自报, NPHS 2023）:
  - 18-29: 极低（数据被抑制）
  - 30-39: 2.4%
  - 40-49: 7.7%
  - 50-59: 19.3%
  - 60-69: 38.5%
  - 60+ (实测): **72.8%**

**CPT 设计**: P(has_hypertension | age_group, ethnicity, gender, bmi_category)

来源: PMC Hypertension Multi-ethnic Study, WHO Hypertension Profile Singapore

---

### 字段 6: `has_hyperlipidemia` (boolean)
**含义**：是否患有高血脂

**数据** [HARD]:
- 总体患病率: **30.5%**（NPHS 2023-2024），从 2019-2020 的 39.1% 下降
- 年龄标化后 dyslipidemia 患病率约 **48.1%**，其中 20% 未意识到
- 男性高于女性（更年期前）
- 教育程度低、吸烟、蓝领: 更多未诊断

**条件分布**: 随年龄递增，45岁后急升

**CPT 设计**: P(has_hyperlipidemia | age_group, gender, bmi_category)

来源: Singapore Heart Foundation, Frontiers Cardiovascular Medicine

---

### 字段 7: `bmi_category` (enum: underweight / normal / overweight / obese)
**含义**：BMI 分类（亚洲标准）

**数据** [HARD]:
- 肥胖（BMI≥30）: **12.7%**（NPHS 2023-2024），从 10.5% 上升
- 超重/肥胖高风险（BMI≥27.5）: **22.8%**
- **按性别**: 男 13.1% 肥胖, 女 10.2%
- **按年龄**: 40-49岁最高 15.0%
- **按族群**: 马来裔 **20.7%**, 印度裔 **14.0%**, 华人 **5.9%**（肥胖）

**注**: 新加坡使用亚洲 BMI 标准（overweight ≥23, obese ≥27.5 高风险）

**CPT 设计**: P(bmi_category | age_group, ethnicity, gender, income)

来源: NPHS 2024 MOH, World Obesity Federation

---

### 字段 8: `smoking_status` (enum: current / former / never)
**含义**：吸烟状态

**数据** [HARD]:
- 每日吸烟率: **8.4%**（NPHS 2024），历史新低，从 2019年 10.6% 下降
- **按性别**: 男 **21.8%**, 女 **3.5%**（男：女 ≈ 6:1）
- **按族群**: 马来裔吸烟率是华人/印度裔的 **2倍以上**
  - 马来男性 30-39岁: **49%**
  - 华人男性 30-39岁: **19%**
  - 印度男性 30-39岁: **12%**
- **按年龄**: 18-29岁 ~5.1%, 40-49岁最高 ~11.6%

**CPT 设计**: P(smoking_status | gender, ethnicity, age_group, education)

来源: data.gov.sg Smoking Prevalence, PMC Smoking Study

---

### 字段 9: `exercise_frequency_weekly` (int: 0-7)
**含义**：每周运动频次

**数据** [HARD]:
- 达到充足运动量比例: **84.7%**（NPHS 2024），从 2023 年 78.5% 显著上升
- 通勤贡献最大（51.6%），休闲运动仅 24.7%
- **39.8%** 有规律休闲运动（50岁以上研究）
- **37%** 有高度久坐行为
- 老年人（65+）运动不足的比例更高
- 年轻人（18-29）: 运动达标率最高

**CPT 设计**: P(exercise_freq | age_group, gender, income, occupation)
- 枚举建议: 0次(15%), 1-2次(35%), 3-4次(30%), 5+次(20%)

来源: NPHS 2024 MOH, BMC Physical Activity Study

---

### 字段 10: `screening_compliance` (enum: regular / occasional / never)
**含义**：健康筛查依从性

**数据** [HARD]:
- 慢病筛查参与率: **62.6%**（NPHS 2023），从 60.3% 上升
- 宫颈癌筛查: **45.4%**
- 大肠癌筛查: **41.7%**
- 乳腺癌筛查: **34.7%**（下降）
- Screen for Life 参与者中: 华人 86%, 马来 7%, 印度 4%

**条件分布建议**:
- regular (~40%): 有慢病者、中高收入、女性、年龄40+
- occasional (~35%): 年轻人、偶尔通过公司体检
- never (~25%): 低收入、年轻男性、马来/印度裔

**CPT 设计**: P(screening | age_group, gender, income, ethnicity, has_chronic_disease)

来源: MOH NPHS 2023, MOH Screen for Life

---

### 字段 11: `has_mental_health_condition` (boolean)
**含义**：是否有心理健康问题（自报或确诊）

**数据** [HARD]:
- SMHS 2016 终生患病率: **13.9%**（任一情绪/焦虑/酒精使用障碍）
- SMHS 2016 12个月患病率: **6.5%**
- 2022 Web Panel: 抑郁症状 **14.1%**, 焦虑症状 **15.2%**, 合计 **20.0%**
- NYMHS 2024（15-35岁）: **30.6%** 报告严重/极严重抑郁/焦虑/压力症状
  - 抑郁: 14.9%（20-24岁最高 20.9%）
  - 焦虑: 27.0%（20-24岁最高 34.1%）
  - 女性高于男性（28.9% vs 25.0%）
- NPHS 2024: 18-29岁 **26%** 报告心理健康不佳

**CPT 设计**: P(has_mental_health | age_group, gender, income, marital_status)
- 年轻人（18-29）: ~25%
- 中年（30-49）: ~15%
- 老年（50+）: ~10%

来源: SMHS 2016, BMC Psychiatry 2022, NYMHS 2024

---

### 字段 12: `stress_level` (enum: high / medium / low)
**含义**：压力水平

**数据** [HARD]:
- **68%** 新加坡雇员每周至少经历一次压力（高于亚太平均 61%）
- Gen Z: **35%** 报告"大部分或所有时间有压力"
- 千禧代: **27%** 类似情况
- Gen Z 职业倦怠率: **68%**, 千禧代 **65%**
- 主要压力源: 工作（73%提及）、生活成本（27%）
- 50%+ 的 18-34岁报告频繁或持续压力
- 非正式求助（78.4%）多于正式求助（62.8%）

**CPT 设计**: P(stress_level | age_group, occupation, income, marital_status)

来源: HR Online Mental Health, HRD Asia Stress Survey

---

### 字段 13: `dental_visit_frequency` (enum: regular / problem_only / never)
**含义**：牙科就诊频率

**数据** [HARD]:
- **53.9%** 至少每年看一次牙医（NAOHS 2019）
- **34.4%** 仅在出现问题时才看
- ~12% 从不看牙医（推算）
- 不看牙医原因: 无需要(55.1%), 费用(38.5%), 没时间(15.2%)
- 1-2 房组屋居民: 未治疗龋齿比例更高
- 口腔卫生差: 约 **40-50%** 人口

**条件分布建议**:
- 收入越高: regular 比例越高
- 1-2房组屋: problem_only 比例高
- 年龄越大: 未治疗龋齿越多

**CPT 设计**: P(dental_visit | income, housing_type, age_group)

来源: NAOHS 2019, MOH Dental Care

---

### 字段 14: `preferred_hospital_type` (enum: public / private)
**含义**：偏好的医院类型

**数据** [HARD]:
- 公立医院占 **80%+** 床位
- 私立医院: 等待时间短、隐私好、设施好 — 高收入/外国人首选
- 公立 B2/C 等级病房有收入测试决定补贴比例（20%-75%）
- 有 IP 保险的可选公/私立
- 没有 IP 或低收入: 基本只能选公立

**条件分布建议**:
- 收入 > $6000/月 + 有 IP: ~30% 偏好私立
- 收入 < $3000/月: ~95% 公立
- 总体: 公立 75%, 私立 25%

**CPT 设计**: P(hospital_pref | income, ip_tier, housing_type)

来源: Commonwealth Fund Singapore Profile

---

### 字段 15: `vaccination_attitude` (enum: proactive / neutral / resistant)
**含义**：疫苗接种态度

**数据** [HARD]:
- COVID-19 完整接种率: **~90%**（2023年3月）
- 疫苗犹豫率: **9.9%**（成人接种计划启动6个月后）
- 加强针犹豫: **30.5%**（25.9% 不确定 + 4.7% 拒绝）
- 流感疫苗接种率（18-74岁）: 21.7%→**28.2%**（2023→2024）
- 肺炎球菌疫苗（65+）: 22%→**61%**（2020→2024）
- 60岁以上: ~25% 曾拒绝/未预约 COVID 疫苗

**CPT 设计**: P(vax_attitude | age_group, education, income)
- proactive (~55%): 高教育、有慢病老年人、年轻专业人士
- neutral (~35%): 大部分中间层
- resistant (~10%): 低教育、部分老年人、反疫苗群体

来源: PMC Vaccine Hesitancy Singapore, NPHS 2024 Vaccination

---

### 字段 16: `uses_tcm` (boolean)
**含义**：是否使用中医

**数据** [HARD]:
- NHS 2010: **39.6%** 受访者曾看过中医
- MOH 估计（2001）: **67%** 人口曾咨询中医
- TCM 占 CAM 使用的 **88%**
- 就诊原因: 保健(26%), 扭伤(25.8%), 慢性疼痛(20.6%), 急性小病(17.5%)
- 儿童中药使用: **84.3%**（家长报告）
- 80% 家长同时使用 TCM 和西医

**条件分布建议**:
- 华人: ~45% 曾使用
- 马来/印度: ~15%
- 年龄越大: 越可能使用
- 性别: 女性略高

**CPT 设计**: P(uses_tcm | ethnicity, age_group, gender)

来源: Annals TCM Singapore, Use of TCM in Singapore Children

---

### 字段 17: `annual_oop_healthcare` (int: SGD)
**含义**：年度自付医疗支出

**数据** [DERIVED]:
- HES 2017/18: 家庭月均医疗支出 **$320**（从2012/13的$260上升）
- 年化: ~**$3,840/户**
- OOP 占总医疗支出: **~31%**（2016，从2009年43%下降）
- MediShield Life 年度免赔额: $1,500-$3,000
- 共保比例: 3%-10%
- 低收入底部20%: 医疗支出占比更高

**条件分布建议**（个人年度OOP）:
- 健康年轻人: $200-800
- 有慢病中年: $1,000-3,000
- 老年多病: $2,000-5,000+
- 住院事件: 单次可达 $5,000-20,000+

**CPT 设计**: P(oop_range | age, has_chronic_disease, income, hospital_pref)

来源: MOH Healthcare Expenditure, SingStat HES 2017/18

---

### 字段 18: `is_caregiver` (boolean)
**含义**：是否为家庭照护者（照顾老年/残疾家人）

**数据** [HARD]:
- **6-8%** 新加坡居民（18-69岁）提供定期非正式照护（NHSS 2010/2013）
- 2010年: **8.1%** 居民为照护者
- **60%** 照护者为女性（MSF）
- 35% 为未婚中年女性
- 照护者平均收入损失: **63%**
- ~12,500人因照护辞职（多为40岁以上已婚女性）

**条件分布建议**:
- 女性 40-60岁: ~15%
- 男性 40-60岁: ~5%
- 年轻人: ~3%
- 三代同堂/与老人同住: 概率高

**CPT 设计**: P(is_caregiver | gender, age_group, marital_status, housing_type)

来源: MOH Caregiver Data, Duke-NUS TraCE Study

---

### 字段 19: `health_info_source` (enum: doctor / internet / family / tcm)
**含义**：首选健康信息来源

**数据** [ESTIMATED]:
- 97.3% 受访者使用互联网，其中 **87.4%** 曾在线搜索健康信息（区域研究）
- 65.97% 每月搜索一次以上
- 但仅 **26.88%** 会向医生询问网上找到的信息
- 老年人数字素养较低: 部分不使用互联网
- 有慢病者 75.9% 每日使用互联网
- 非正式求助（家人/朋友）: **78.4%** vs 正式求助（医疗专业人员）: **62.8%**

**CPT 设计**: P(info_source | age_group, education, has_chronic_disease)
- 18-39: internet 60%, doctor 20%, family 15%, tcm 5%
- 40-59: internet 40%, doctor 30%, family 20%, tcm 10%
- 60+: doctor 35%, family 30%, internet 20%, tcm 15%

来源: BMC Digital Health Literacy, NPHS Mental Health Help-Seeking

---

## 三、推荐字段汇总表

| # | 字段名 | 类型 | 数据质量 | 主要数据源 |
|---|--------|------|----------|------------|
| 1 | `has_regular_gp` | bool | [HARD] | Healthier SG / MOH |
| 2 | `gp_visit_frequency_annual` | int | [DERIVED] | MOH polyclinic stats |
| 3 | `preferred_care_type` | enum(3) | [HARD] | MOH primary care + TCM surveys |
| 4 | `has_diabetes` | bool | [HARD] | NPHS 2024 |
| 5 | `has_hypertension` | bool | [HARD] | NPHS 2024 |
| 6 | `has_hyperlipidemia` | bool | [HARD] | NPHS 2024 |
| 7 | `bmi_category` | enum(4) | [HARD] | NPHS 2024 |
| 8 | `smoking_status` | enum(3) | [HARD] | NPHS 2024 + data.gov.sg |
| 9 | `exercise_frequency_weekly` | int/enum | [HARD] | NPHS 2024 |
| 10 | `screening_compliance` | enum(3) | [HARD] | NPHS 2023 |
| 11 | `has_mental_health_condition` | bool | [HARD] | SMHS 2016 + NYMHS 2024 |
| 12 | `stress_level` | enum(3) | [HARD] | NPHS 2024 + Deloitte survey |
| 13 | `dental_visit_frequency` | enum(3) | [HARD] | NAOHS 2019 |
| 14 | `preferred_hospital_type` | enum(2) | [DERIVED] | MOH hospital stats |
| 15 | `vaccination_attitude` | enum(3) | [HARD] | NPHS 2024 + PMC studies |
| 16 | `uses_tcm` | bool | [HARD] | NHS 2010 / MOH |
| 17 | `annual_oop_healthcare` | int(SGD) | [DERIVED] | HES 2017/18 + MOH |
| 18 | `is_caregiver` | bool | [HARD] | NHSS 2010/13 + MOH |
| 19 | `health_info_source` | enum(4) | [ESTIMATED] | Digital health literacy studies |

**总计: 19 个字段**

---

## 四、条件依赖关系图

```
age_group ──┬──> has_diabetes
            ├──> has_hypertension     ──┐
            ├──> has_hyperlipidemia     ├──> screening_compliance
            ├──> bmi_category ─────────┘        │
            ├──> smoking_status                  │
            ├──> exercise_frequency              v
            ├──> stress_level ──> has_mental_health_condition
            └──> is_caregiver

ethnicity ──┬──> has_diabetes
            ├──> bmi_category
            ├──> smoking_status
            ├──> uses_tcm
            └──> preferred_care_type

income ─────┬──> preferred_care_type
            ├──> preferred_hospital_type
            ├──> dental_visit_frequency
            ├──> annual_oop_healthcare
            └──> screening_compliance

gender ─────┬──> smoking_status
            ├──> has_mental_health_condition
            └──> is_caregiver

has_chronic* ─┬──> has_regular_gp
              ├──> gp_visit_frequency
              ├──> screening_compliance
              └──> annual_oop_healthcare
```

---

## 五、数据缺口分析 (Data Gaps)

| 缺口 | 说明 | 替代方案 |
|------|------|----------|
| **慢病按年龄×族群×性别交叉表** | NPHS 完整交叉表在 PDF 报告中，搜索结果仅返回总体/单维度数据 | 需下载 NPHS 2024 PDF 报告手动提取，或使用 data.gov.sg API |
| **牙科保险覆盖率** | 无官方统计数据，仅知"许多雇主提供"但无百分比 | [GAP] 建议按就业类型估算: 全职白领 ~60%, 蓝领 ~20%, 自雇 ~5% |
| **TCM 最新使用率** | 最新全国数据来自 NHS 2010（39.6%），14年前的数据 | [GAP] 可参考 MOH 2001 的 67%，但可能偏高，建议取 35-45% |
| **HES 按收入五分位医疗支出** | 最新 HES 为 2017/18，6年前数据 | [GAP] 需等 HES 2022/23（如果已发布）或按 CPI 调整 |
| **former_smoker 比例** | NPHS 仅报告 current daily smoker，无 former smoker 数据 | [ESTIMATED] 参考全球文献，估算 former = current × 0.6-0.8 |
| **health_info_source 本地数据** | 大部分数据来自区域或香港研究，非新加坡特定 | [ESTIMATED] 可用 NPHS 心理健康求助偏好数据作为代理 |
| **dental_insurance 持有率** | 无官方统计 | [GAP] 建议不设此字段，用 dental_visit_frequency 替代 |

---

## 六、CPT 构建优先级建议

**P0（数据最硬，优先实现）**:
1. `has_diabetes` — 完整的 age × gender × ethnicity 数据
2. `has_hypertension` — 同上
3. `smoking_status` — 同上，含极详细的族群数据
4. `bmi_category` — 同上

**P1（数据较硬，需少量推导）**:
5. `has_hyperlipidemia` — 有总体和趋势，缺交叉表
6. `screening_compliance` — 有总体率，缺条件分布
7. `has_mental_health_condition` — 多源数据可交叉验证
8. `exercise_frequency_weekly` — 有总体，缺细分
9. `stress_level` — 多源但均为调查数据

**P2（需较多推导/估算）**:
10-19 — 其余字段，部分基于单一数据源或区域数据

---

## 七、与现有 Agent 字段的关联

现有字段 → Healthcare 字段映射:
- `age` → 所有慢病字段的核心条件变量
- `gender` → smoking_status, is_caregiver, has_mental_health
- `ethnicity` → has_diabetes, bmi_category, smoking_status, uses_tcm
- `monthly_income` → preferred_care_type, preferred_hospital_type, dental_visit, oop_healthcare
- `housing_type` → 可作为 income 的代理（1-2房 = 低收入）
- `health_status` → 与 has_diabetes/hypertension/hyperlipidemia 直接关联
- `has_ip` / `ip_tier`（保险层）→ preferred_hospital_type, annual_oop_healthcare

---

## 参考文献

- NPHS 2024 MOH Press Release
- NPHS 2024 Report (HPB)
- NPHS 2023 Report PDF
- data.gov.sg Health Prevalence Dataset
- MOH Prevalence Dataset (1992-2017)
- SMHS 2016 (PMC)
- BMC Psychiatry 2022 Depression/Anxiety Study
- NYMHS 2024 IMH Press Release
- PMC Hypertension Multi-ethnic Study
- WHO Hypertension Profile Singapore 2023
- PMC Smoking Prevalence Study
- data.gov.sg Daily Smoking Prevalence
- NAOHS 2019 (Wiley)
- MOH Healthier SG Enrolment Data
- Healthier SG White Paper
- Healthier SG PMC Study
- MOH Primary Care
- PMC Vaccine Hesitancy Singapore
- IDF Diabetes Atlas Singapore
- Singapore Heart Foundation - Cholesterol
- Frontiers Cardiovascular Medicine Singapore
- World Obesity Federation Singapore
- Commonwealth Fund Singapore Healthcare Profile
- MOH Caregiver Data
- Duke-NUS Caregiver Research Brief
- MOH Screen for Life Programme
- Annals TCM Integration Singapore
- BMC Digital Health Literacy Study
- SingStat HES 2017/18 Report
- MOH Healthcare Expenditure Statistics
