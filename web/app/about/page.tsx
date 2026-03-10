'use client';

import NavBar from '@/components/NavBar';
import { useLocale } from '@/lib/locale-context';

export default function AboutPage() {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <NavBar />

      <div className="max-w-3xl mx-auto px-6 py-12">

        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-3xl font-extrabold mb-3 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
            {zh ? '系统介绍' : 'How It Works'}
          </h1>
          <p className="text-[#94a3b8] text-sm leading-relaxed max-w-xl mx-auto">
            {zh
              ? '17万+ 个数学严谨的 AI 市民孪生智能体，两种使用模式，三种仿真方法。以下是我们如何做到的、为什么可信、以及技术难度在哪里。'
              : '170,000+ mathematically rigorous AI citizen digital twins, two operating modes, three simulation methods. Here\'s how we do it, why it\'s trustworthy, and what makes it hard.'}
          </p>
        </div>

        {/* ─── Section 1: Why Not Just Ask an LLM ─── */}
        <Section
          icon="01"
          title={zh ? '为什么不能直接问大模型？' : 'Why Not Just Ask an LLM?'}
          subtitle={zh ? '通用大模型做社会调研的三大致命问题' : 'Three fatal problems when using general-purpose LLMs for social research'}
        >
          <div className="space-y-4">
            <ProblemSolution
              problem={zh
                ? '问题一：一致性偏差。直接问大模型"新加坡人支持这个政策吗？"，100 次问 100 次都是同一个答案。没有多样性，无法反映真实社会的意见分布。'
                : 'Problem 1: Uniformity bias. Ask a general-purpose LLM "Do Singaporeans support this policy?" 100 times, you get the same answer 100 times. No diversity, no real opinion distribution.'}
              solution={zh
                ? '解决：语言化采样（Verbalized Sampling, VS）。我们不让模型选一个答案，而是输出概率分布（如"支持 60%，反对 30%，中立 10%"），然后按概率随机抽样。同一个画像，每次运行得到不同回答——就像真人一样。多样性提升 1.6-2.1 倍。'
                : 'Solution: Verbalized Sampling (VS). We don\'t ask the model to pick one answer — it outputs a probability distribution (e.g., "support 60%, oppose 30%, neutral 10%"), then we randomly sample. Same persona, different runs produce different answers — like real people. 1.6-2.1x diversity improvement.'}
            />
            <ProblemSolution
              problem={zh
                ? '问题二：社会期望偏差。让大模型角色扮演（"你是一个 25 岁的马来族女性"），模型会给出"政治正确"的答案，系统性高估进步立场。'
                : 'Problem 2: Social desirability bias. Ask the model to role-play ("You are a 25-year-old Malay female"), it gives "politically correct" answers, systematically overestimating progressive positions.'}
              solution={zh
                ? '解决：重构提示词（Reformulated Prompting, RP）。我们不说"你是这个人"，而是"这个人会怎么回答？"——第三人称中性框架。模型变成观察者而非角色扮演者。社会期望偏差降低约 34%。'
                : 'Solution: Reformulated Prompting (RP). Instead of "You are this person," we ask "How would this person answer?" — third-person neutral framing. The model becomes an observer, not a role-player. ~34% reduction in social desirability bias.'}
            />
            <ProblemSolution
              problem={zh
                ? '问题三：有常识，没有人口结构。大模型知道"新加坡华族约占 76%"这类 Wikipedia 级别的聚合统计，但它没有真正的人口结构——不知道联合分布（"55 岁华族男性住 HDB 4-Room 月入 $4,000"这个组合有多常见）、不知道条件概率（P(住 Condo | 月入>$15K) 具体是多少）、也无法保证逐个生成 1,000 人后整体分布匹配人口普查。它有常识，但没有微观数据。'
                : 'Problem 3: Common sense, but no population structure. LLMs know aggregate Wikipedia-level stats ("Singapore is ~76% Chinese"), but they lack true population structure — they don\'t know joint distributions (how common is a "55-year-old Chinese male, HDB 4-Room, $4K income" combination), can\'t give precise conditional probabilities (P(Condo | income>$15K) = ?), and cannot ensure that 1,000 individually-generated personas collectively match Census distributions. They have common sense, but no microdata.'}
              solution={zh
                ? '解决：172,173 个合成智能体，基于人口普查微观数据重建联合概率分布。IPF（迭代比例拟合）在 age × gender × ethnicity × planning area 四维空间上精确匹配 Census 边际分布；贝叶斯网络保证属性间的条件依赖（education → income → housing）；验证门控要求 SRMSE < 0.10，否则合成失败重跑。不是"大致差不多"——是数学保证的人口结构还原。'
                : 'Solution: 172,173 synthetic agents with joint probability distributions reconstructed from Census microdata. IPF (Iterative Proportional Fitting) exactly matches Census marginals across a 4D space (age × gender × ethnicity × planning area); Bayesian Networks enforce conditional dependencies (education → income → housing); validation gates require SRMSE < 0.10 or synthesis is rejected. Not "roughly similar" — mathematically guaranteed population structure.'}
            />
          </div>
          <Ref>{zh
            ? 'VS 方法：Zhang et al. (2025) "Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity," arXiv:2510.01171. RP 方法：Argyle et al. (2023) "Out of One, Many: Using Language Models to Simulate Human Samples," Political Analysis 31(3).'
            : 'VS method: Zhang et al. (2025) "Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity," arXiv:2510.01171. RP method: Argyle et al. (2023) "Out of One, Many: Using Language Models to Simulate Human Samples," Political Analysis 31(3).'}</Ref>
        </Section>

        {/* ─── Section 2: Population ─── */}
        <Section
          icon="02"
          title={zh ? '合成人口：数学上如何保证代表性？' : 'Synthetic Population: How Is Representativeness Guaranteed?'}
          subtitle={zh ? '从人口普查到 172K 个独特的 AI 市民' : 'From Census data to 172K unique AI citizens'}
        >
          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '生成流程（4 步）' : 'Generation Pipeline (4 Steps)'}
          </h4>
          <div className="space-y-1 mb-6">
            {(zh ? [
              { s: '1', t: 'IPF 拟合', d: '用 Deming-Stephan 迭代比例拟合算法，在 4,704 个单元格（21 年龄段 × 2 性别 × 4 种族 × 28 规划区）上拟合人口普查边际分布。数学保证：最小化 KL 散度（Csiszar 1975 I-投影定理）。', color: 'text-blue-400 bg-blue-500/15 border-blue-500/25' },
              { s: '2', t: '贝叶斯网络采样', d: '用有向无环图（DAG）建模属性之间的条件概率：P(收入|教育,年龄) × P(住房|收入) × P(婚姻|年龄,性别)。每张条件概率表来自 GHS 2025 官方数据。属性不是独立生成的——一个 60 岁 HDB 3-Room 居民，更可能是中学学历、月入 $2,000-3,000。', color: 'text-purple-400 bg-purple-500/15 border-purple-500/25' },
              { s: '3', t: '高斯 Copula', d: '连续变量（大五人格、风险偏好、社会信任）通过 Gaussian Copula 生成，保留变量间相关性（如外向性↔开放性正相关 r=0.25，尽责性↔神经质负相关 r=-0.30）。基于 Sklar 定理（1959）。', color: 'text-cyan-400 bg-cyan-500/15 border-cyan-500/25' },
              { s: '4', t: '校准 + k-匿名', d: '贪心交换法校准边际分布至 |P_合成 - P_普查| < 1/N。对所有准标识符组合强制 k≥5 匿名性（Sweeney 2002），防止个体可识别。', color: 'text-green-400 bg-green-500/15 border-green-500/25' },
            ] : [
              { s: '1', t: 'IPF Fitting', d: 'Deming-Stephan Iterative Proportional Fitting on 4,704 cells (21 age bands × 2 genders × 4 ethnicities × 28 planning areas). Mathematical guarantee: minimizes KL divergence (Csiszar 1975 I-projection theorem).', color: 'text-blue-400 bg-blue-500/15 border-blue-500/25' },
              { s: '2', t: 'Bayesian Network Sampling', d: 'DAG models conditional probabilities: P(income|education,age) × P(housing|income) × P(marital|age,gender). Each CPT from GHS 2025 official data. Attributes are NOT independent — a 60-year-old HDB 3-Room resident is more likely to have secondary education and earn $2,000-3,000/month.', color: 'text-purple-400 bg-purple-500/15 border-purple-500/25' },
              { s: '3', t: 'Gaussian Copula', d: 'Continuous variables (Big Five personality, risk appetite, social trust) via Gaussian Copula, preserving inter-variable correlations (e.g., Extraversion↔Openness r=0.25, Conscientiousness↔Neuroticism r=-0.30). Based on Sklar\'s theorem (1959).', color: 'text-cyan-400 bg-cyan-500/15 border-cyan-500/25' },
              { s: '4', t: 'Calibration + k-Anonymity', d: 'Greedy swap calibration ensures |P_synth - P_census| < 1/N for all marginals. k≥5 anonymity enforced for all quasi-identifier combinations (Sweeney 2002).', color: 'text-green-400 bg-green-500/15 border-green-500/25' },
            ]).map((s) => (
              <div key={s.s} className="flex gap-4 items-start py-3">
                <div className={`w-8 h-8 rounded-lg border flex items-center justify-center text-xs font-bold shrink-0 ${s.color}`}>
                  {s.s}
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#e2e8f0]">{s.t}</div>
                  <div className="text-xs text-[#94a3b8] mt-0.5 leading-relaxed">{s.d}</div>
                </div>
              </div>
            ))}
          </div>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '每个 Agent 的属性（39 字段 + NVIDIA 叙事人格）' : 'Each Agent\'s Attributes (39 Fields + NVIDIA Narrative Persona)'}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
            {(zh ? [
              { cat: '人口统计', fields: '年龄 · 性别 · 种族 · 规划区 · 居住身份 · 年龄段', n: 6 },
              { cat: '经济', fields: '月收入 · 收入段 · 教育 · 职业 · 行业 · 雇主类型', n: 6 },
              { cat: '住房', fields: '住房类型（HDB 1-5房/EC/公寓/独栋）· 收入段', n: 2 },
              { cat: '家庭', fields: '婚姻状况 · 家庭ID · 家庭角色', n: 3 },
              { cat: '健康', fields: '健康状态', n: 1 },
              { cat: '人格 & 态度', fields: '大五人格（O/C/E/A/N）· 风险偏好 · 政治倾向 · 社会信任 · 宗教虔诚', n: 9 },
              { cat: '生活状态', fields: '人生阶段 · 存活状态 · 数据来源', n: 3 },
            ] : [
              { cat: 'Demographics', fields: 'Age · Gender · Ethnicity · Planning area · Residency · Age group', n: 6 },
              { cat: 'Economic', fields: 'Monthly income · Income band · Education · Occupation · Industry · Employer type', n: 6 },
              { cat: 'Housing', fields: 'Type (HDB 1-5rm/EC/Condo/Landed) · Income band', n: 2 },
              { cat: 'Family', fields: 'Marital status · Household ID · Household role', n: 3 },
              { cat: 'Health', fields: 'Health status', n: 1 },
              { cat: 'Personality & Attitudes', fields: 'Big Five (O/C/E/A/N) · Risk appetite · Political leaning · Social trust · Religious devotion', n: 9 },
              { cat: 'Life State', fields: 'Life phase · Alive status · Data source', n: 3 },
            ]).map((c) => (
              <div key={c.cat} className="bg-[#111827] border border-[#1e293b] rounded-lg px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-400">{c.cat}</span>
                  <span className="text-[10px] text-[#475569]">{c.n}</span>
                </div>
                <div className="text-[11px] text-[#94a3b8] mt-1">{c.fields}</div>
              </div>
            ))}
          </div>
          <div className="bg-gradient-to-r from-purple-500/5 to-blue-500/5 border border-[#1e293b] rounded-lg px-4 py-3 mb-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-purple-400">{zh ? 'NVIDIA 叙事人格（8 个文本维度）' : 'NVIDIA Narrative Persona (8 text dimensions)'}</span>
              <span className="text-[10px] text-[#475569]">{zh ? '每人约 3,000 字' : '~3,000 chars each'}</span>
            </div>
            <div className="text-[11px] text-[#94a3b8] mt-1">
              {zh
                ? '个人画像 · 职业人格 · 文化背景 · 运动偏好 · 艺术品味 · 旅行风格 · 美食偏好 · 兴趣爱好 — 由 NVIDIA Nemotron 模型基于结构化属性生成，每个 agent 拥有独一无二的叙事身份'
                : 'Persona · Professional · Cultural background · Sports · Arts · Travel · Culinary · Hobbies — generated by NVIDIA Nemotron from structured attributes, each agent has a unique narrative identity'}
            </div>
            <div className="text-[10px] text-[#475569] mt-2 italic">
              {zh
                ? '"Jie 是一个超级有条理的 21 岁年轻人，白天研究社区健康，晚上沉迷 K 歌，收集流浪筷子当纪念品，永远在担心辣油淋得不够完美。"'
                : '"Jie is a hyper-organized 21-year-old who balances relentless study of community health with nightly karaoke marathons, hoards stray chopsticks as quirky souvenirs..."'}
            </div>
          </div>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '验证方法（4 重检验）' : 'Validation (4 Layers of Testing)'}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
            {(zh ? [
              { test: '卡方检验', desc: '每个人口变量的边际分布 vs 普查目标，p > 0.05 通过' },
              { test: 'KL 散度', desc: '衡量合成分布与真实分布的信息损失，D_KL → 0 为最优' },
              { test: 'SRMSE', desc: '标准化均方根误差，< 0.05 优秀 / < 0.10 良好 / < 0.20 可接受' },
              { test: "Cramer's V", desc: '验证变量间关联强度：年龄×教育 > 0.3，种族×规划区弱关联' },
            ] : [
              { test: 'Chi-Square', desc: 'Each variable\'s marginal vs Census target, p > 0.05 to pass' },
              { test: 'KL Divergence', desc: 'Information loss between synthetic and real distributions, D_KL → 0 optimal' },
              { test: 'SRMSE', desc: 'Standardized RMSE: < 0.05 excellent / < 0.10 good / < 0.20 acceptable' },
              { test: "Cramér's V", desc: 'Validates association strength: age×education > 0.3, ethnicity×area weak' },
            ]).map((v) => (
              <div key={v.test} className="bg-[#111827] border border-[#1e293b] rounded-lg px-4 py-3">
                <div className="text-xs font-bold text-purple-400">{v.test}</div>
                <div className="text-[11px] text-[#94a3b8] mt-1">{v.desc}</div>
              </div>
            ))}
          </div>
          <div className="text-[11px] text-[#475569] mt-1">
            {zh
              ? '硬约束：性别/种族/年龄/家庭规模 SRMSE < 0.10，否则合成失败，必须重跑。'
              : 'Hard constraints: Gender/ethnicity/age/household SRMSE < 0.10 or synthesis is rejected.'}
          </div>

          <Callout type="info">
            {zh
              ? '数据来源：Population Trends 2025、GHS 2025、Key Household Income Trends 2025、MOM Labour Force Survey 2025、HDB Key Statistics 2024/25、Population in Brief 2025。所有边际约束来自新加坡政府官方统计，不是 LLM 猜测。'
              : 'Data sources: Population Trends 2025, GHS 2025, Key Household Income Trends 2025, MOM Labour Force Survey 2025, HDB Key Statistics 2024/25, Population in Brief 2025. All marginal constraints from official Singapore government statistics, not LLM guesses.'}
          </Callout>
        </Section>

        {/* ─── Section 3: Mode A - Social Simulation ─── */}
        <Section
          icon="03"
          title={zh ? '模式 A：社会模拟（7 天多轮 ABM）' : 'Mode A: Social Simulation (7-Day Multi-Round ABM)'}
          subtitle={zh ? '基于 Agent-Based Modeling 的多轮意见动力学仿真' : 'Multi-round opinion dynamics simulation based on Agent-Based Modeling'}
        >
          <p className="mb-4">
            {zh
              ? '不是一次性问答，而是模拟真实社会中政策发布后 7 天内的意见演化过程。系统基于 Agent-Based Modeling（ABM）框架，运行 3 轮仿真，每轮注入递增的社会影响因子，捕捉经典社会科学中的信息级联（Bikhchandani et al. 1992）、群体极化（Sunstein 2002）和回音室效应（Jamieson & Cappella 2008）。'
              : 'Not a one-shot Q&A, but a simulation of opinion evolution over 7 days after a policy announcement. Built on an Agent-Based Modeling (ABM) framework, the system runs 3 rounds with escalating social influence factors, capturing information cascades (Bikhchandani et al. 1992), group polarization (Sunstein 2002), and echo chamber effects (Jamieson & Cappella 2008).'}
          </p>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '三轮演进模型' : 'Three-Round Evolution Model'}
          </h4>
          <div className="space-y-1 mb-6">
            {(zh ? [
              { s: 'R1', t: 'Day 1 — 冷反应（Information Exposure）', d: '智能体仅接收客观事实（政策内容、政府理由、公众顾虑），无同侪信号。模拟真实世界中"刚看到新闻"的初始态度形成。每个 agent 基于自身人口画像独立输出 5 级 Likert 量表回答（+2 强烈支持 → -2 强烈反对），记录选择和推理链。这一轮建立基线分布。', color: 'text-blue-400 bg-blue-500/15 border-blue-500/25' },
              { s: 'R2', t: 'Day 4 — 同侪影响（Social Influence Injection）', d: '计算 Day 1 各聚类的意见分布，然后注入社会上下文："你的社交圈中，约 X% 支持、Y% 反对。一位 [邻居/同事/亲戚] 说了这句话……"。聚类键为 housing_type × age_tier（如 hdb_mid_senior、private_young），每个聚类独立计算多数意见。模拟的是小世界网络中的局部影响传播（Watts & Strogatz 1998）——人们主要受到社会经济地位相似的人群影响。', color: 'text-purple-400 bg-purple-500/15 border-purple-500/25' },
              { s: 'R3', t: 'Day 7 — 回音室 + 最终决策（Echo Chamber Convergence）', d: '使用 Day 4 更新后的聚类统计，注入更强社会压力："几乎所有你认识的人都支持/反对""社交媒体上 #话题 在 TikTok/Reddit 趋势榜""政府召开发布会重申立场"。对分裂聚类额外注入反面引用，模拟信息交叉暴露。输出最终立场——捕捉 Noelle-Neumann (1974) 沉默螺旋理论中的从众压力效应。', color: 'text-cyan-400 bg-cyan-500/15 border-cyan-500/25' },
            ] : [
              { s: 'R1', t: 'Day 1 — Cold Reaction (Information Exposure)', d: 'Agents receive only objective facts (policy content, government rationale, public concerns) with zero peer signals. Simulates the "just saw the news" initial attitude formation. Each agent independently outputs a 5-point Likert scale response (+2 strongly support → -2 strongly oppose) with reasoning chain. This round establishes the baseline distribution.', color: 'text-blue-400 bg-blue-500/15 border-blue-500/25' },
              { s: 'R2', t: 'Day 4 — Peer Influence (Social Influence Injection)', d: 'Computes Day 1 opinion distribution per cluster, then injects social context: "In your social circle, ~X% support, Y% oppose. A [neighbour/colleague/relative] said this..." Cluster key = housing_type × age_tier (e.g., hdb_mid_senior, private_young), each cluster computes majority opinion independently. Simulates local influence propagation in small-world networks (Watts & Strogatz 1998) — people are primarily influenced by socioeconomically similar peers.', color: 'text-purple-400 bg-purple-500/15 border-purple-500/25' },
              { s: 'R3', t: 'Day 7 — Echo Chamber + Final Decision', d: 'Uses Day 4 updated cluster stats, injects stronger social pressure: "Almost everyone you know supports/opposes this", "Social media trending on TikTok/Reddit", "Government press conference reaffirming position." Split clusters receive counter-quotes for information cross-exposure. Captures conformity pressure from Noelle-Neumann\'s (1974) Spiral of Silence theory.', color: 'text-cyan-400 bg-cyan-500/15 border-cyan-500/25' },
            ]).map((s) => (
              <div key={s.s} className="flex gap-4 items-start py-3">
                <div className={`w-8 h-8 rounded-lg border flex items-center justify-center text-[10px] font-bold shrink-0 ${s.color}`}>
                  {s.s}
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#e2e8f0]">{s.t}</div>
                  <div className="text-xs text-[#94a3b8] mt-0.5 leading-relaxed">{s.d}</div>
                </div>
              </div>
            ))}
          </div>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '意见动力学分析指标' : 'Opinion Dynamics Metrics'}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
            {(zh ? [
              { k: '极化指数 σ', v: '全体意见得分的标准差。Day 1→Day 7 σ 上升 = 群体极化加剧（Sunstein 2002）' },
              { k: '回音室强度', v: '聚类内标准差均值。σ_within 下降 = 同质化加强，回音室形成' },
              { k: '意见迁移率', v: 'Day 1→Day 7 立场改变的 agent 比例。典型值 15-30%，与社会心理学实验一致' },
              { k: '净流向', v: '向支持方向移动 vs 向反对方向移动的 agent 数差值，揭示总体舆论趋势' },
            ] : [
              { k: 'Polarization Index σ', v: 'Standard deviation of all opinion scores. Day 1→Day 7 σ increase = group polarization intensifying (Sunstein 2002)' },
              { k: 'Echo Chamber Strength', v: 'Mean within-cluster σ. Decreasing σ_within = stronger homogenization, echo chamber formation' },
              { k: 'Opinion Migration Rate', v: 'Percentage of agents whose position changed Day 1→Day 7. Typical range 15-30%, consistent with social psychology experiments' },
              { k: 'Net Drift', v: 'Difference between agents moving toward support vs oppose, revealing overall opinion trend' },
            ]).map((m) => (
              <div key={m.k} className="bg-[#111827] border border-[#1e293b] rounded-lg px-4 py-3">
                <div className="text-xs font-bold text-purple-400">{m.k}</div>
                <div className="text-[11px] text-[#94a3b8] mt-1">{m.v}</div>
              </div>
            ))}
          </div>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '底层技术栈' : 'Underlying Technical Stack'}
          </h4>
          <div className="space-y-3 mb-6">
            {(zh ? [
              { s: '1', t: 'Verbalized Sampling (VS)', d: 'LLM 不选一个答案，而是输出概率分布 P(choice|persona, context)，然后蒙特卡洛采样。消除模式坍缩（Zhang et al. 2025, arXiv:2510.01171），多样性提升 1.6-2.1 倍。同一画像、不同 run 得到不同回答——像真人一样。' },
              { s: '2', t: 'Reformulated Prompting (RP)', d: '第三人称中性框架："这个人会怎么回答？"而非"你是这个人"。模型变成观察者而非角色扮演者，社会期望偏差降低约 34%（Argyle et al. 2023, Political Analysis）。' },
              { s: '3', t: '人口聚类（Demographic Clustering）', d: '按 housing_type × age_tier 构建 12 个社会经济聚类（hdb_small/mid/large × young/mid/senior + private × 3）。每个聚类独立计算意见分布，作为下一轮的社会信号源。基于社会同质性原理（McPherson et al. 2001, "Birds of a Feather"）。' },
              { s: '4', t: '分层抽样（Stratified Sampling）', d: '从 172K 中按 Neyman 分配在 age × gender 10 层中按比例抽样。保证样本人口结构匹配全国分布，可按种族/收入/住房/教育等 8 维度筛选目标受众。' },
              { s: '5', t: '并发仿真引擎', d: '20 路 asyncio 并发调用 DeepSeek LLM。每轮 N 个 agent，3 轮 = 3N 次 LLM 调用。指数退避重试（最多 5 次）。200 人样本约 15 分钟完成全部 3 轮（600 次 LLM 调用）。' },
              { s: '6', t: 'NVIDIA Nemotron-70B 质量评分', d: '每个回答独立发送给 Reward Model 评分。> -5 高质量，-5~-15 可接受，< -15 标记低质量。非阻塞管线——评分失败不中断仿真。用于过滤幻觉回答和质量异常。' },
              { s: '7', t: '交叉分析 + 意见轨迹追踪', d: '按年龄/收入/种族/住房交叉分析。独特功能：追踪每个 agent 的 3 轮意见轨迹（如 +1→+2→+2 "坚定支持" 或 0→-1→-2 "被说服反对"），输出"意见旅程"叙事。' },
            ] : [
              { s: '1', t: 'Verbalized Sampling (VS)', d: 'LLM outputs probability distribution P(choice|persona, context) instead of picking one answer, then Monte Carlo samples. Eliminates mode collapse (Zhang et al. 2025, arXiv:2510.01171), 1.6-2.1x diversity improvement. Same persona, different runs produce different answers — like real people.' },
              { s: '2', t: 'Reformulated Prompting (RP)', d: 'Third-person neutral framing: "How would this person answer?" not "You are this person." Model becomes observer, not role-player. ~34% reduction in social desirability bias (Argyle et al. 2023, Political Analysis).' },
              { s: '3', t: 'Demographic Clustering', d: '12 socioeconomic clusters built on housing_type × age_tier (hdb_small/mid/large × young/mid/senior + private × 3). Each cluster independently computes opinion distribution as social signal for the next round. Based on homophily principle (McPherson et al. 2001, "Birds of a Feather").' },
              { s: '4', t: 'Stratified Sampling', d: 'Neyman allocation across 10 strata (age × gender) from 172K population. Guarantees sample demographic structure matches national distribution. Supports 8-dimension audience filtering by ethnicity/income/housing/education.' },
              { s: '5', t: 'Concurrent Simulation Engine', d: '20-way asyncio concurrent DeepSeek LLM calls. N agents per round, 3 rounds = 3N total LLM calls. Exponential backoff retry (up to 5x). 200-agent sample completes all 3 rounds (~600 LLM calls) in ~15 minutes.' },
              { s: '6', t: 'NVIDIA Nemotron-70B Quality Scoring', d: 'Each response independently scored by Reward Model. >-5 high quality, -5 to -15 acceptable, <-15 flagged. Non-blocking pipeline — scoring failures don\'t halt simulation. Filters hallucinated responses and quality anomalies.' },
              { s: '7', t: 'Cross-tabulation + Opinion Trajectory Tracking', d: 'Breakdown by age/income/ethnicity/housing. Unique feature: tracks each agent\'s 3-round opinion trajectory (e.g., +1→+2→+2 "committed supporter" or 0→-1→-2 "persuaded to oppose"), outputting "opinion journey" narratives.' },
            ]).map((s) => (
              <PipelineStep key={s.s} step={s.s} title={s.t} desc={s.d} />
            ))}
          </div>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? 'A/B 因果推断' : 'A/B Causal Inference'}
          </h4>
          <p>
            {zh
              ? '同一批 agent，两个不同政策方案（Context A vs Context B），各跑完整 7 天 3 轮。双比例 z 检验计算统计显著性（p < 0.05），输出效应量（百分点差异）。因为控制了人口结构变量（同一批 agent），只改变政策变量——满足 Rubin (1974) 因果推断框架中的反事实条件：同一"个体"在两个处理条件下的结果差异。'
              : 'Same agents, two different policy variants (Context A vs B), each running the full 7-day 3-round cycle. Two-proportion z-test for statistical significance (p < 0.05), outputs effect size in percentage points. Since population structure is controlled (same agents), only the policy variable changes — satisfying the counterfactual condition in Rubin\'s (1974) causal inference framework: same "individual" under two treatment conditions.'}
          </p>

          <Ref>{zh
            ? '学术参考：Bikhchandani et al. (1992) "A Theory of Fads, Fashion, Custom, and Cultural Change as Informational Cascades," JPE; Sunstein (2002) "The Law of Group Polarization," JPP; Watts & Strogatz (1998) "Collective dynamics of small-world networks," Nature; Noelle-Neumann (1974) "The Spiral of Silence," J. Communication; McPherson et al. (2001) "Birds of a Feather: Homophily in Social Networks," Ann. Rev. Sociology; Rubin (1974) "Estimating Causal Effects of Treatments," JASA.'
            : 'References: Bikhchandani et al. (1992) "Informational Cascades," JPE; Sunstein (2002) "Law of Group Polarization," JPP; Watts & Strogatz (1998) "Small-world networks," Nature; Noelle-Neumann (1974) "Spiral of Silence," J. Communication; McPherson et al. (2001) "Birds of a Feather," Ann. Rev. Sociology; Rubin (1974) "Causal Effects of Treatments," JASA.'}</Ref>

          <Callout type="info">
            {zh
              ? '典型场景：政策预演（CPF 提取年龄调整）、选举预测（GE2025）、社会态度调查（死刑/377A/种族和谐）、危机影响评估（GST 上调对各收入群体的影响）。每次仿真输出完整的 7 天意见演化曲线、聚类极化分析、和个体意见轨迹。'
              : 'Typical use: Policy rehearsal (CPF withdrawal age), election forecasting (GE2025), social attitudes (death penalty/377A/racial harmony), crisis impact (GST increase). Each simulation outputs a complete 7-day opinion evolution curve, cluster polarization analysis, and individual opinion trajectories.'}
          </Callout>
        </Section>

        {/* ─── Section 4: Mode B - Research ─── */}
        <Section
          icon="04"
          title={zh ? '模式 B：调研模式' : 'Mode B: Research Mode'}
          subtitle={zh ? '本体驱动的 AI 市场调研引擎 — 从需求对话到统计推断的全自动化流程' : 'Ontology-driven AI survey engine — fully automated pipeline from conversational intake to statistical inference'}
        >
          <p className="mb-4">
            {zh
              ? 'Sophie 是一个本体驱动（Ontology-driven）的 AI 调研引擎，而非简单的对话机器人。底层由 6 张知识图谱表（行业本体、话题图谱、情境事实库、受众预设、探测模板、问卷模式库）支撑，通过 RAG（Retrieval-Augmented Generation）管线将领域知识注入每一轮对话，确保问卷设计的专业性与一致性。'
              : 'Sophie is an ontology-driven AI research engine, not a simple chatbot. It is backed by 6 knowledge graph tables (industry ontology, topic graph, contextual fact store, audience presets, probe templates, survey pattern library) feeding a RAG (Retrieval-Augmented Generation) pipeline that injects domain knowledge into every conversation turn, ensuring professional rigor and consistency in survey design.'}
          </p>

          {/* 6-Stage Pipeline */}
          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '六阶段研究流程' : 'Six-Stage Research Pipeline'}
          </h4>
          <div className="space-y-3 mb-6">
            {(zh ? [
              { s: '1', t: '本体引导探索', d: '基于 6 大行业（政府/金融/医疗/零售/地产/通用）× 51 个预定义话题的知识图谱，Sophie 通过多阶段探测模板（probe templates）引导用户锁定研究方向。每个话题关联 35+ 条情境事实（context facts），自动注入 LLM prompt，提供新加坡本地化的领域上下文。' },
              { s: '2', t: '智能问卷生成', d: '基于 5 种调查模式库（Likert 量表、多选、排序、开放题、联合分析），Sophie 自动生成结构化问卷。支持上传已有问卷（PDF/Word/文本），通过 LLM 解析抽取问题、选项与目标受众。所有问题通过 VS（Verbalized Sampling）格式化——要求模型输出概率分布而非单一答案。' },
              { s: '3', t: '多维受众配置', d: '8 维人口统计学筛选器（年龄、性别、住房类型、收入、种族、教育、婚姻状况、人生阶段），直接映射 172K agent 数据库的分层抽样框架。系统提供 10 组预设受众配置，覆盖常见细分场景。SQL 级实时计数确保样本代表性。' },
              { s: '4', t: '试点验证（n=20）', d: '小样本预运行用于验证三个维度：(1) 问题措辞的清晰度——检查理解偏差；(2) 选项覆盖度——检测选项遗漏；(3) 回答质量——通过 NVIDIA Nemotron-70B Reward Model 评分。零成本迭代，修改后即时重跑。' },
              { s: '5', t: '大规模并发仿真', d: '20 路并发 LLM 调用引擎，支持 1,000 / 2,000 / 5,000 / 20,000 样本量。每个 agent 的 prompt 包含完整人口统计画像 + VS 概率输出指令 + RP 第三人称框架。1,000 agent 约 3-5 分钟完成。实时 WebSocket 进度推送。' },
              { s: '6', t: '统计分析与推断', d: '输出层包含：(1) 频率分布与置信区间；(2) 多维交叉表（demographics × responses）；(3) 个体级引用追溯——每条回答可回溯到具体 agent 画像；(4) NVIDIA 质量评分分布；(5) 样本充足性检验。支持一键扩大样本量进行效力分析（power analysis）。' },
            ] : [
              { s: '1', t: 'Ontology-Guided Discovery', d: 'Knowledge graph spanning 6 industries (government/finance/healthcare/retail/real estate/general) × 51 pre-defined topics. Sophie uses multi-stage probe templates to guide users toward research focus. Each topic links to 35+ contextual facts auto-injected into LLM prompts, providing Singapore-localized domain context.' },
              { s: '2', t: 'Intelligent Survey Generation', d: 'Based on 5 survey pattern types (Likert scale, multiple choice, ranking, open-ended, conjoint analysis), Sophie auto-generates structured questionnaires. Supports uploading existing surveys (PDF/Word/text) — LLM extracts questions, options, and target audiences. All questions formatted with VS (Verbalized Sampling) — requiring probability distributions, not single answers.' },
              { s: '3', t: 'Multi-Dimensional Audience Config', d: '8-dimensional demographic filter (age, gender, housing, income, ethnicity, education, marital status, life phase) mapping directly to stratified sampling frames across the 172K agent database. 10 preset audience configurations cover common segmentation scenarios. SQL-level real-time counting ensures sample representativeness.' },
              { s: '4', t: 'Pilot Validation (n=20)', d: 'Small-sample pre-run validates three dimensions: (1) question wording clarity — detecting comprehension drift; (2) option coverage — identifying missing choices; (3) response quality — scored by NVIDIA Nemotron-70B Reward Model. Zero-cost iteration with instant re-runs after modifications.' },
              { s: '5', t: 'Large-Scale Concurrent Simulation', d: '20-way concurrent LLM invocation engine supporting 1,000 / 2,000 / 5,000 / 20,000 sample sizes. Each agent prompt includes full demographic persona + VS probability output instructions + RP third-person framing. ~3-5 minutes for 1,000 agents. Real-time WebSocket progress streaming.' },
              { s: '6', t: 'Statistical Analysis & Inference', d: 'Output layer includes: (1) frequency distributions with confidence intervals; (2) multi-dimensional cross-tabs (demographics × responses); (3) individual-level quote tracing — each response traceable to a specific agent persona; (4) NVIDIA quality score distributions; (5) sample adequacy tests. One-click scale-up for power analysis.' },
            ]).map((s) => (
              <PipelineStep key={s.s} step={s.s} title={s.t} desc={s.d} />
            ))}
          </div>

          {/* Technical Stack */}
          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '核心技术栈' : 'Core Technical Stack'}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
            {(zh ? [
              { t: '本体知识库', d: '6 张 Supabase 表：行业→话题→事实的三层图谱 + 受众预设 + 探测模板 + 调查模式' },
              { t: 'RAG 管线', d: '每轮对话实时检索相关话题事实，注入 system prompt，消除 LLM 幻觉' },
              { t: 'VS+RP 仿真', d: '概率化输出 + 第三人称框架，解决一致性偏差和社会期望偏差' },
              { t: 'NVIDIA 评分', d: 'Nemotron-70B Reward Model 对每条回答评分，自动标记低质量样本' },
              { t: '分层抽样', d: '基于人口统计分层的概率抽样，确保样本对新加坡人口的代表性' },
              { t: '并发引擎', d: '20 路异步 LLM 调用 + WebSocket 实时进度推送' },
            ] : [
              { t: 'Ontology Store', d: '6 Supabase tables: industry→topic→fact three-layer graph + audience presets + probe templates + survey patterns' },
              { t: 'RAG Pipeline', d: 'Real-time retrieval of relevant topic facts per conversation turn, injected into system prompts to eliminate LLM hallucination' },
              { t: 'VS+RP Simulation', d: 'Probabilistic output + third-person framing, solving uniformity bias and social desirability bias' },
              { t: 'NVIDIA Scoring', d: 'Nemotron-70B Reward Model scores each response, auto-flagging low-quality samples' },
              { t: 'Stratified Sampling', d: 'Demographic-stratified probabilistic sampling ensuring representativeness of Singapore population' },
              { t: 'Concurrent Engine', d: '20-way async LLM invocation + WebSocket real-time progress streaming' },
            ]).map((item) => (
              <div key={item.t} className="bg-[#111827] border border-[#1e293b] rounded-lg p-3">
                <div className="text-xs font-bold text-blue-400 mb-1">{item.t}</div>
                <div className="text-[11px] text-[#94a3b8] leading-relaxed">{item.d}</div>
              </div>
            ))}
          </div>

          {/* Conjoint Analysis */}
          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '联合分析 (Conjoint Analysis)' : 'Conjoint Analysis (CBC Method)'}
          </h4>
          <p className="mb-4">
            {zh
              ? '基于选择导向联合分析（Choice-Based Conjoint, CBC）方法论（Green & Srinivasan, 1990）。将产品/方案分解为多个属性维度（价格、功能、品牌等），生成正交属性组合，每个 agent 在多组 profile 对中做偏好选择。通过条件 Logit 模型估计各属性的部分效用值（part-worth utilities），输出：各方案的市场偏好份额、按收入/年龄/住房类型的细分偏好、agent 级别的选择理由追溯。适用于产品概念测试、定价弹性研究和市场份额预测。'
              : 'Based on Choice-Based Conjoint (CBC) methodology (Green & Srinivasan, 1990). Products/plans are decomposed into attribute dimensions (price, features, brand, etc.), generating orthogonal attribute profiles. Each agent makes preference choices across multiple profile pairs. Conditional logit models estimate part-worth utilities per attribute, outputting: market preference shares per profile, breakdowns by income/age/housing segments, and agent-level choice reasoning traces. Applicable to product concept testing, price elasticity studies, and market share forecasting.'}
          </p>

          {/* Academic References */}
          <div className="border-t border-[#1e293b] pt-4 mb-4">
            <h4 className="text-xs font-bold text-[#64748b] mb-2 uppercase tracking-wider">
              {zh ? '方法论参考' : 'Methodological References'}
            </h4>
            <div className="space-y-1 text-[11px] text-[#475569]">
              <p>Green & Srinivasan (1990). Conjoint Analysis in Marketing. <i>Journal of Marketing</i>, 54(4).</p>
              <p>Lewis et al. (2004). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. <i>NeurIPS</i>.</p>
              <p>Haines (2014). <i>Product Management</i>. McGraw-Hill — Stage-gate survey design framework.</p>
              <p>Louviere et al. (2000). <i>Stated Choice Methods</i>. Cambridge University Press — Discrete choice experiments.</p>
              <p>Cochran (1977). <i>Sampling Techniques</i>. Wiley — Stratified random sampling theory.</p>
            </div>
          </div>

          <Callout type="info">
            {zh
              ? '适用场景：政策预研 · 市场调研 · 产品概念测试 · 品牌感知 · 定价策略 · 竞品对比 · 舆情预判 · 选举民调。'
              : 'Applications: Policy pre-research · Market surveys · Product concept testing · Brand perception · Pricing strategy · Competitive analysis · Public opinion forecasting · Election polling.'}
          </Callout>
        </Section>

        {/* ─── Section 5: Quality ─── */}
        <Section
          icon="05"
          title={zh ? '质量保障与 Backtest' : 'Quality Assurance & Backtesting'}
          subtitle={zh ? '用真实历史数据验证系统准确度' : 'Validating accuracy against real historical data'}
        >
          <p className="mb-4">
            {zh
              ? '我们用 7 个已有真实结果的历史事件来检验系统。核心原则：AI 的 context 中绝不包含被验证调查的结果——模型必须独立预测，不能"抄答案"。可以引用其他事件的数据作为参考锚定（如用 GE2020 数据锚定 GE2025 预测），但不可以引用被验证事件的结果。'
              : 'We validate against 7 historical events with known real results. Core principle: AI context NEVER includes the survey results being validated — the model must predict independently. May reference other events\' data as anchoring (e.g., GE2020 data to anchor GE2025 predictions), but never the validated event\'s results.'}
          </p>
          <div className="space-y-2 mb-4">
            {[
              { name: zh ? '2023 总统选举' : '2023 Presidential Election', mae: '2.7pp', verdict: zh ? '优秀' : 'Excellent', color: 'text-green-400' },
              { name: zh ? '2050 净零碳排' : 'Net Zero 2050', mae: '2.9pp', verdict: zh ? '优秀' : 'Excellent', color: 'text-green-400' },
              { name: zh ? 'GST 涨至 9%' : 'GST Increase to 9%', mae: '4.3pp', verdict: zh ? '良好' : 'Good', color: 'text-green-400' },
              { name: zh ? '2025 大选' : '2025 General Election', mae: '6.2pp', verdict: zh ? '合理' : 'Reasonable', color: 'text-yellow-400' },
              { name: zh ? '死刑态度' : 'Death Penalty Attitudes', mae: '7.0pp', verdict: zh ? '合理' : 'Reasonable', color: 'text-yellow-400' },
              { name: zh ? '种族和谐' : 'Racial Harmony', mae: '9.3pp', verdict: zh ? '偏差较大' : 'Notable bias', color: 'text-orange-400' },
              { name: zh ? '377A 废除' : '377A Repeal', mae: '14.4pp', verdict: zh ? '显著偏差' : 'Significant bias', color: 'text-red-400' },
            ].map((bt) => (
              <div key={bt.name} className="flex items-center gap-3 bg-[#111827] border border-[#1e293b] rounded-lg px-4 py-2.5">
                <span className="text-sm font-bold w-16 text-right font-mono">{bt.mae}</span>
                <span className="flex-1 text-sm text-[#e2e8f0]">{bt.name}</span>
                <span className={`text-xs font-semibold ${bt.color}`}>{bt.verdict}</span>
              </div>
            ))}
          </div>
          <div className="text-[11px] text-[#475569] mb-6">
            MAE = Mean Absolute Error{zh ? '（平均绝对误差）' : ''}. {zh ? '越低越好。' : 'Lower is better.'} pp = {zh ? '百分点' : 'percentage points'}.
          </div>

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-3">
            {zh ? '已知偏差（诚实披露）' : 'Known Biases (Honest Disclosure)'}
          </h4>
          <div className="space-y-3">
            <BiasCard
              title={zh ? '社会期望偏差' : 'Social Desirability Bias'}
              desc={zh
                ? 'LLM 训练数据偏向西方进步价值观。敏感议题上系统性高估"进步"立场（377A +21.6pp）。保守共识议题偏差较小。'
                : 'LLM training data skews toward Western progressive values. Systematically overestimates "progressive" positions on sensitive issues (377A +21.6pp).'}
              severity={zh ? '高' : 'High'}
              color="text-red-400"
            />
            <BiasCard
              title={zh ? '负面放大 + 中立压缩' : 'Negativity Amplification + Neutral Compression'}
              desc={zh
                ? '互联网数据过度代表冲突。种族和谐低估正面看法 13.4pp。同时 LLM 倾向"强迫"表态，压缩中立选项（377A 中立：真实 36% vs 模型 17.9%）。'
                : 'Internet data over-represents conflict — underestimates positive racial harmony by 13.4pp. LLM also "forces" agents to take positions, compressing neutral options (377A neutral: real 36% vs model 17.9%).'}
              severity={zh ? '中' : 'Medium'}
              color="text-orange-400"
            />
          </div>
          <Callout type="warning">
            {zh
              ? '系统提供方向性信号，不是精确预测。适合回答"哪些人群更可能反对？""主要顾虑是什么？"——而非"精确支持率是 47.3%"。'
              : 'The system provides directional signals, not precise predictions. Best for "Which groups oppose most?" and "What are the main concerns?" — not "The exact support rate is 47.3%."'}
          </Callout>
        </Section>

        {/* ─── Section 6: Tech Stack ─── */}
        <Section
          icon="06"
          title={zh ? '技术栈' : 'Tech Stack'}
          subtitle={zh ? '支撑系统运行的核心技术' : 'Core technologies powering the system'}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {(zh ? [
              { k: 'AI 对话', v: 'Sophie（DeepSeek LLM 驱动）' },
              { k: '仿真 LLM', v: 'DeepSeek Chat · temp 0.7 · VS+RP' },
              { k: '质量模型', v: 'NVIDIA Nemotron-70B Reward' },
              { k: '人口合成', v: 'IPF + Bayesian Network + Copula' },
              { k: '统计验证', v: '卡方 + KL 散度 + SRMSE + Hellinger' },
              { k: '前端', v: 'Next.js 14 + TypeScript + Tailwind' },
              { k: '仿真引擎', v: 'Python · 20 路并发 · 指数退避重试' },
              { k: '数据库', v: 'Supabase PostgreSQL · 172K agents' },
            ] : [
              { k: 'AI Chat', v: 'Sophie (DeepSeek LLM-powered)' },
              { k: 'Simulation LLM', v: 'DeepSeek Chat · temp 0.7 · VS+RP' },
              { k: 'Quality Model', v: 'NVIDIA Nemotron-70B Reward' },
              { k: 'Population', v: 'IPF + Bayesian Network + Copula' },
              { k: 'Validation', v: 'Chi-sq + KL Div + SRMSE + Hellinger' },
              { k: 'Frontend', v: 'Next.js 14 + TypeScript + Tailwind' },
              { k: 'Simulation', v: 'Python · 20 concurrent · exp backoff' },
              { k: 'Database', v: 'Supabase PostgreSQL · 172K agents' },
            ]).map((t) => (
              <div key={t.k} className="bg-[#111827] border border-[#1e293b] rounded-lg px-3 py-2">
                <span className="text-[#64748b]">{t.k}:</span>{' '}
                <span className="text-[#e2e8f0]">{t.v}</span>
              </div>
            ))}
          </div>
        </Section>

        {/* Footer */}
        <div className="text-center text-xs text-[#475569] mt-16 pb-8 border-t border-[#1e293b] pt-8">
          Digital Twin Studio · Singapore · {zh ? '合成人口仿真平台' : 'Synthetic Population Simulation Platform'}
        </div>
      </div>
    </div>
  );
}

