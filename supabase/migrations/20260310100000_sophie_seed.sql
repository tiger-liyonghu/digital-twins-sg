INSERT INTO sophie_industries (id, name, name_zh, icon, sort_order, is_other) VALUES
  ('government',  'Government & Public Sector', '政府与公共部门', '🏛️', 1, FALSE),
  ('finance',     'Financial Services & Insurance', '金融与保险', '🏦', 2, FALSE),
  ('healthcare',  'Healthcare & Pharma', '医疗健康与制药', '🏥', 3, FALSE),
  ('retail',      'Retail & Consumer Goods', '零售与消费品', '🛒', 4, FALSE),
  ('realestate',  'Real Estate & Property', '房地产', '🏢', 5, FALSE),
  ('other',       'Other', '其他行业', '🔧', 99, TRUE)
ON CONFLICT (id) DO NOTHING;
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('a0000001-0000-0000-0000-000000000001', 'government', 'policy_simulation',
   'CPF & Retirement Reform', 'CPF与退休制度改革',
   'Test public reaction to changes in CPF withdrawal age, contribution rates, or retirement sum requirements',
   '测试公众对CPF提取年龄、缴费率或退休金要求变化的反应',
   ARRAY['cpf','retirement','pension','withdrawal'], 1),

  ('a0000001-0000-0000-0000-000000000002', 'government', 'policy_simulation',
   'Housing & HDB Policy', 'HDB住房政策',
   'Gauge sentiment on BTO allocation rules, resale levy changes, or new housing grant criteria',
   '衡量公众对BTO分配规则、转售税变化或新住房补助标准的看法',
   ARRAY['hdb','bto','housing','resale','grant'], 2),

  ('a0000001-0000-0000-0000-000000000003', 'government', 'policy_simulation',
   'Immigration & Foreign Workforce', '移民与外劳政策',
   'Assess public attitudes toward EP/S-Pass quotas, PR criteria, or new citizen integration programs',
   '评估公众对EP/S准证配额、PR标准或新公民融入计划的态度',
   ARRAY['immigration','foreign worker','ep','s-pass','pr'], 3),

  ('a0000001-0000-0000-0000-000000000004', 'government', 'policy_simulation',
   'Climate & Sustainability', '气候与可持续发展',
   'Test reactions to carbon tax increases, EV mandates, or plastic reduction policies',
   '测试对碳税上调、电动车政策或减塑政策的反应',
   ARRAY['carbon tax','ev','sustainability','green','climate'], 4),

  ('a0000001-0000-0000-0000-000000000005', 'government', 'policy_simulation',
   'Education & Skills Policy', '教育与技能政策',
   'Gauge public opinion on PSLE reforms, SkillsFuture changes, or university admission criteria',
   '衡量公众对PSLE改革、SkillsFuture变化或大学录取标准的看法',
   ARRAY['psle','education','skillsfuture','university'], 5),

  ('a0000001-0000-0000-0000-000000000006', 'government', 'policy_simulation',
   'Healthcare Subsidies & MediShield', '医疗补贴与MediShield',
   'Test reaction to changes in subsidized healthcare, MediShield Life coverage, or Medisave limits',
   '测试对补贴医疗、MediShield Life保障或Medisave上限变化的反应',
   ARRAY['medishield','medisave','healthcare','subsidy'], 6),

  ('a0000001-0000-0000-0000-000000000007', 'government', 'policy_simulation',
   'Transport & Infrastructure', '交通与基础设施',
   'Assess public sentiment on MRT expansion, ERP changes, COE system reform, or cycling infrastructure',
   '评估公众对MRT扩展、ERP变化、COE制度改革或骑行基础设施的看法',
   ARRAY['mrt','erp','coe','transport','bus'], 7);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('a0000001-0000-0000-0000-000000000011', 'government', 'product_pricing',
   'Public Service Fees & Charges', '公共服务费用',
   'Test acceptance of fee changes for government services (passport, licenses, park entry)',
   '测试公众对政府服务费用变化的接受度（护照、执照、公园门票）',
   ARRAY['fees','charges','service'], 1),

  ('a0000001-0000-0000-0000-000000000012', 'government', 'product_pricing',
   'Transport Fare Adjustments', '交通费用调整',
   'Gauge reaction to MRT/bus fare changes, ERP pricing, or COE premium adjustments',
   '衡量公众对MRT/巴士票价变化、ERP定价或COE溢价调整的反应',
   ARRAY['fare','mrt','bus','erp','coe'], 2),

  ('a0000001-0000-0000-0000-000000000013', 'government', 'product_pricing',
   'Utility & Water Pricing', '水电费定价',
   'Test willingness to pay for water price increases, carbon surcharges, or green energy premiums',
   '测试公众对水价上涨、碳附加费或绿色能源溢价的支付意愿',
   ARRAY['utility','water','electricity','energy'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('a0000001-0000-0000-0000-000000000021', 'government', 'audience_intelligence',
   'Public Trust & Institutional Confidence', '公众信任与制度信心',
   'Understand citizen trust levels in government institutions across different demographics',
   '了解不同人口群体对政府机构的信任水平',
   ARRAY['trust','confidence','institution','satisfaction'], 1),

  ('a0000001-0000-0000-0000-000000000022', 'government', 'audience_intelligence',
   'Digital Government Services', '数字政府服务',
   'Assess adoption barriers and satisfaction with Singpass, LifeSG, and other e-services',
   '评估Singpass、LifeSG等电子服务的使用障碍和满意度',
   ARRAY['singpass','lifesg','digital','e-services'], 2),

  ('a0000001-0000-0000-0000-000000000023', 'government', 'audience_intelligence',
   'Community Needs by Segment', '分群社区需求',
   'Deep dive into unmet needs of specific communities: elderly, low-income, new immigrants, persons with disabilities',
   '深入了解特定社区的未满足需求：老年人、低收入群体、新移民、残障人士',
   ARRAY['community','elderly','low-income','immigrant','disability'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('b0000001-0000-0000-0000-000000000001', 'finance', 'policy_simulation',
   'Interest Rate & Monetary Policy Impact', '利率与货币政策影响',
   'Simulate how MAS interest rate decisions affect consumer borrowing, savings, and investment behavior',
   '模拟MAS利率决策对消费者借贷、储蓄和投资行为的影响',
   ARRAY['interest rate','mas','monetary','savings'], 1),

  ('b0000001-0000-0000-0000-000000000002', 'finance', 'policy_simulation',
   'Financial Regulation Changes', '金融监管变化',
   'Test industry and consumer reaction to new MAS regulations, anti-money laundering rules, or crypto policies',
   '测试行业和消费者对MAS新规、反洗钱规则或加密货币政策的反应',
   ARRAY['regulation','mas','aml','crypto','compliance'], 2),

  ('b0000001-0000-0000-0000-000000000003', 'finance', 'policy_simulation',
   'Tax Policy Effects on Financial Behavior', '税收政策对金融行为的影响',
   'Assess how GST changes, wealth taxes, or property stamp duties affect financial decisions',
   '评估GST变化、财富税或房产印花税如何影响金融决策',
   ARRAY['gst','tax','stamp duty','wealth tax'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('b0000001-0000-0000-0000-000000000011', 'finance', 'product_pricing',
   'Insurance Product Design & Pricing', '保险产品设计与定价',
   'Test consumer preference for different insurance plan structures, premium levels, and coverage options',
   '测试消费者对不同保险计划结构、保费水平和保障选项的偏好',
   ARRAY['insurance','premium','coverage','life','health'], 1),

  ('b0000001-0000-0000-0000-000000000012', 'finance', 'product_pricing',
   'Banking Products & Digital Banking', '银行产品与数字银行',
   'Gauge interest in new savings accounts, credit card features, or digital bank offerings',
   '衡量消费者对新储蓄账户、信用卡功能或数字银行产品的兴趣',
   ARRAY['banking','savings','credit card','digital bank','dbs','ocbc','uob'], 2),

  ('b0000001-0000-0000-0000-000000000013', 'finance', 'product_pricing',
   'Investment & Wealth Management', '投资与财富管理',
   'Test appetite for robo-advisors, ESG funds, crypto products, or new investment platforms',
   '测试消费者对智能投顾、ESG基金、加密货币产品或新投资平台的兴趣',
   ARRAY['investment','robo-advisor','esg','crypto','wealth'], 3),

  ('b0000001-0000-0000-0000-000000000014', 'finance', 'product_pricing',
   'Payment & BNPL Services', '支付与先买后付服务',
   'Assess adoption willingness for new payment methods, BNPL services, or cross-border payment solutions',
   '评估消费者对新支付方式、先买后付服务或跨境支付方案的使用意愿',
   ARRAY['payment','bnpl','paynow','cross-border','fintech'], 4);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('b0000001-0000-0000-0000-000000000021', 'finance', 'audience_intelligence',
   'Financial Literacy & Planning Habits', '金融素养与理财习惯',
   'Understand saving, budgeting, and investment behaviors across different demographics',
   '了解不同人群的储蓄、预算和投资行为',
   ARRAY['literacy','savings','budget','planning'], 1),

  ('b0000001-0000-0000-0000-000000000022', 'finance', 'audience_intelligence',
   'Retirement Readiness', '退休准备程度',
   'Deep dive into retirement planning attitudes, CPF understanding, and elderly financial security concerns',
   '深入了解退休规划态度、CPF理解程度和老年财务安全关切',
   ARRAY['retirement','cpf','elderly','financial security'], 2),

  ('b0000001-0000-0000-0000-000000000023', 'finance', 'audience_intelligence',
   'Digital Finance Adoption Barriers', '数字金融使用障碍',
   'Identify why certain segments resist digital banking, e-payments, or online investment',
   '识别特定群体抗拒数字银行、电子支付或在线投资的原因',
   ARRAY['digital','adoption','barrier','elderly','unbanked'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('c0000001-0000-0000-0000-000000000001', 'healthcare', 'policy_simulation',
   'MediShield & MediSave Reform', 'MediShield与MediSave改革',
   'Test public reaction to coverage expansion, premium changes, or MediSave withdrawal rule adjustments',
   '测试公众对保障扩展、保费变化或MediSave提取规则调整的反应',
   ARRAY['medishield','medisave','coverage','premium'], 1),

  ('c0000001-0000-0000-0000-000000000002', 'healthcare', 'policy_simulation',
   'Telehealth & Digital Health Regulation', '远程医疗与数字健康监管',
   'Gauge acceptance of telehealth mandates, digital prescription rules, or AI diagnostic approvals',
   '衡量公众对远程医疗要求、数字处方规则或AI诊断审批的接受度',
   ARRAY['telehealth','digital health','telemedicine','ai diagnostic'], 2),

  ('c0000001-0000-0000-0000-000000000003', 'healthcare', 'policy_simulation',
   'Eldercare & Long-term Care Policy', '养老与长期护理政策',
   'Assess support for CareShield Life changes, eldercare facility expansion, or caregiver support schemes',
   '评估公众对CareShield Life变化、养老设施扩建或看护者支持计划的支持度',
   ARRAY['eldercare','careshield','long-term care','caregiver','nursing home'], 3),

  ('c0000001-0000-0000-0000-000000000004', 'healthcare', 'policy_simulation',
   'Mental Health Policy', '心理健康政策',
   'Test reaction to workplace mental health mandates, school counseling expansion, or destigmatization campaigns',
   '测试公众对职场心理健康规定、学校心理辅导扩展或去污名化运动的反应',
   ARRAY['mental health','counseling','workplace','stigma'], 4);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('c0000001-0000-0000-0000-000000000011', 'healthcare', 'product_pricing',
   'Health Insurance Plans', '健康保险计划',
   'Test willingness to pay for different Integrated Shield Plan tiers, riders, or new coverage types',
   '测试消费者对不同综合健保计划层级、附加保障或新保障类型的支付意愿',
   ARRAY['insurance','shield plan','rider','premium','ip'], 1),

  ('c0000001-0000-0000-0000-000000000012', 'healthcare', 'product_pricing',
   'Digital Health Services', '数字健康服务',
   'Gauge interest and price sensitivity for telehealth subscriptions, health apps, or wearable-linked services',
   '衡量消费者对远程医疗订阅、健康App或可穿戴设备关联服务的兴趣和价格敏感度',
   ARRAY['telehealth','app','wearable','subscription','digital'], 2),

  ('c0000001-0000-0000-0000-000000000013', 'healthcare', 'product_pricing',
   'Wellness & Prevention Programs', '健康管理与预防计划',
   'Test appetite for corporate wellness packages, health screening bundles, or preventive care subscriptions',
   '测试消费者对企业健康套餐、体检组合或预防保健订阅的兴趣',
   ARRAY['wellness','prevention','screening','corporate','health check'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('c0000001-0000-0000-0000-000000000021', 'healthcare', 'audience_intelligence',
   'Healthcare Access Barriers', '医疗服务获取障碍',
   'Identify why specific groups (elderly, low-income, minorities) face difficulty accessing healthcare',
   '识别特定群体（老年人、低收入群体、少数族裔）获取医疗服务困难的原因',
   ARRAY['access','barrier','elderly','minority','language'], 1),

  ('c0000001-0000-0000-0000-000000000022', 'healthcare', 'audience_intelligence',
   'Mental Health Attitudes by Segment', '不同群体的心理健康态度',
   'Understand stigma, help-seeking behavior, and mental health awareness across age groups and cultures',
   '了解不同年龄段和文化群体的心理健康偏见、求助行为和心理健康意识',
   ARRAY['mental health','stigma','help-seeking','culture','youth'], 2),

  ('c0000001-0000-0000-0000-000000000023', 'healthcare', 'audience_intelligence',
   'Caregiver Experience & Needs', '看护者体验与需求',
   'Deep dive into the challenges, burnout, and support needs of family caregivers for elderly or disabled persons',
   '深入了解家庭看护者（照顾老年人或残障人士）的挑战、倦怠和支持需求',
   ARRAY['caregiver','burnout','family','elderly','support'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('d0000001-0000-0000-0000-000000000001', 'retail', 'policy_simulation',
   'Consumer Protection & E-commerce Rules', '消费者保护与电商规则',
   'Test consumer reaction to new online shopping regulations, return policies, or marketplace accountability rules',
   '测试消费者对新的网购规定、退货政策或平台责任规则的反应',
   ARRAY['consumer protection','e-commerce','regulation','return policy'], 1),

  ('d0000001-0000-0000-0000-000000000002', 'retail', 'policy_simulation',
   'Sustainability & Packaging Mandates', '可持续发展与包装规定',
   'Gauge consumer willingness to accept plastic bag charges, packaging reduction rules, or sustainability labels',
   '衡量消费者接受塑料袋收费、包装减量规则或可持续标签的意愿',
   ARRAY['sustainability','plastic','packaging','green','eco'], 2);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('d0000001-0000-0000-0000-000000000011', 'retail', 'product_pricing',
   'New Product Concept Testing', '新产品概念测试',
   'Test consumer interest and willingness to pay for new F&B concepts, consumer products, or service innovations',
   '测试消费者对新餐饮概念、消费产品或服务创新的兴趣和支付意愿',
   ARRAY['new product','concept','f&b','innovation','launch'], 1),

  ('d0000001-0000-0000-0000-000000000012', 'retail', 'product_pricing',
   'Pricing & Promotion Sensitivity', '定价与促销敏感度',
   'Assess price elasticity for different product categories, discount structures, or bundle pricing',
   '评估不同产品类别的价格弹性、折扣结构或捆绑定价',
   ARRAY['pricing','discount','bundle','promotion','elasticity'], 2),

  ('d0000001-0000-0000-0000-000000000013', 'retail', 'product_pricing',
   'Subscription vs One-time Purchase', '订阅制vs一次性购买',
   'Test preference for subscription models versus traditional purchase across various product categories',
   '测试消费者在各类产品中对订阅模式vs传统购买的偏好',
   ARRAY['subscription','recurring','one-time','model','saas'], 3),

  ('d0000001-0000-0000-0000-000000000014', 'retail', 'product_pricing',
   'Brand Positioning & Perception', '品牌定位与认知',
   'Compare brand perception, premium willingness, and competitive positioning among target segments',
   '比较目标群体中的品牌认知、溢价意愿和竞争定位',
   ARRAY['brand','perception','positioning','premium','loyalty'], 4);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('d0000001-0000-0000-0000-000000000021', 'retail', 'audience_intelligence',
   'Shopping Behavior & Channel Preference', '购物行为与渠道偏好',
   'Understand online vs offline shopping habits, platform preferences, and purchase decision factors',
   '了解线上线下购物习惯、平台偏好和购买决策因素',
   ARRAY['shopping','online','offline','channel','platform','lazada','shopee'], 1),

  ('d0000001-0000-0000-0000-000000000022', 'retail', 'audience_intelligence',
   'Sustainability & Ethical Consumption', '可持续与道德消费',
   'Deep dive into willingness to pay for sustainable products, ethical sourcing awareness, and green purchasing barriers',
   '深入了解消费者为可持续产品支付溢价的意愿、道德采购意识和绿色购买障碍',
   ARRAY['sustainability','ethical','green','organic','fair trade'], 2),

  ('d0000001-0000-0000-0000-000000000023', 'retail', 'audience_intelligence',
   'F&B Dining Trends & Preferences', '餐饮趋势与偏好',
   'Understand dining-out frequency, cuisine preferences, food delivery usage, and price sensitivity by segment',
   '了解不同群体的外出就餐频率、菜系偏好、外卖使用和价格敏感度',
   ARRAY['f&b','dining','food delivery','hawker','restaurant','grab food'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('e0000001-0000-0000-0000-000000000001', 'realestate', 'policy_simulation',
   'HDB Policies & BTO Reform', 'HDB政策与BTO改革',
   'Test reaction to BTO allocation changes, resale levy adjustments, or new flat classification rules',
   '测试公众对BTO分配变化、转售税调整或新组屋分类规则的反应',
   ARRAY['hdb','bto','resale','flat','allocation'], 1),

  ('e0000001-0000-0000-0000-000000000002', 'realestate', 'policy_simulation',
   'Property Cooling Measures', '房产降温措施',
   'Gauge reaction to ABSD changes, TDSR tightening, or new foreign buyer restrictions',
   '衡量公众对ABSD变化、TDSR收紧或新的外国买家限制的反应',
   ARRAY['absd','tdsr','cooling','stamp duty','foreign buyer'], 2),

  ('e0000001-0000-0000-0000-000000000003', 'realestate', 'policy_simulation',
   'Rental Market Regulation', '租赁市场监管',
   'Assess support for rental caps, tenant protections, or short-term rental (Airbnb) rules',
   '评估公众对租金上限、租户保护或短期租赁（Airbnb）规则的支持度',
   ARRAY['rental','tenant','airbnb','landlord','cap'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('e0000001-0000-0000-0000-000000000011', 'realestate', 'product_pricing',
   'Condo Features & Amenity Valuation', '公寓设施与配套估值',
   'Test how much buyers value specific amenities: smart home, EV charging, co-working spaces, greenery',
   '测试买家对特定配套的估值：智能家居、电动车充电、共享办公、绿化',
   ARRAY['condo','amenity','smart home','ev charging','pool','gym'], 1),

  ('e0000001-0000-0000-0000-000000000012', 'realestate', 'product_pricing',
   'Co-living & Flexible Housing', '共享居住与灵活住房',
   'Gauge interest in co-living concepts, serviced apartments, or flexible-term leasing among different segments',
   '衡量不同群体对共享居住概念、服务式公寓或灵活租期的兴趣',
   ARRAY['co-living','serviced apartment','flexible','sharing','young professional'], 2),

  ('e0000001-0000-0000-0000-000000000013', 'realestate', 'product_pricing',
   'PropTech Services', '房产科技服务',
   'Test adoption willingness for virtual tours, AI property matching, or blockchain-based transactions',
   '测试消费者对虚拟看房、AI房产匹配或区块链交易的使用意愿',
   ARRAY['proptech','virtual tour','ai','blockchain','digital'], 3);
INSERT INTO sophie_topics (id, industry_id, scenario_type, name, name_zh, description, description_zh, keywords, sort_order) VALUES
  ('e0000001-0000-0000-0000-000000000021', 'realestate', 'audience_intelligence',
   'Housing Aspirations & Upgrading Intent', '住房期望与升级意向',
   'Understand housing goals, upgrading timeline, and budget expectations across demographics',
   '了解不同人群的住房目标、升级时间表和预算期望',
   ARRAY['aspiration','upgrading','budget','dream home','first home'], 1),

  ('e0000001-0000-0000-0000-000000000022', 'realestate', 'audience_intelligence',
   'Neighborhood & Location Preferences', '社区与位置偏好',
   'Deep dive into what makes a desirable neighborhood: MRT access, schools, amenities, community feel',
   '深入了解理想社区的要素：地铁可达性、学校、配套、社区氛围',
   ARRAY['neighborhood','location','mrt','school','amenity','community'], 2),

  ('e0000001-0000-0000-0000-000000000023', 'realestate', 'audience_intelligence',
   'Elderly & Downsizing Needs', '老年人住房与缩小需求',
   'Understand elderly housing preferences: aging in place, downsizing motivations, assisted living interest',
   '了解老年人住房偏好：原地养老、缩小住房动机、辅助生活兴趣',
   ARRAY['elderly','downsizing','aging in place','assisted living','senior'], 3);
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('a0000001-0000-0000-0000-000000000001', 'CPF contribution rates: 20% employee + 17% employer for workers under 55', 'CPF缴费率：55岁以下员工缴20%，雇主缴17%', 'CPF Board 2025'),
  ('a0000001-0000-0000-0000-000000000001', 'CPF withdrawal age for retirement sum: 55 (partial), with Full Retirement Sum (FRS) of S$205,800 in 2025', 'CPF退休金提取年龄：55岁（部分），2025年全额退休金为S$205,800', 'CPF Board 2025'),
  ('a0000001-0000-0000-0000-000000000001', 'CPF interest rates: OA 2.5%, SA/MA/RA 4.0%, extra 1% on first S$60K', 'CPF利率：普通账户2.5%，特别/保健/退休账户4.0%，首S$6万额外1%', 'CPF Board'),
  ('a0000001-0000-0000-0000-000000000001', 'Singapore life expectancy: 84.07 years (2024), one of the highest globally', '新加坡预期寿命：84.07岁（2024），全球最高之一', 'World Bank'),
  ('a0000001-0000-0000-0000-000000000001', 'Median monthly household income: S$10,099 (2023)', '家庭月收入中位数：S$10,099（2023）', 'DOS');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('a0000001-0000-0000-0000-000000000002', '~78% of Singapore residents live in HDB flats', '约78%的新加坡居民住在HDB组屋中', 'HDB Annual Report'),
  ('a0000001-0000-0000-0000-000000000002', 'BTO application rate for mature estates: 5-10x oversubscribed on average', '成熟区BTO申请率：平均超额认购5-10倍', 'HDB'),
  ('a0000001-0000-0000-0000-000000000002', 'Median resale HDB price (4-room): ~S$550,000 in 2025', '4房式HDB转售中位价：2025年约S$550,000', 'HDB Resale Index'),
  ('a0000001-0000-0000-0000-000000000002', 'New flat classification: Standard, Plus, Prime (from 2024)', '新组屋分类：标准型、优选型、黄金型（2024年起）', 'HDB'),
  ('a0000001-0000-0000-0000-000000000002', 'Enhanced CPF Housing Grant up to S$80,000 for eligible first-timers', '符合条件的首次购房者可获最高S$80,000的CPF住房补助', 'HDB');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('a0000001-0000-0000-0000-000000000003', 'Singapore population: 5.92 million (2024), of which 4.15M are residents (3.61M citizens + 0.54M PRs)', '新加坡人口：592万（2024），其中415万为居民（361万公民+54万PR）', 'DOS'),
  ('a0000001-0000-0000-0000-000000000003', 'Non-resident workforce: ~1.77 million on various work passes (EP, S-Pass, WP)', '非居民劳动力：约177万持各类工作准证（EP、S准证、WP）', 'MOM'),
  ('a0000001-0000-0000-0000-000000000003', 'COMPASS (Complementarity Assessment Framework) for EP holders introduced Sep 2023', 'EP持有者的COMPASS互补性评估框架于2023年9月推出', 'MOM'),
  ('a0000001-0000-0000-0000-000000000003', 'New citizens per year: ~20,000-22,000; new PRs: ~30,000-35,000', '每年新公民：约2万-2.2万；新PR：约3万-3.5万', 'PMO');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('b0000001-0000-0000-0000-000000000011', 'All Singapore citizens/PRs are covered by MediShield Life (basic health insurance)', '所有新加坡公民/PR均受MediShield Life（基本健康保险）保障', 'MOH'),
  ('b0000001-0000-0000-0000-000000000011', 'Integrated Shield Plans (IPs): ~70% of residents have upgraded coverage from private insurers', '综合健保计划（IP）：约70%居民拥有私人保险公司的升级保障', 'LIA'),
  ('b0000001-0000-0000-0000-000000000011', 'Life insurance penetration rate in Singapore: ~7.8% of GDP', '新加坡人寿保险渗透率：约占GDP的7.8%', 'LIA'),
  ('b0000001-0000-0000-0000-000000000011', 'Average annual insurance premium per capita: ~S$4,200', '人均年保费：约S$4,200', 'LIA');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('c0000001-0000-0000-0000-000000000001', 'Total healthcare expenditure: ~S$37 billion (2024), ~4.1% of GDP', '总医疗支出：约S$370亿（2024），占GDP约4.1%', 'MOH'),
  ('c0000001-0000-0000-0000-000000000001', 'Government subsidizes up to 80% at polyclinics for citizens', '政府为公民在综合诊所提供最高80%补贴', 'MOH'),
  ('c0000001-0000-0000-0000-000000000001', 'MediShield Life premiums: S$130-2,840/year depending on age', 'MediShield Life保费：S$130-2,840/年，视年龄而定', 'CPF Board'),
  ('c0000001-0000-0000-0000-000000000001', 'Pioneer Generation: additional subsidies and Medisave top-ups', '建国一代：额外补贴和Medisave充值', 'MOH');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('e0000001-0000-0000-0000-000000000001', 'HDB loan interest rate: 2.6% (pegged at 0.1% above CPF OA rate)', 'HDB贷款利率：2.6%（高于CPF普通账户利率0.1%）', 'HDB'),
  ('e0000001-0000-0000-0000-000000000001', 'Income ceiling for BTO: S$14,000/month for families, S$7,000 for singles', 'BTO收入上限：家庭S$14,000/月，单身S$7,000/月', 'HDB'),
  ('e0000001-0000-0000-0000-000000000001', 'Minimum occupation period (MOP): 5 years for BTO flats', '最低居住期限（MOP）：BTO组屋5年', 'HDB'),
  ('e0000001-0000-0000-0000-000000000001', 'New BTO supply: ~19,000-23,000 flats per year (2023-2025)', '新BTO供应：每年约19,000-23,000套（2023-2025）', 'HDB');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('e0000001-0000-0000-0000-000000000002', 'ABSD rates (2024): 20% for 2nd property (citizens), 30% for 3rd+, 60% for foreigners', 'ABSD税率（2024）：公民第二套20%，第三套+30%，外国人60%', 'IRAS'),
  ('e0000001-0000-0000-0000-000000000002', 'Total Debt Servicing Ratio (TDSR): max 55% of gross monthly income', '总偿债率（TDSR）：不超过月总收入的55%', 'MAS'),
  ('e0000001-0000-0000-0000-000000000002', 'Private residential property price index rose ~30% from 2020 to 2024', '私人住宅价格指数从2020到2024年上涨约30%', 'URA');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('d0000001-0000-0000-0000-000000000011', 'Singapore retail sales: ~S$4.5 billion/month (2024)', '新加坡零售销售额：约S$45亿/月（2024）', 'DOS'),
  ('d0000001-0000-0000-0000-000000000011', 'E-commerce penetration: ~15% of total retail, growing ~20% YoY', '电商渗透率：约占总零售额的15%，年增长约20%', 'Statista'),
  ('d0000001-0000-0000-0000-000000000011', 'Top e-commerce platforms: Shopee, Lazada, Amazon SG', '主要电商平台：Shopee、Lazada、Amazon SG', 'SimilarWeb'),
  ('d0000001-0000-0000-0000-000000000011', 'Average monthly household expenditure: ~S$5,200 (2024)', '家庭月均消费支出：约S$5,200（2024）', 'DOS');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('d0000001-0000-0000-0000-000000000021', 'Smartphone penetration: 97%, one of highest globally', '智能手机渗透率：97%，全球最高之一', 'IMDA'),
  ('d0000001-0000-0000-0000-000000000021', 'Social commerce growing: ~40% of online shoppers have purchased via social media', '社交电商增长：约40%的网购者曾通过社交媒体购物', 'Meta/Bain'),
  ('d0000001-0000-0000-0000-000000000021', 'Cash usage declining: >60% of transactions now cashless (PayNow, cards, e-wallets)', '现金使用下降：超60%的交易为无现金（PayNow、银行卡、电子钱包）', 'MAS');
INSERT INTO sophie_context_facts (topic_id, fact, fact_zh, source) VALUES
  ('d0000001-0000-0000-0000-000000000023', 'Average lunch cost: S$5-8 hawker, S$10-15 food court/cafe, S$20-35 restaurant', '午餐均价：小贩中心S$5-8，美食广场S$10-15，餐厅S$20-35', 'Informal survey'),
  ('d0000001-0000-0000-0000-000000000023', 'Food delivery market size: ~S$2.5 billion (2024), Grab Food ~55% market share', '外卖市场规模：约S$25亿（2024），Grab Food占约55%份额', 'Momentum Works'),
  ('d0000001-0000-0000-0000-000000000023', 'Hawker centres: 114 across Singapore, UNESCO-listed cultural heritage', '小贩中心：全新加坡114个，列入联合国教科文组织非遗名录', 'NEA');
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('government', 'policy_simulation', 1,
   'Which policy area are you looking to test? For example, CPF reform, housing rules, immigration quotas, or something else?',
   '你想预演哪个政策领域？比如CPF改革、住房规则、移民配额，还是其他？', 1),
  ('government', 'policy_simulation', 2,
   'What''s the specific policy change you''re considering? And what''s the key concern — public backlash, demographic divide, or implementation feasibility?',
   '你们在考虑的具体政策变化是什么？主要担心什么——公众反弹、人群分化、还是实施可行性？', 1),
  ('government', 'policy_simulation', 3,
   'Who are the critical segments you need to convince? Any particular age group, housing type, or income bracket you''re most worried about?',
   '你最需要说服的关键群体是谁？有没有特别担心的年龄段、住房类型或收入水平？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('government', 'product_pricing', 1,
   'Which public service fee or charge are you considering adjusting? Transport fares, utility prices, service fees?',
   '你在考虑调整哪项公共服务费用？交通费、水电费、还是服务收费？', 1),
  ('government', 'product_pricing', 2,
   'What''s the proposed change and range? And what outcome matters most — public acceptance, revenue impact, or fairness perception?',
   '拟议的调整幅度是多少？最关心的结果是什么——公众接受度、收入影响、还是公平感？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('government', 'audience_intelligence', 1,
   'Which community or population segment do you want to understand better? Elderly, youth, new immigrants, specific ethnic groups?',
   '你想深入了解哪个社区或人群？老年人、年轻人、新移民、还是特定族裔群体？', 1),
  ('government', 'audience_intelligence', 2,
   'What aspect of their experience are you most interested in — daily challenges, service satisfaction, unmet needs, or attitudes toward a specific topic?',
   '你最想了解他们体验的哪个方面——日常挑战、服务满意度、未满足需求、还是对某个特定话题的态度？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('finance', 'policy_simulation', 1,
   'Which financial policy or regulation change are you exploring? Interest rates, tax policy, compliance rules, or crypto regulation?',
   '你在关注哪方面的金融政策或监管变化？利率、税收政策、合规规则、还是加密货币监管？', 1),
  ('finance', 'policy_simulation', 2,
   'How would this change affect your customers or business? What''s the key uncertainty you want to resolve?',
   '这个变化会怎样影响你的客户或业务？你最想解决的关键不确定性是什么？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('finance', 'product_pricing', 1,
   'What type of financial product are you testing? Insurance plan, banking product, investment offering, or payment service?',
   '你想测试什么类型的金融产品？保险计划、银行产品、投资产品、还是支付服务？', 1),
  ('finance', 'product_pricing', 2,
   'What''s the pricing decision you need to make? Are you testing price sensitivity, feature trade-offs, or competitive positioning?',
   '你需要做什么定价决策？是测试价格敏感度、功能取舍、还是竞争定位？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('finance', 'audience_intelligence', 1,
   'Which customer segment do you want to understand better? Young professionals, retirees, high-net-worth, or underserved groups?',
   '你想深入了解哪个客户群体？年轻专业人士、退休人员、高净值群体、还是服务不足的群体？', 1),
  ('finance', 'audience_intelligence', 2,
   'What behavior or attitude are you trying to understand — financial planning habits, digital adoption barriers, or product awareness gaps?',
   '你想了解什么行为或态度——理财规划习惯、数字化使用障碍、还是产品认知差距？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('healthcare', 'policy_simulation', 1,
   'Which healthcare policy are you exploring? MediShield changes, telehealth rules, eldercare expansion, or mental health mandates?',
   '你在关注哪方面的医疗政策？MediShield变化、远程医疗规则、养老扩展、还是心理健康规定？', 1),
  ('healthcare', 'policy_simulation', 2,
   'What''s the specific change being considered, and what reaction are you most concerned about — cost sensitivity, access impact, or trust issues?',
   '具体在考虑什么变化？最担心的反应是什么——费用敏感度、可及性影响、还是信任问题？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('healthcare', 'product_pricing', 1,
   'What healthcare product or service are you testing? Insurance plan, digital health service, wellness program, or medical device?',
   '你想测试什么医疗产品或服务？保险计划、数字健康服务、健康管理计划、还是医疗设备？', 1),
  ('healthcare', 'product_pricing', 2,
   'What''s the pricing question — willingness to pay for premium features, price comparison with competitors, or subscription vs pay-per-use?',
   '定价问题是什么——为优质功能的支付意愿、与竞品的价格对比、还是订阅vs按次付费？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('healthcare', 'audience_intelligence', 1,
   'Which patient or population group do you want to understand? Elderly patients, caregivers, specific disease groups, or underserved communities?',
   '你想了解哪个患者或人群？老年患者、看护者、特定疾病群体、还是医疗服务不足的社区？', 1),
  ('healthcare', 'audience_intelligence', 2,
   'What do you most need to understand about them — barriers to care, treatment preferences, trust factors, or unmet needs?',
   '你最需要了解他们什么——就医障碍、治疗偏好、信任因素、还是未满足需求？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('retail', 'policy_simulation', 1,
   'Which regulation or policy affecting retail are you interested in? E-commerce rules, sustainability mandates, consumer protection, or import regulations?',
   '你关注哪方面影响零售的法规或政策？电商规则、可持续发展规定、消费者保护、还是进口法规？', 1),
  ('retail', 'policy_simulation', 2,
   'How would this policy change affect your business operations or consumer behavior? What''s the key risk you want to quantify?',
   '这个政策变化会怎样影响你的业务运营或消费者行为？你最想量化的关键风险是什么？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('retail', 'product_pricing', 1,
   'What are you testing — a new product concept, pricing strategy, promotion format, or brand positioning?',
   '你在测试什么——新产品概念、定价策略、促销形式、还是品牌定位？', 1),
  ('retail', 'product_pricing', 2,
   'Who is your target customer? And what''s the core decision — price point, feature set, packaging, or competitive differentiation?',
   '你的目标客户是谁？核心决策是什么——价格点、功能组合、包装、还是竞争差异化？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('retail', 'audience_intelligence', 1,
   'Which consumer segment do you want to explore? By age, lifestyle, spending level, or shopping behavior?',
   '你想探索哪个消费者群体？按年龄、生活方式、消费水平、还是购物行为？', 1),
  ('retail', 'audience_intelligence', 2,
   'What insight are you looking for — purchase drivers, brand perception, channel preferences, or unmet needs?',
   '你在寻找什么洞察——购买驱动因素、品牌认知、渠道偏好、还是未满足需求？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('realestate', 'policy_simulation', 1,
   'Which property policy are you interested in testing? HDB allocation, cooling measures, rental regulations, or land use changes?',
   '你想测试哪方面的房产政策？HDB分配、降温措施、租赁法规、还是土地使用变化？', 1),
  ('realestate', 'policy_simulation', 2,
   'What''s the specific change and who are the most affected groups? Buyers, renters, investors, or developers?',
   '具体变化是什么？受影响最大的群体是谁？买家、租客、投资者、还是开发商？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('realestate', 'product_pricing', 1,
   'What property product or service are you testing? Condo amenities, co-living concepts, PropTech services, or pricing tiers?',
   '你在测试什么房产产品或服务？公寓配套、共享居住概念、房产科技服务、还是定价层级？', 1),
  ('realestate', 'product_pricing', 2,
   'What''s the key question — willingness to pay for specific features, market sizing, or competitive positioning?',
   '关键问题是什么——为特定功能的支付意愿、市场规模估算、还是竞争定位？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('realestate', 'audience_intelligence', 1,
   'Which group''s housing needs do you want to understand? First-time buyers, upgraders, elderly downsizers, or renters?',
   '你想了解哪个群体的住房需求？首次购房者、升级换房者、老年缩小住房者、还是租客？', 1),
  ('realestate', 'audience_intelligence', 2,
   'What aspect matters most — location preferences, budget constraints, lifestyle priorities, or decision-making process?',
   '哪个方面最重要——位置偏好、预算限制、生活方式优先级、还是决策过程？', 1);
INSERT INTO sophie_probe_templates (industry_id, scenario_type, stage, template, template_zh, sort_order) VALUES
  ('other', 'policy_simulation', 1,
   'What policy or regulation change are you looking to test? Tell me the specific area and I''ll help design the right survey.',
   '你想测试什么政策或法规变化？告诉我具体领域，我来帮你设计合适的问卷。', 1),
  ('other', 'policy_simulation', 2,
   'What outcome are you most interested in — public support levels, demographic differences in response, or potential controversy areas?',
   '你最关心什么结果——公众支持度、不同人群的反应差异、还是潜在争议点？', 1),
  ('other', 'product_pricing', 1,
   'What product or service are you testing? Tell me about the concept and the key pricing decision you need to make.',
   '你在测试什么产品或服务？告诉我概念和你需要做的关键定价决策。', 1),
  ('other', 'product_pricing', 2,
   'Who is your target audience and what''s the main uncertainty — price point acceptance, feature preferences, or competitive positioning?',
   '你的目标受众是谁？主要的不确定性是什么——价格接受度、功能偏好、还是竞争定位？', 1),
  ('other', 'audience_intelligence', 1,
   'Which audience segment do you want to understand better? Describe the group and what you''re trying to learn.',
   '你想深入了解哪个受众群体？描述一下这个群体和你想了解的内容。', 1),
  ('other', 'audience_intelligence', 2,
   'What''s driving this research — a specific business decision, a knowledge gap, or a strategic planning exercise?',
   '这项调研的驱动力是什么——具体的业务决策、知识缺口、还是战略规划？', 1);
INSERT INTO sophie_survey_patterns (name, name_zh, pattern_type, description, description_zh, example_question, example_question_zh, example_options, example_options_zh, best_for, best_for_zh) VALUES
  ('Likert Agreement Scale', '李克特同意量表', 'likert',
   '5-point agree/disagree scale for measuring attitudes and opinions',
   '5点同意/不同意量表，用于衡量态度和观点',
   'To what extent do you agree with the following statement: "The government should increase carbon tax to combat climate change."',
   '你在多大程度上同意以下说法："政府应提高碳税以应对气候变化。"',
   '["Strongly agree", "Somewhat agree", "Neutral", "Somewhat disagree", "Strongly disagree"]',
   '["非常同意", "比较同意", "中立", "不太同意", "非常不同意"]',
   'Policy approval, attitude measurement, satisfaction surveys',
   '政策支持度、态度衡量、满意度调查'),

  ('Multiple Choice (Mutually Exclusive)', '单选题（互斥选项）', 'choice',
   'Single-select from 5-8 options covering all possible responses, including a neutral/NA option',
   '从5-8个覆盖所有可能回答的选项中单选，包含中立/不适用选项',
   'What is the biggest challenge you face when accessing healthcare services in Singapore?',
   '你在新加坡获取医疗服务时面临的最大挑战是什么？',
   '["Long waiting times", "High costs", "Language barriers", "Inconvenient locations", "Lack of awareness", "No major challenges"]',
   '["等待时间长", "费用高", "语言障碍", "位置不便", "缺乏了解", "没有大的挑战"]',
   'Identifying top concerns, preference ranking, barrier analysis',
   '识别首要关切、偏好排序、障碍分析'),

  ('Behavioral Intent', '行为意向', 'behavior',
   'Measures likelihood of taking a specific action, from very likely to very unlikely',
   '衡量采取特定行动的可能性，从非常可能到非常不可能',
   'If a new meal subscription service offers unlimited lunch deliveries for S$199/month, how likely are you to subscribe?',
   '如果一项新的餐饮订阅服务以S$199/月提供无限午餐配送，你有多大可能订阅？',
   '["Very likely", "Somewhat likely", "Neutral", "Unlikely", "Very unlikely", "Not applicable"]',
   '["很可能", "比较可能", "中立", "不太可能", "很不可能", "不适用"]',
   'Product launch prediction, pricing sensitivity, adoption forecasting',
   '产品推出预测、定价敏感度、采用率预测'),

  ('Willingness to Pay', '支付意愿', 'willingness',
   'Tests price acceptance with tiered options to find the optimal price point',
   '通过分层选项测试价格接受度，找到最优价格点',
   'What is the maximum monthly premium you would pay for a comprehensive health insurance plan with full coverage?',
   '你愿意为一份全面覆盖的综合健康保险计划支付的最高月保费是多少？',
   '["Under S$100", "S$100-200", "S$200-300", "S$300-500", "Over S$500", "Would not purchase"]',
   '["S$100以下", "S$100-200", "S$200-300", "S$300-500", "S$500以上", "不会购买"]',
   'Pricing strategy, market sizing, premium feature valuation',
   '定价策略、市场规模估算、高级功能估值'),

  ('Scenario Response', '情景反应', 'ranking',
   'Presents a hypothetical scenario and asks for the respondent''s likely response or reaction',
   '呈现一个假设情景，询问受访者可能的反应或回应',
   'The government announces that COE prices will be capped at S$80,000. How would you respond?',
   '政府宣布COE价格将封顶在S$80,000。你会怎么回应？',
   '["Strongly support", "Cautiously support", "Need more info", "Cautiously oppose", "Strongly oppose", "Doesn''t affect me"]',
   '["强烈支持", "谨慎支持", "需要更多信息", "谨慎反对", "强烈反对", "与我无关"]',
   'Policy simulation, public reaction forecasting, controversy detection',
   '政策模拟、公众反应预测、争议检测');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('a0000001-0000-0000-0000-000000000001', 21, 75, 'CPF affects all working-age adults and retirees', 'CPF影响所有工作年龄成人和退休人员');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('a0000001-0000-0000-0000-000000000002', 21, 45, 'Housing policy most impacts first-time buyers aged 21-45', '住房政策对21-45岁首次购房者影响最大');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('a0000001-0000-0000-0000-000000000003', 21, 75, 'Immigration policy affects all residents with broad economic impact', '移民政策影响所有居民，经济影响广泛');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('b0000001-0000-0000-0000-000000000011', 25, 64, 'Insurance purchasing decisions peak in 25-64 age range', '保险购买决策集中在25-64岁');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('c0000001-0000-0000-0000-000000000021', 18, 80, 'Healthcare access barriers affect all ages but especially elderly', '医疗服务获取障碍影响所有年龄段，尤其是老年人');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('c0000001-0000-0000-0000-000000000003', 35, 80, 'Eldercare policy concerns both seniors and their working-age caregivers', '养老政策关系到老年人和他们的工作年龄看护者');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('d0000001-0000-0000-0000-000000000011', 21, 55, 'Product concept testing targets primary consumer spending ages', '产品概念测试针对主要消费支出年龄段');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('e0000001-0000-0000-0000-000000000001', 21, 45, 'HDB BTO policy primarily impacts young couples and families', 'HDB BTO政策主要影响年轻夫妇和家庭');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('e0000001-0000-0000-0000-000000000002', 25, 65, 'Cooling measures affect property owners and active market participants', '降温措施影响业主和活跃的市场参与者');
INSERT INTO sophie_audience_presets (topic_id, age_min, age_max, rationale, rationale_zh) VALUES
  ('e0000001-0000-0000-0000-000000000023', 55, 80, 'Elderly downsizing and housing needs are most relevant for 55+', '老年缩小住房需求对55岁以上最相关');
