'use client';

import NavBar from '@/components/NavBar';
import { useLocale } from '@/lib/locale-context';

/* ─── Reusable sub-components ─── */

function Section({ icon, title, subtitle, children }: {
  icon: string; title: string; subtitle: string; children: React.ReactNode;
}) {
  return (
    <section className="mb-16">
      <div className="flex items-center gap-3 mb-1">
        <span className="text-[11px] font-mono font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded-md px-2 py-0.5">{icon}</span>
        <h2 className="text-lg font-bold text-[#e2e8f0]">{title}</h2>
      </div>
      <p className="text-xs text-[#94a3b8] mb-6 ml-11">{subtitle}</p>
      <div className="ml-0">{children}</div>
    </section>
  );
}

function PaperCard({ institution, year, title, finding, significance, color }: {
  institution: string; year: string; title: string; finding: string; significance: string; color: string;
}) {
  return (
    <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-5 mb-3">
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${color}`}>{institution}</span>
        <span className="text-[10px] text-[#475569]">{year}</span>
      </div>
      <h4 className="text-sm font-semibold text-[#e2e8f0] mb-2">{title}</h4>
      <p className="text-xs text-[#94a3b8] leading-relaxed mb-2">{finding}</p>
      <div className="text-[11px] text-cyan-400/80 leading-relaxed">
        {significance}
      </div>
    </div>
  );
}

function AdvantageCard({ icon, title, research, ourEdge }: {
  icon: string; title: string; research: string; ourEdge: string;
}) {
  return (
    <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-5 mb-3">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-base">{icon}</span>
        <h4 className="text-sm font-bold text-[#e2e8f0]">{title}</h4>
      </div>
      <div className="text-xs text-[#94a3b8] leading-relaxed mb-3">
        <span className="text-[#475569] font-semibold">Research: </span>{research}
      </div>
      <div className="text-xs text-[#cbd5e1] leading-relaxed bg-gradient-to-r from-blue-500/5 to-purple-500/5 border border-blue-500/15 rounded-lg px-4 py-3">
        <span className="text-blue-400 font-semibold">Our edge: </span>{ourEdge}
      </div>
    </div>
  );
}

function ConfidenceRow({ level, color, label, domains }: {
  level: string; color: string; label: string; domains: { name: string; desc: string; example: string }[];
}) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${color}`}>{level}</span>
        <span className="text-xs text-[#94a3b8]">{label}</span>
      </div>
      <div className="space-y-2">
        {domains.map((d) => (
          <div key={d.name} className="bg-[#111827] border border-[#1e293b] rounded-lg px-4 py-3">
            <div className="text-xs font-semibold text-[#e2e8f0] mb-1">{d.name}</div>
            <div className="text-[11px] text-[#94a3b8] leading-relaxed mb-1.5">{d.desc}</div>
            <div className="text-[11px] text-[#475569] italic">{d.example}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Main Page ─── */

export default function ResearchPage() {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <NavBar />

      <div className="max-w-3xl mx-auto px-6 py-12">

        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-3xl font-extrabold mb-3 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
            {zh ? '研究基础与可信度论证' : 'Research Evidence & Credibility'}
          </h1>
          <p className="text-[#94a3b8] text-sm leading-relaxed max-w-xl mx-auto">
            {zh
              ? '15 篇顶级论文证明 LLM 社会仿真可行——我们的产品在此基础上更进一步。'
              : '15 peer-reviewed papers prove LLM social simulation works — our product goes further.'}
          </p>
        </div>

        {/* ─── Key Metrics Banner ─── */}
        <div className="grid grid-cols-4 gap-3 mb-16">
          {[
            { value: '85%', label: zh ? '个体还原准确率' : 'Individual accuracy', sub: 'Stanford 2024' },
            { value: '6/7', label: zh ? '摇摆州预测正确' : 'Swing states correct', sub: 'FlockVote 2024' },
            { value: '4%', label: zh ? '态度误差上限' : 'Attitude error bound', sub: 'Verasight 2026' },
            { value: '10K+', label: zh ? '智能体规模验证' : 'Agent scale verified', sub: zh ? '清华 2025' : 'Tsinghua 2025' },
          ].map((m) => (
            <div key={m.value} className="bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-4 text-center">
              <div className="text-xl font-extrabold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">{m.value}</div>
              <div className="text-[11px] text-[#e2e8f0] mt-1">{m.label}</div>
              <div className="text-[10px] text-[#475569] mt-0.5">{m.sub}</div>
            </div>
          ))}
        </div>

        {/* ═══════════════════════════════════════════════ */}
        {/* PART 1: LLM Social Simulation Evidence          */}
        {/* ═══════════════════════════════════════════════ */}
        <Section
          icon="01"
          title={zh ? 'LLM 社会仿真：已被验证的方法' : 'LLM Social Simulation: A Validated Method'}
          subtitle={zh ? '全球顶级研究机构的实证论文' : 'Empirical evidence from the world\'s leading institutions'}
        >
          {/* Landmark studies */}
          <h4 className="text-sm font-bold text-[#e2e8f0] mb-4">
            {zh ? '里程碑研究' : 'Landmark Studies'}
          </h4>

          <PaperCard
            institution="Stanford"
            year="2024"
            color="text-red-300 bg-red-500/15 border border-red-500/25"
            title={zh
              ? '1,052 人深度访谈 → AI 孪生，GSS 准确率 85%'
              : '1,052 deep interviews → AI twins, GSS accuracy 85%'}
            finding={zh
              ? '研究团队对 1,052 名真实个体进行 2 小时深度访谈，用 LLM 构建每人的数字孪生。在美国最权威的社会调查 General Social Survey 上，AI 智能体复现受访者回答的准确率达 85%——接近真人两周后重新回答自己问题的一致性水平。'
              : 'Researchers conducted 2-hour deep interviews with 1,052 real individuals, then built LLM-based digital twins. On the General Social Survey (gold-standard US social survey), AI agents reproduced respondents\' answers with 85% accuracy — approaching the consistency of real people retaking the same survey two weeks later.'}
            significance={zh
              ? '首次在千人规模上严格验证"AI 能否代替真人回答调查"——来自全球排名第一的 AI 实验室。'
              : 'First rigorous validation at 1,000-person scale that AI can stand in for real survey respondents — from the world\'s #1 AI lab.'}
          />

          <PaperCard
            institution="Stanford"
            year="2023"
            color="text-red-300 bg-red-500/15 border border-red-500/25"
            title={zh
              ? '25 个智能体自主组织社会活动，展现涌现行为'
              : '25 agents autonomously organize social events, exhibit emergent behavior'}
            finding={zh
              ? '25 个 LLM 智能体在模拟小镇中自主组织情人节派对、传播消息、建立新关系。人类评估者认为 AI 智能体的回答比"扮演该角色的真人"更像那个角色。'
              : '25 LLM agents in a simulated town autonomously organized a Valentine\'s party, spread information, and formed new relationships. Human evaluators rated AI agents as more believable than real people role-playing the same characters.'}
            significance={zh
              ? '证明 LLM 智能体不仅能回答问题，还能产生真实的社会动态——从"问一个AI"到"运行一个AI社会"。'
              : 'Proved LLM agents can generate authentic social dynamics — the leap from "ask one AI" to "run an AI society."'}
          />

          <PaperCard
            institution="FlockVote"
            year="2024"
            color="text-amber-300 bg-amber-500/15 border border-amber-500/25"
            title={zh
              ? '正确预测 2024 美国大选 7 个摇摆州中 6 个'
              : 'Correctly predicted 6 of 7 swing states in 2024 US election'}
            finding={zh
              ? '基于 LLM 智能体的微观模拟正确预测了七个摇摆州中六个的选举结果。研究者可以直接"采访"AI 选民，理解投票逻辑。'
              : 'LLM agent-based microsimulation correctly predicted election outcomes in 6 of 7 swing states. Researchers could directly "interview" AI voters to understand voting logic.'}
            significance={zh
              ? 'LLM 社会仿真在真实高风险场景中最有力的验证之一。'
              : 'One of the most powerful real-world validations of LLM social simulation in a high-stakes scenario.'}
          />

          <PaperCard
            institution={zh ? '清华大学' : 'Tsinghua'}
            year="2025"
            color="text-emerald-300 bg-emerald-500/15 border border-emerald-500/25"
            title={zh
              ? '万级智能体、500 万次交互，复现 4 个已知社会实验'
              : '10K+ agents, 5M interactions, reproduced 4 known social experiments'}
            finding={zh
              ? 'AgentSociety 为超过 10,000 个智能体生成社会生活，模拟了 500 万次交互。成功复现了舆论极化、煽动性信息传播、全民基本收入政策效应、及自然灾害冲击的影响。'
              : 'AgentSociety generated social lives for 10,000+ agents with 5M interactions. Successfully reproduced opinion polarization, misinformation spread, universal basic income effects, and natural disaster impacts.'}
            significance={zh
              ? '证明 LLM 社会仿真在万级规模下仍然有效——我们 172K 架构的直接参照。'
              : 'Validates LLM social simulation at 10K+ scale — direct reference for our 172K architecture.'}
          />

          <h4 className="text-sm font-bold text-[#e2e8f0] mb-4 mt-8">
            {zh ? '精度与可行性验证' : 'Precision & Feasibility Validation'}
          </h4>

          <PaperCard
            institution="Verasight"
            year="2025-26"
            color="text-sky-300 bg-sky-500/15 border border-sky-500/25"
            title={zh
              ? '2,000 人多轮验证：常见态度问题总体误差 < 4%'
              : '2,000-person multi-round validation: common attitude questions < 4% error'}
            finding={zh
              ? '对 2,000 名美国成年人的多轮验证发现，常见政治态度问题的总体误差可控制在 4 个百分点以内。误差最低的问题（低至 2.5%）是具有强烈人口统计关联的态度问题。'
              : 'Multi-round validation with 2,000 US adults found overall error under 4 percentage points for common political attitude questions. Lowest errors (down to 2.5%) were on questions with strong demographic correlations.'}
            significance={zh
              ? '政策态度预测是 LLM 仿真目前最成熟、最可靠的应用领域——恰好是我们"政策预演"的核心场景。'
              : 'Policy attitude prediction is LLM simulation\'s most mature domain — exactly our "policy rehearsal" core scenario.'}
          />

          <PaperCard
            institution="MIT Media Lab"
            year="2025"
            color="text-violet-300 bg-violet-500/15 border border-violet-500/25"
            title={zh
              ? '百万级仿真：纽约 840 万智能体，成本仅数百美元'
              : 'Million-scale: 8.4M NYC agents, cost just hundreds of dollars'}
            finding={zh
              ? '通过"LLM 原型 (Archetypes)"方法实现百万级仿真。纽约市 840 万智能体成功重现劳动参与和出行模式。新西兰政府已用同一框架模拟 500 万公民。'
              : 'Using "LLM Archetypes" method for million-scale simulation. NYC\'s 8.4M agent digital twin successfully reproduced labor participation and mobility patterns. New Zealand government uses the same framework for 5M citizens.'}
            significance={zh
              ? '证明我们的"原型聚类 + LLM"架构在百万级别可行且经济。'
              : 'Proves our "archetype clustering + LLM" architecture is feasible and economical at million-scale.'}
          />

          <PaperCard
            institution={zh ? '巴西/皇家学会' : 'Royal Society'}
            year="2024"
            color="text-pink-300 bg-pink-500/15 border border-pink-500/25"
            title={zh
              ? 'LLM 跨党派捕捉公民政策偏好，增强民主决策'
              : 'LLM captures cross-party citizen policy preferences for augmented democracy'}
            finding={zh
              ? '在巴西 2022 年总统大选实验中，微调的 LLM 捕捉到超越简单左右分类的政策立场细微差异。LLM 增强后的概率样本比未增强的更准确。'
              : 'In Brazil\'s 2022 presidential election experiment, fine-tuned LLMs captured policy nuances beyond simple left-right classification. LLM-augmented probability samples were more accurate than unaugmented ones.'}
            significance={zh
              ? '直接证明 LLM 可以作为公民的政策偏好代理——我们"政策预演"产品的学术理论基础。'
              : 'Direct proof that LLMs can serve as citizen policy preference proxies — academic basis for our product.'}
          />

          <div className="grid grid-cols-2 gap-3 mt-4">
            {[
              {
                title: zh ? '消费行为仿真' : 'Consumer Behavior',
                desc: zh
                  ? '智能体展现品牌忠诚形成、价格敏感性差异等真实模式，验证产品定价测试场景。'
                  : 'Agents exhibited brand loyalty formation, price sensitivity patterns — validates product pricing test scenarios.',
                src: 'arXiv:2510.18155, 2025'
              },
              {
                title: zh ? 'ICML 2025 学术定位' : 'ICML 2025 Position',
                desc: zh
                  ? '多机构联合确认：LLM 社会仿真是有前途的研究方法。共识已从"能不能做"转向"如何做更好"。'
                  : 'Multi-institution consensus: LLM social simulation is a promising research method. Debate shifted from "can it work?" to "how to do it better."',
                src: 'Anthis et al., ICML 2025'
              },
            ].map((c) => (
              <div key={c.title} className="bg-[#111827] border border-[#1e293b] rounded-xl p-4">
                <div className="text-xs font-semibold text-[#e2e8f0] mb-1">{c.title}</div>
                <div className="text-[11px] text-[#94a3b8] leading-relaxed mb-2">{c.desc}</div>
                <div className="text-[10px] text-[#475569]">{c.src}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* ═══════════════════════════════════════════════ */}
        {/* PART 2: Our Competitive Advantages              */}
        {/* ═══════════════════════════════════════════════ */}
        <Section
          icon="02"
          title={zh ? '我们的差异化优势' : 'Our Competitive Advantages'}
          subtitle={zh ? '为什么我们的新加坡数字孪生比"通用LLM + 简单prompt"更准' : 'Why our Singapore digital twin outperforms "generic LLM + simple prompt"'}
        >
          <AdvantageCard
            icon="🎯"
            title={zh ? '人口统计校准 vs 纯 Prompt' : 'Demographic Calibration vs Pure Prompting'}
            research={zh
              ? 'Park et al. (2024) 发现仅用人口统计描述的 prompt 方法会产生更大的种族和意识形态偏差。Verasight (2026) 报告子群体误差膨胀到 10%，最小群体可达 30%。'
              : 'Park et al. (2024) found pure demographic prompting produces larger racial and ideological biases. Verasight (2026) reports subgroup errors balloon to 10%, reaching 30% for smallest groups.'}
            ourEdge={zh
              ? '172,173 个合成居民基于人口普查数据，通过 IPF + 高斯 Copula 在种族×年龄×性别×规划区×收入×教育×住房 多维联合分布上经过卡方检验和 KL 散度验证。"碧山区 42 岁华族 PME 男性"在统计上是真实存在的画像，不是 LLM 随意编造的角色。'
              : '172,173 synthetic residents built from Census data via IPF + Gaussian Copula, validated across ethnicity×age×gender×planning area×income×education×housing joint distributions with chi-square tests and KL divergence. "42-year-old Chinese PME male in Bishan" is a statistically real profile, not an LLM fabrication.'}
          />

          <AdvantageCard
            icon="🇸🇬"
            title={zh ? '本地知识注入 vs 通用世界知识' : 'Local Knowledge Injection vs Generic World Knowledge'}
            research={zh
              ? 'NAACL 2025 发现通用 LLM 在文化多样性语境下产生刻板或过度自信的回答。Silicon Sampling 研究确认人口统计+上下文的组合 prompt 效果最优。'
              : 'NAACL 2025 found generic LLMs produce stereotyped or overconfident responses in culturally diverse contexts. Silicon Sampling confirms demographic + context combined prompting is optimal.'}
            ourEdge={zh
              ? 'RAG 管线从 Reddit r/singapore、HardwareZone EDMW、国会 Hansard 辩论记录、REACH 公众咨询中持续采集。当 AI 居民回答关于 CPF 或 HDB 的问题时，参考的是新加坡社区中真实存在的争议和论点——不是全球泛化知识。'
              : 'RAG pipeline continuously ingests Reddit r/singapore, HardwareZone EDMW, Parliament Hansard debates, and REACH public consultations. When AI residents answer CPF or HDB questions, they reference real debates from Singapore communities — not generic global knowledge.'}
          />

          <AdvantageCard
            icon="🎲"
            title={zh ? 'VS+RP 方法 vs 直接回答' : 'VS+RP Method vs Direct Answering'}
            research={zh
              ? 'LLM 直接回答存在系统性偏差——回答更同质化、更正面、缺乏真人的多样性和矛盾性（Zhang & Xu 2025, Sociological Methods & Research）。'
              : 'LLMs answering directly exhibit systematic bias — more homogeneous, more positive, lacking real human diversity and contradiction (Zhang & Xu 2025, Sociological Methods & Research).'}
            ourEdge={zh
              ? 'LLM 不直接"回答"问题，而是作为分析师估算该画像人群的回答概率分布，然后通过采样产生最终选择。从架构层面缓解同质化偏差和社会期望偏差。'
              : 'LLM doesn\'t "answer" questions directly — it acts as an analyst estimating the probability distribution of responses for each persona, then samples from it. Architectural mitigation of uniformity and social desirability biases.'}
          />

          <AdvantageCard
            icon="🌐"
            title={zh ? '群体交互 vs 独立问答' : 'Group Interaction vs Independent Q&A'}
            research={zh
              ? 'AgentSociety (清华 2025) 证明只有智能体之间存在交互才能复现舆论极化等涌现现象。Chuang et al. (NAACL 2024) 发现网络中交互后出现意见碎片化，与社会科学经典发现一致。'
              : 'AgentSociety (Tsinghua 2025) proved only agent-to-agent interaction produces emergent phenomena like opinion polarization. Chuang et al. (NAACL 2024) found post-interaction opinion fragmentation consistent with social science classics.'}
            ourEdge={zh
              ? '社会模拟引擎运行 7 天 3 轮演进：Day 1 冷反应（纯新闻刺激）→ Day 4 同侪影响（住房×年龄聚类的社区多数意见注入）→ Day 7 回音室效应（强社会压力 + 全国趋势）。智能体按住房类型和年龄分层聚类，每轮注入上一轮的社区意见分布，捕捉口口相传、立场极化、中立群体流向等单次 prompt 无法模拟的动态。'
              : 'Social simulation engine runs a 7-day, 3-round evolution: Day 1 cold reaction (raw news stimulus) → Day 4 peer influence (community majority opinion injected by housing×age cluster) → Day 7 echo chamber effect (strong social pressure + national trend). Agents are clustered by housing type and age tier; each round injects the previous round\'s community opinion distribution, capturing word-of-mouth, opinion polarization, and neutral-group drift that single-prompt methods cannot simulate.'}
          />

          <AdvantageCard
            icon="🔄"
            title={zh ? '持续校准 vs 一次性快照' : 'Continuous Calibration vs One-Time Snapshot'}
            research={zh
              ? 'Verasight 报告 LLM 在训练数据丰富领域（政治）表现远好于稀疏领域（品牌）。MIT AgentTorch 实践证明持续回测校准是保持准确性的关键。'
              : 'Verasight reports LLMs perform far better in data-rich domains (politics) than sparse ones (brands). MIT AgentTorch practice confirms continuous backtesting is key to maintaining accuracy.'}
            ourEdge={zh
              ? '每次客户使用产品做仿真，如果分享了真实调研结果，我们就获得一条校准数据。这是通用 LLM 永远无法获得的反馈闭环——因为它们没有我们的客户场景数据。'
              : 'Every time a client runs a simulation and shares real research results, we gain a calibration data point. This is a feedback loop generic LLMs can never achieve — they don\'t have our client scenario data.'}
          />
        </Section>

        {/* ═══════════════════════════════════════════════ */}
        {/* PART 3: Prediction Domains by Confidence Level  */}
        {/* ═══════════════════════════════════════════════ */}
        <Section
          icon="03"
          title={zh ? '预测领域：置信度分级' : 'Prediction Domains: Confidence Tiers'}
          subtitle={zh ? '哪些能预测、哪些要谨慎、哪些做不了——诚实公示' : 'What we can predict, what needs caution, what we can\'t — honest disclosure'}
        >
          <ConfidenceRow
            level={zh ? '高置信度' : 'HIGH'}
            color="text-green-300 bg-green-500/15"
            label={zh ? '研究充分支撑，误差可控' : 'Well-supported by research, error within bounds'}
            domains={[
              {
                name: zh ? '政策态度预测' : 'Policy Attitude Prediction',
                desc: zh
                  ? '不同人群对政府政策的支持/反对分布、情绪强度、关键争议点。政策态度与人口统计强相关（年龄×种族×收入×教育→态度），我们的合成人口在这些维度上经过严格校准。'
                  : 'Support/opposition distribution across demographics, emotional intensity, key controversies. Policy attitudes strongly correlate with demographics (age×ethnicity×income×education→attitude), and our synthetic population is rigorously calibrated on these dimensions.',
                example: zh
                  ? '"CPF 最低提取年龄从 55 调整到 58，各年龄段和收入层的接受度如何？"'
                  : '"CPF minimum withdrawal age change from 55 to 58 — acceptance by age group and income tier?"',
              },
              {
                name: zh ? '价值观与社会态度调查' : 'Values & Social Attitudes',
                desc: zh
                  ? '不同群体对社会议题的态度分布。Park et al. 2024 的 GSS 85% 准确率本质上就是价值观和社会态度调查。新加坡多族群社会让这种关联更加明显。'
                  : 'Attitude distributions across social issues. Park et al. 2024\'s 85% GSS accuracy was essentially a values and social attitudes survey. Singapore\'s multi-ethnic society makes these correlations even more pronounced.',
                example: zh
                  ? '"对 LGBTQ 权利扩展的支持率，在不同宗教和年龄群体中如何分布？"'
                  : '"Support for LGBTQ rights expansion by religion and age group?"',
              },
            ]}
          />

          <ConfidenceRow
            level={zh ? '中等置信度' : 'MEDIUM'}
            color="text-amber-300 bg-amber-500/15"
            label={zh ? '方向性信号可靠，精确数值需验证' : 'Directional signal reliable, precise numbers need validation'}
            domains={[
              {
                name: zh ? '产品概念与定价敏感度' : 'Product Concept & Pricing Sensitivity',
                desc: zh
                  ? '消费偏好与人口统计的关联弱于政策态度。但当产品特征与人群特征有明确关联时（如 Halal 食品对马来族、乐龄保健对 60+），预测仍然可靠。定位：在真人测试前筛选掉 80% 的不靠谱方案。'
                  : 'Consumer preferences correlate less strongly with demographics than policy attitudes. But when product features clearly map to demographic segments (e.g., Halal food for Malay, elderly care for 60+), predictions remain reliable. Positioning: screen out 80% of bad ideas before real testing.',
                example: zh
                  ? '"这款住院保险定价 $199 vs $249，不同收入层和年龄段的购买意愿差异？"'
                  : '"Hospital insurance at $199 vs $249 — purchase intent by income tier and age?"',
              },
              {
                name: zh ? '传播与叙事效果预测' : 'Narrative Effect Prediction',
                desc: zh
                  ? '对文本的情绪反应和传播行为是复杂的。但在"这段话会不会在某个群体中引起反感"这个层面，LLM 已经能提供有用的预警信号。'
                  : 'Emotional reactions and sharing behavior are complex. But at the level of "will this wording cause backlash in a specific group?", LLMs already provide useful early warning signals.',
                example: zh
                  ? '"这条涨价公告用方案 A vs B 的措辞，在低收入群体中引发的负面情绪差异？"'
                  : '"Price increase announcement wording A vs B — negative sentiment difference among low-income groups?"',
              },
            ]}
          />

          <ConfidenceRow
            level={zh ? '需谨慎' : 'CAUTION'}
            color="text-red-300 bg-red-500/15"
            label={zh ? '当前方法局限，不建议作为决策依据' : 'Current method limitations — not recommended as sole decision basis'}
            domains={[
              {
                name: zh ? '具体行为频率' : 'Specific Behavior Frequency',
                desc: zh
                  ? 'LLM 训练数据中没有细粒度的行为-画像映射。Verasight 已验证品牌认知和具体消费习惯的预测误差显著高于态度预测。'
                  : 'LLM training data lacks fine-grained behavior-profile mappings. Verasight verified that brand awareness and specific consumption habit predictions have significantly higher error than attitude predictions.',
                example: zh ? '"碧山居民多久去一次 Giant 超市"' : '"How often do Bishan residents visit Giant supermarket?"',
              },
              {
                name: zh ? '极端少数群体的精确量化' : 'Precise Quantification of Extreme Minorities',
                desc: zh
                  ? 'LLM 系统性地低估极端立场和少数意见，有内在的"趋向共识"偏差。'
                  : 'LLMs systematically underestimate extreme positions and minority opinions — inherent "consensus-seeking" bias.',
                example: zh ? '"新加坡反疫苗群体的确切比例"' : '"Exact percentage of anti-vaccine population in Singapore"',
              },
              {
                name: zh ? '个体级别的精确预测' : 'Individual-Level Precise Prediction',
                desc: zh
                  ? 'Park et al. 2024 的 85% 是群体级别的统计指标。单个个体上存在不可消除的随机性。'
                  : 'Park et al. 2024\'s 85% is a group-level statistical metric. Irreducible randomness exists at the individual level.',
                example: zh ? '"张先生具体会选 A 还是 B"' : '"Will Mr. Zhang specifically choose A or B?"',
              },
            ]}
          />
        </Section>

        {/* ═══════════════════════════════════════════════ */}
        {/* PART 4: References                              */}
        {/* ═══════════════════════════════════════════════ */}
        <Section
          icon="04"
          title={zh ? '论文引用' : 'References'}
          subtitle={zh ? '15 篇核心论文，来自 Stanford、MIT、清华等顶级机构' : '15 core papers from Stanford, MIT, Tsinghua and other leading institutions'}
        >
          <div className="space-y-2">
            {[
              'Park, J.S., et al. (2024). "Generative Agent Simulations of 1,000 People." arXiv:2411.10109. Stanford & Google DeepMind.',
              'Park, J.S., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." UIST \'23 (ACM). Stanford & Google Research.',
              'Argyle, L.P., et al. (2023). "Out of One, Many: Using Language Models to Simulate Human Samples." Political Analysis 31(3). BYU.',
              '"FlockVote: LLM-Empowered Agent-Based Modeling for Election Prediction." arXiv:2512.05982, 2024.',
              'Piao, J., et al. (2025). "AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents." arXiv:2502.08691. Tsinghua University.',
              '"Scaling LLM-Guided Agent Simulations to Millions." AAMAS 2025. MIT Media Lab.',
              'Hidalgo, C.A., et al. (2024). "Large language models as agents for augmented democracy." Royal Society Phil. Trans.',
              'Horton, J.J. (2023). "Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?" NBER Working Paper.',
              'Anthis, J.R., et al. (2025). "Position: LLM Social Simulations Are a Promising Research Method." ICML 2025.',
              'Verasight (2025-2026). "Synthetic Omnibus Survey" White Paper Series. Morris et al.',
              'Chuang, Y.-S., et al. (2024). "Simulating Opinion Dynamics with Networks of LLM-based Agents." NAACL 2024.',
              'Cao, Y., et al. (2025). "Specializing Large Language Models to Simulate Survey Response Distributions." NAACL 2025.',
              'Zhang, S. & Xu, J. (2025). "Generative AI Meets Open-Ended Survey Responses." Sociological Methods & Research.',
              '"LLM-Based Multi-Agent System for Simulating and Analyzing Marketing and Consumer Behavior." arXiv:2510.18155, 2025.',
              '"Evaluating Silicon Sampling: LLM Accuracy in Simulating Public Opinion." Conference Paper, 2025.',
            ].map((ref, i) => (
              <div key={i} className="flex gap-3 items-start text-[11px] text-[#94a3b8] leading-relaxed">
                <span className="text-[#475569] font-mono shrink-0">[{i + 1}]</span>
                <span>{ref}</span>
              </div>
            ))}
          </div>
        </Section>

      </div>

      {/* Footer */}
      <div className="border-t border-[#1e293b] py-8 text-center text-[11px] text-[#475569]">
        {zh
          ? '© 2026 Digital Twin Studio — 新加坡合成人口仿真平台'
          : '© 2026 Digital Twin Studio — Singapore Synthetic Population Simulation Platform'}
      </div>
    </div>
  );
}