// ─── Reusable Components ────────────────────────────

function Section({ icon, title, subtitle, children }: {
  icon: string; title: string; subtitle: string; children: React.ReactNode;
}) {
  return (
    <section className="mb-14">
      <div className="flex items-center gap-3 mb-1">
        <span className="text-xs font-bold text-blue-500/60 font-mono">{icon}</span>
        <h2 className="text-xl font-extrabold text-[#e2e8f0]">{title}</h2>
      </div>
      <p className="text-xs text-[#64748b] mb-5 ml-9">{subtitle}</p>
      <div className="ml-9 text-sm text-[#cbd5e1] leading-relaxed">
        {children}
      </div>
    </section>
  );
}

function ProblemSolution({ problem, solution }: { problem: string; solution: string }) {
  return (
    <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-5">
      <div className="text-xs text-[#94a3b8] mb-3 leading-relaxed">
        <span className="text-red-400/80 font-semibold">{'\u2717'} </span>
        {problem}
      </div>
      <div className="text-xs text-[#cbd5e1] leading-relaxed">
        <span className="text-green-400/80 font-semibold">{'\u2713'} </span>
        {solution}
      </div>
    </div>
  );
}

function PipelineStep({ step, title, desc }: { step: string; title: string; desc: string }) {
  return (
    <div className="flex gap-3 items-start">
      <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded px-1.5 py-0.5 shrink-0 mt-0.5">{step}</span>
      <div>
        <span className="text-xs font-semibold text-[#e2e8f0]">{title}</span>
        <span className="text-xs text-[#94a3b8]"> — {desc}</span>
      </div>
    </div>
  );
}

function BiasCard({ title, desc, severity, color }: {
  title: string; desc: string; severity: string; color: string;
}) {
  return (
    <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-bold text-[#e2e8f0]">{title}</h4>
        <span className={`text-[10px] font-bold uppercase ${color}`}>{severity}</span>
      </div>
      <p className="text-xs text-[#94a3b8] leading-relaxed">{desc}</p>
    </div>
  );
}

function Ref({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-3 text-[11px] text-[#475569] italic leading-relaxed">
      {children}
    </div>
  );
}

function Callout({ type, children }: { type: 'info' | 'warning'; children: React.ReactNode }) {
  const styles = type === 'warning'
    ? 'border-orange-500/30 bg-orange-500/5'
    : 'border-blue-500/30 bg-blue-500/5';
  return (
    <div className={`mt-5 border rounded-xl px-5 py-4 text-xs text-[#cbd5e1] leading-relaxed ${styles}`}>
      {children}
    </div>
  );
}
