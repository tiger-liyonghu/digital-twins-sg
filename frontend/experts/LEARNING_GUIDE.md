# Expert Learning Mechanism

## Overview
This system maintains a knowledge base for 9 domain experts who advise on the Singapore Digital Twin project. Each expert periodically learns from web sources and codebase changes to stay current.

## File Structure
```
experts/
  knowledge.js      — Deep knowledge base (source code + web research)
  learning_log.js   — Action items from latest learning session
  LEARNING_GUIDE.md — This file (learning process documentation)
```

## Learning Cycle (Recommended: Monthly)

### Step 1: Codebase Scan
Ask Claude to scan the engine/ and frontend/ directories for parameter changes since last session:
```
"Scan the codebase for any parameter changes since March 2026. Update knowledge.js accordingly."
```

### Step 2: Web Research per Expert
Ask Claude to research latest developments for each expert's domain:
```
"Have [expert name] research the latest developments in [domain]. Update knowledge.js and learning_log.js."
```

**Expert domains to research:**
| Expert | Domain | Key Sources |
|--------|--------|------------|
| Dr. Chen Wei (陈维博士) | Demographics, IPF, microsimulation | DOS.gov.sg, UN Population Division |
| Prof. Sarah Lim (林思慧教授) | Social networks, contagion | arXiv cs.SI, Nature Computational Science |
| Prof. Rachel Koh (许瑞秋教授) | NLP, LLM agents, persona prompting | arXiv cs.CL, ACL/EMNLP proceedings |
| Dr. Priya Nair (普里亚博士) | Network science, graph theory | arXiv physics.soc-ph, Network Science journal |
| Dr. Aisha Rahman (艾莎博士) | Survey methodology, MRP | AAPOR, arXiv stat.ME |
| Dr. Michael Ong (王明德博士) | Behavioral psychology, Big Five | JPSP, Psychological Review |
| Mr. Tan Keng Huat (陈庆发先生) | Singapore policy, CPF, HDB | CPF Board, MOM, HDB, MOF Budget |
| Ms. Adeline Wee (黄雅琳) | Privacy, PDPA, AI governance | PDPC.gov.sg, IMDA AI Verify |
| James Liu (刘建明) | Software architecture, scaling | Supabase docs, DeepSeek API, async patterns |

### Step 3: Update Action Items
After research, update `learning_log.js` with:
- New findings that require code changes
- Priority: CRITICAL (factual errors) > HIGH (outdated params) > MEDIUM (improvements)
- Include source URLs for verification

### Step 4: Implement Critical Fixes
Address CRITICAL items immediately (e.g., wrong CPF rates, population numbers).

## Quick Command for Claude
To trigger a full learning session:
```
"Expert learning session: scan codebase for changes, research web for latest updates in all 9 expert domains, update knowledge.js and learning_log.js, and list critical action items."
```

## Last Learning Session
- **Date:** 2026-03-07
- **Experts updated:** All 9 (knowledge.js web research sections)
- **Action items:** 24 total (5 CRITICAL, 9 HIGH, 10 MEDIUM)
- **Status:** See learning_log.js for details
