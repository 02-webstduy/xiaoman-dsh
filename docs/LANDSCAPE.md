# 现有项目调研：个人学习面板 + 每日简报 + 规划

> 调研时间：2026-10-29。星数来自 GitHub API；「最近推送」是同一天的实测值。
> 结论先放前面：**没有成熟的一体化项目**，最省事的做法是「拿 2–3 个现成的 + 小满做人格和每日闭环」。

## 一、候选一览

| 项目 | 星数 | 最近推送 | 协议 | 在你的设想里承担什么 | 缺口 |
|---|---|---|---|---|---|
| [Khoj](https://github.com/khoj-ai/khoj) | 37.9k | 2026-08-02 | AGPL-3.0 | 个人 AI 第二大脑：文档/网页问答、Agent、**定时研究 + 个人简报**、浏览器/Obsidian/手机/WhatsApp | 规划、竞赛、中文源弱；近两月没推送 |
| [Open Notebook](https://github.com/lfnovo/open-notebook) | 40.8k | 2026-10-25 | MIT | NotebookLM 替代：资料 → 笔记 → 对话 → 播客；支持 vLLM/Ollama | 没有日报/规划/陪伴 |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) | 67.7k | 2026-10-28 | MIT | 工作区式 RAG + Agent | 同上 |
| [Open WebUI](https://github.com/open-webui/open-webui) | 157k | 2026-10-29 | 自定义 | 聊天前端 + 知识库 + 工具 | 只是"壳"，流程要自己搭 |
| [n8n](https://github.com/n8n-io/n8n) | 209k | 2026-10-29 | fair-code | 每日抓取 → 清洗 → 调用模型 → 推送 | 不是给人用的学习界面 |
| [RSSHub](https://github.com/DIYgod/RSSHub) + [FreshRSS](https://github.com/FreshRSS/FreshRSS) | 46.7k / 16.4k | 2026-10-29 | AGPL | 把没有 RSS 的站点变成 RSS | 要自己部署；公共实例在本机不可达 |
| [Zotero-arXiv-Daily](https://github.com/TideDra/zotero-arxiv-daily) | 6.1k | 2026-10-01 | AGPL | 按 Zotero 库每天推 arXiv + LLM 摘要，GitHub Actions 零服务器 | 依赖 Zotero；只覆盖论文 |
| [ai-research-radar](https://github.com/mlnjsh/ai-research-radar) | 12 | 2026-10-29 | MIT | GitHub Actions 每 6 小时抓 arXiv、自动摘要 | 太小，只能当参考实现 |
| [PaperFlow](https://github.com/OpenRaiser/PaperFlow) | 176 | 2026-08-22 | MIT | 个性化论文推荐 + 阅读 + 日报 | 小众 |
| [ai-contest-radar](https://github.com/ye4wzp/ai-contest-radar) | 0 | 2026-10-29 | — | 全网 AI 竞赛/黑客松聚合 | 刚起步，不能依赖 |
| [Vikunja](https://github.com/go-vikunja/vikunja) / [Super Productivity](https://github.com/johannesjo/super-productivity) | 5.9k / 23.2k | 2026-10-29 | AGPL / MIT | 任务与时间管理 | 没有 AI |
| [Mem0](https://github.com/mem0ai/mem0) / [Letta](https://github.com/letta-ai/letta) | 68k / 25.3k | 2026-10-26 / 10-18 | Apache-2.0 | 给"记得住你"提供记忆层 | 需要自己接 |

已停更/归档，不建议押注：[Reor](https://github.com/reorproject/reor)（2025-05 归档）、[Flowise](https://github.com/FlowiseAI/Flowise)（归档）、[arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite)（2023 后没动）。

## 二、结论：没有「开箱即用」的一体化

你的设想其实是四件事拼在一起：

1. **有人格的陪伴**（小满）
2. **知识库/学习资料**（Open Notebook、Khoj、AnythingLLM）
3. **每日采集 + 筛选 + 摘要 + 推送**（Khoj automations、n8n、Zotero-arXiv-Daily）
4. **规划 + 竞赛/社区信息**（Vikunja；竞赛目前没有成熟聚合项目）

现成项目能覆盖 1–3 的一部分，**没有项目同时覆盖 4**，中文竞赛这一块尤其空白。

## 三、三条路线

| 路线 | 做法 | 成本 | 评价 |
|---|---|---|---|
| A. 拿来主义 | Khoj（AI + 简报） + RSSHub（源） + Vikunja（任务） | 1–2 天 | 最快可用；但人格、中文竞赛、复盘都弱，改造成本会回流 |
| **B. 小满做壳，组件做里子（推荐）** | 小满负责人格/每日三件事/复盘；采集用自写 Python worker；知识库按需接 Open Notebook | 1–2 周 MVP | 差异化在「中文竞赛 + 复盘 + 陪伴口吻」，不是再造一个 RAG |
| C. 全自研 | 学习页 + RAG + 采集 + 规划全部自己写 | 3–6 周 | 不建议，重复造轮子 |

## 四、如果走 B，你真正的作品是什么

不是「又一个笔记/知识库」，而是**每日闭环**：

```
早上 3 条（论文/项目/竞赛，各一句"为什么与你有关"）
  → 你挑一条
  → 小满问一句"今天能做的 30 分钟是什么"
  → 晚上回来只看这件事
  → 周五自动复盘：做了什么、卡在哪、下周一个实验
```

这块没有现成项目做，而且正好接得上第 2 步（记忆）和第 3 步（脱困流程）。

## 五、本机网络实测（决定采集怎么设计）

| 源 | 结果 |
|---|---|
| arXiv API | ✅ 200（1.4s），支持按分类拉取 |
| Hugging Face Daily Papers | ❌ 官方域超时；✅ `hf-mirror.com` 可用 |
| 机器之心 RSS | ✅ 200 |
| Hacker News (Algolia) | ✅ 200 |
| GitHub API | ✅ 200；网页/gist/raw 慢或不可达 |
| 天池 / Kaggle | ✅ 200（Kaggle 建议走官方 API + token） |
| RSSHub 公共实例 | ❌ 不可达（需自建） |

所以采集层要用 **arXiv + hf-mirror + 机器之心 + HN + GitHub API** 起步，竞赛单独写适配器。

## 六、不算结论的建议

1. 先别部署 Khoj——它和你要的"陪伴 + 规划"不是一回事，接进来还要改它的 agent。
2. 学习资料先用 Open Notebook（MIT、活跃、支持 vLLM），把"看论文/做笔记"这块交出去。
3. 小满只做三件事：**每日三件事、复盘、陪你说话**。这三件没人替你做。
4. 竞赛聚合是最容易做出差异、也最容易维护的一块，建议作为第一个自建适配器。
