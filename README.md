# 小满

一个接本地模型、常驻服务器、有固定人格的「脱困搭子」。第 1 步只做了一件事：**让你能和它好好说话**。

- 本地 `Qwen2.5-7B-AWQ` 流式对话，首字 ~120ms
- 人格写在 [base.md](src/xiaoman/persona/base.md)，改完刷新即生效
- 会话内记忆（刷新不丢，重启即忘）
- 说「卡住」时先做三分类：没方向 / 有方向但没动力 / 有方向但不知道怎么做
- 被问「上次」会老实说没记住，不编
- 自玩评测（10 个剧本 × 4 轮 × 2 遍）：**68/80 条完全合规（85%）**

> 状态：MVP，第 1 步（对话 + 人格 + 自玩评测）。下一步计划见文末 Roadmap。

## 快速开始

```bash
cd xiaoman
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m xiaoman
# http://127.0.0.1:8765

# 想让它常驻（关掉终端也不停）：
setsid nohup .venv/bin/python -m xiaoman > /tmp/xiaoman.log 2>&1 &
```

模型地址、端口、名字都在 [config.toml](config.toml)；密钥只走环境变量。

## 版本迭代

| 版本 | 改了什么 | 自玩评测（两轮合并） | 结论 |
|---|---|---|---|
| baseline | 第 1 步交付 | 53/80 = 66% | — |
| round1 | 只给「卡住」加适用范围 | 24/40 = 60% | ❌ 三分类丢了，问号变多 |
| **v2** | 范围限定 + 格式纪律（禁清单/标题/多问号） | **68/80 = 85%** | ✅ 保留，平均 40 字 |
| v3 | 加「别分析」「接上文」 | 61/80 = 76% | ❌ 清单和长回复回来了 |

每个版本的失败案例、噪声数据和判断依据在 [docs/iterations.md](docs/iterations.md)；评测方法在 [WORKFLOW.md](WORKFLOW.md)。

## 目录

```
src/xiaoman/       后端：app.py（HTTP/SSE）、llm.py、config.py、persona/base.md
web/               前端：index.html、app.js、style.css、pet.js
eval/              scenarios.json（固定剧本）、results/（各版本汇总）
scripts/           selfplay.py（自玩评测）
docs/              ARCHITECTURE.md、iterations.md
```

## 文档

| 文档 | 内容 |
|---|---|
| [ROADMAP.md](ROADMAP.md) | 整张地图 + 一步一步做的协议 |
| [WORKFLOW.md](WORKFLOW.md) | 自玩评测：角色、流程、噪声、红线 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 前后端结构、一次输入到输出的完整链路 |
| [docs/iterations.md](docs/iterations.md) | 每个版本的改动、分数、失败案例 |

## Roadmap

- [x] 第 1 步：能聊（本地模型 + 人格 + 流式页面）
- [ ] **红线：危机安全协议**（优先于功能迭代，人工写死）
- [ ] 第 2 步：跨会话记忆（SQLite：事实 / 未完成 / 情绪）
- [ ] 第 3 步：脱困流程（定性 → 盘点 → 方向卡 → 7 天实验）
- [ ] 第 4 步：每日前沿简报（arXiv / GitHub / HN → 3 条 + 为什么与你有关）
- [ ] 第 5 步：主动找你（21:30 问候、停 3 天轻推、推送到手机）
- [ ] 第 6 步：周复盘

## 现在故意没有的

数据库、跨会话记忆、登录、推送到手机、危机安全协议。
其中危机协议是**红线**，见 [docs/iterations.md](docs/iterations.md)；它不该由模型自由发挥，需要人工写死。
