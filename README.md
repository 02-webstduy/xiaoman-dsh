# 小满

一个接本地模型、常驻服务器、有固定人格的「脱困搭子」。第 1 步只做了一件事：**让你能和它好好说话**。

- 本地 `Qwen2.5-7B-AWQ` 流式对话，首字 ~120ms
- 人格写在 [base.md](src/xiaoman/persona/base.md)，改完刷新即生效
- 会话内记忆（刷新不丢，重启即忘）
- 说「卡住」时先做三分类：没方向 / 有方向但没动力 / 有方向但不知道怎么做
- 被问「上次」会老实说没记住，不编
- 危机语句走固定回应（不经过模型）：先问「你现在安全吗」，再给你配置的联系人和 12356
- 自玩评测（10 个剧本 × 4 轮 × 2 遍）：**68/80 条完全合规（85%）**

> 状态：MVP，第 1 步（对话 + 人格 + 自玩评测）。下一步计划见文末 Roadmap。

## 快速开始

```bash
cd xiaoman
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m xiaoman
# http://127.0.0.1:8765

# 想改模型地址 / 填紧急联系人：复制一份本机配置（不会提交）
cp config.local.example.toml config.local.toml

# 想让它常驻（关掉终端也不停）：
setsid nohup .venv/bin/python -m xiaoman > /tmp/xiaoman.log 2>&1 &
```

模型地址、端口、名字都在 [config.toml](config.toml)；密钥只走环境变量。

## 换成 API 模型（推荐）

第 1 步默认接本地模型，是为了零成本跑通链路。**能力上限在模型，不在代码**：本地 7B 能演好"短回复"，演不好"想清楚"。

```toml
# config.local.toml
[model]
base_url = "https://api.deepseek.com/v1"
model = "deepseek-chat"
api_key_env = "XIAOMAN_API_KEY"
```

```bash
echo 'XIAOMAN_API_KEY=sk-...' >> .env   # .env 不进 git
```

重启后 `/api/health` 会显示当前端点和模型。换模型不用改代码，也不用改人格。

## 版本迭代

| 版本 | 改了什么 | 自玩评测（两轮合并） | 结论 |
|---|---|---|---|
| baseline | 第 1 步交付 | 53/80 = 66% | — |
| round1 | 只给「卡住」加适用范围 | 24/40 = 60% | ❌ 三分类丢了，问号变多 |
| **v2** | 范围限定 + 格式纪律（禁清单/标题/多问号） | **68/80 = 85%** | ✅ 保留，平均 40 字 |
| v3 | 加「别分析」「接上文」 | 61/80 = 76% | ❌ 清单和长回复回来了 |
| v2.1 | 安全协议 + 求助入口 + 本机私密配置 | 不进评测（红线） | ✅ 8 条测试 |

每个版本的失败案例、噪声数据和判断依据在 [docs/iterations.md](docs/iterations.md)；评测方法在 [WORKFLOW.md](WORKFLOW.md)。

## 安全协议（红线）

当你说出「不想活 / 撑不下去 / 活着没意思」这类话时，**它不会调用模型**，而是回一段固定内容：

1. 先问「你现在安全吗？」
2. 给出你配置的联系人（手机、QQ、微信都行）
3. 给出 12356 和 120

这段内容只从 `config.local.toml` 读，不会提交到公开仓库：

```toml
[safety]
contacts = [
  "妈妈 138xxxx0000",
  "阿哲 QQ 12345678",
]
```

页面右上角的「求助」按钮随时能打开同一份信息。它不能替代专业帮助，这是产品边界。

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
| [docs/LANDSCAPE.md](docs/LANDSCAPE.md) | 现有项目调研：知识库 / 日报 / 规划能不能直接拿来用 |

## Roadmap

- [x] 第 1 步：能聊（本地模型 + 人格 + 流式页面）
- [x] **红线：危机安全协议**（固定回应 + 可配置联系人 + 测试）
- [ ] 第 2 步：跨会话记忆（SQLite：事实 / 未完成 / 情绪）
- [ ] 第 3 步：脱困流程（定性 → 盘点 → 方向卡 → 7 天实验）
- [ ] 第 4 步：每日前沿简报（arXiv / GitHub / HN → 3 条 + 为什么与你有关）
- [ ] 第 5 步：主动找你（21:30 问候、停 3 天轻推、推送到手机）
- [ ] 第 6 步：周复盘

## 现在故意没有的

数据库、跨会话记忆、登录、推送到手机。
危机协议已经装上（固定模板，不经过模型）；接下来的功能迭代见 Roadmap。
