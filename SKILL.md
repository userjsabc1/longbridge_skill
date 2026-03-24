---
name: longbridge-terminal
description: >
  Longbridge 股票交易终端 CLI 技能，覆盖港股(HK)、美股(US)、A股(SH/SZ)、新加坡(SG)
  全部 OpenAPI 端点：实时行情、深度盘口、K线、期权、窝轮、新闻公告、社区话题、
  账户余额、持仓、下单/改单/撤单、资金流水、自选股管理等。
  当用户提到"股票行情"、"查股价"、"K线"、"期权链"、"下单买入"、"卖出"、"持仓"、
  "账户余额"、"自选股"、"longbridge"、"长桥"、"港股"、"美股"、"A股"、"交易"、
  "盘口深度"、"资金流向"、"市场温度"、"新闻公告"、"SEC filing"、
  或任何涉及股票代码（如 TSLA.US、700.HK、600519.SH）的查询与交易场景，必须触发本技能。
---

# longbridge-terminal

> **来源**：[longbridge/longbridge-terminal](https://github.com/longbridge/longbridge-terminal)（MIT）
>
> AI-native CLI，封装了 Longbridge OpenAPI 全部端点，支持表格和 JSON 两种输出格式，
> 适合脚本调用、AI Agent tool-calling 和日常交易工作流。

---

## 文件结构

```
/var/minis/skills/longbridge-terminal/
├── SKILL.md
├── scripts/
│   └── lb.py               # 辅助脚本：批量查询、K线CSV导出、持仓盈亏快照
└── references/
    ├── quote-commands.md    # 行情类命令详细参考
    ├── trade-commands.md    # 交易类命令详细参考
    └── watchlist-commands.md # 自选股命令详细参考
```

---

## 安装

longbridge CLI 是一个独立的 Rust 二进制。当前环境（Alpine Linux arm64）可通过安装脚本自动安装：

```bash
if ! which longbridge > /dev/null 2>&1; then
  curl -sSL https://github.com/longbridge/longbridge-terminal/raw/main/install | sh
fi
```

安装脚本会自动检测平台（Linux/macOS）和架构（arm64/amd64），下载对应二进制到 `/usr/local/bin/longbridge`。支持 musl（Alpine）环境。

安装后验证：
```bash
longbridge -h
```

---

## 认证方式

使用 OAuth 2.0 浏览器授权，无需手动管理 Token。

```bash
longbridge login    # 打开浏览器完成 OAuth 授权，Token 保存到 ~/.longbridge/terminal/.openapi-session
longbridge logout   # 清除 Token
longbridge check    # 验证 Token、地区检测、API 连通性
```

Token 在 CLI 和 TUI 之间共享。登录一次后所有命令无需重复认证。

> CLI 每次启动会后台探测 `geotest.lbkrs.com` 自动检测是否在中国大陆，
> 结果缓存在 `~/.longbridge-openapi/region-cache`，如检测到大陆则自动使用 CN 端点。

### 在 Minis 环境中使用

1. 确认 `longbridge` 已安装（`which longbridge`）
2. 如果尚未登录，执行 `longbridge login` 完成 OAuth 授权
3. 用 `longbridge check` 验证连通性
4. 之后所有命令直接调用即可

---

## 代码格式

所有股票代码格式：`<CODE>.<MARKET>`

| 市场 | 示例 |
|------|------|
| `HK`（港股） | `700.HK`（腾讯）、`9988.HK`（阿里） |
| `US`（美股） | `TSLA.US`、`AAPL.US`、`NVDA.US` |
| `SH`（沪市） | `600519.SH`（贵州茅台） |
| `SZ`（深市） | `000001.SZ`（平安银行） |

---

## 输出格式

```bash
--format table   # 人类可读的表格（默认）
--format json    # 机器可读的 JSON，适合 AI Agent 和管道处理
```

AI Agent 调用时建议始终加 `--format json`。

---

## 快速开始

```bash
# 诊断连通性
longbridge check

# 实时行情
longbridge quote TSLA.US 700.HK AAPL.US

# 日K线（最近100根）
longbridge kline TSLA.US --period day --count 100

# 历史K线（按日期范围）
longbridge kline-history TSLA.US --start 2024-01-01 --end 2024-12-31

# 盘口深度
longbridge depth TSLA.US

# 新闻
longbridge news TSLA.US
longbridge news-detail <id>

# SEC 公告
longbridge filings AAPL.US
longbridge filing-detail AAPL.US <id>

# 持仓
longbridge positions

# 今日订单
longbridge orders

# 限价买入
longbridge buy TSLA.US 100 --price 250.00

# 市价卖出
longbridge sell AAPL.US 50 --order-type MO

# 自选股
longbridge watchlist
longbridge watchlist create "AI Stocks"
```

---

## 命令分类速查

### 行情类

| 命令 | 说明 |
|------|------|
| `quote` | 实时行情（支持多个代码） |
| `depth` | Level 2 盘口深度 |
| `brokers` | 经纪商队列（仅港股） |
| `trades` | 逐笔成交 |
| `intraday` | 分钟级分时数据 |
| `kline` | K线（最近N根） |
| `kline-history` | 历史K线（按日期范围） |
| `static` | 证券基本信息 |
| `calc-index` | 财务指标（PE/PB/EPS等） |
| `capital-flow` | 资金流向时序 |
| `capital-dist` | 资金分布快照 |
| `market-temp` | 市场温度指数（0-100） |
| `trading-session` | 交易时段 |
| `trading-days` | 交易日历 |
| `security-list` | 全部上市证券 |
| `participants` | 做市商/经纪商列表 |

### 新闻与公告

| 命令 | 说明 |
|------|------|
| `news` | 个股新闻列表 |
| `news-detail` | 新闻全文（Markdown） |
| `filings` | 监管公告列表 |
| `filing-detail` | 公告全文（支持多文件） |
| `topics` | 社区讨论话题 |
| `topic-detail` | 话题全文 |

### 期权与窝轮

| 命令 | 说明 |
|------|------|
| `option-quote` | 期权实时行情 |
| `option-chain` | 期权链（到期日/行权价） |
| `warrant-quote` | 窝轮实时行情 |
| `warrant-list` | 关联窝轮列表 |
| `warrant-issuers` | 窝轮发行商 |

### 交易类

| 命令 | 说明 |
|------|------|
| `orders` | 今日/历史订单 |
| `order` | 单笔订单详情 |
| `executions` | 成交记录 |
| `buy` | 买入下单 |
| `sell` | 卖出下单 |
| `cancel` | 撤单 |
| `replace` | 改单 |
| `balance` | 账户余额 |
| `cash-flow` | 资金流水 |
| `positions` | 股票持仓 |
| `fund-positions` | 基金持仓 |
| `margin-ratio` | 保证金比例 |
| `max-qty` | 最大可交易数量 |

### 自选股

| 命令 | 说明 |
|------|------|
| `watchlist` | 查看自选股分组 |
| `watchlist create` | 创建分组 |
| `watchlist update` | 添加/移除/重命名 |
| `watchlist delete` | 删除分组 |

---

## 参考文档

根据用户请求的类型，加载对应的参考文档获取完整参数说明：

- 行情相关（quote/depth/kline/期权/窝轮/新闻等）→ [references/quote-commands.md](references/quote-commands.md)
- 交易相关（orders/buy/sell/positions/balance等）→ [references/trade-commands.md](references/trade-commands.md)
- 自选股相关（watchlist CRUD）→ [references/watchlist-commands.md](references/watchlist-commands.md)

---

## 辅助脚本

对于单个命令，直接调用 `longbridge xxx --format json` 即可。
`scripts/lb.py` 用于需要聚合、批处理或格式转换的场景：

```bash
# 检查 CLI 是否安装且已登录
python3 /var/minis/skills/longbridge-terminal/scripts/lb.py check

# 批量行情（自动计算涨跌幅，聚合表格）
python3 /var/minis/skills/longbridge-terminal/scripts/lb.py quote TSLA.US 700.HK AAPL.US NVDA.US

# K线导出 CSV（方便后续分析）
python3 /var/minis/skills/longbridge-terminal/scripts/lb.py kline TSLA.US --period day --count 30 --csv

# 持仓盈亏快照（拉持仓+实时行情，计算浮动盈亏）
python3 /var/minis/skills/longbridge-terminal/scripts/lb.py snapshot
```

---

## 注意事项

- Longbridge OpenAPI 限流：最多 10 次/秒，SDK 自动刷新 OAuth Token
- 写操作（买入/卖出/撤单/改单）会弹出确认提示，请谨慎操作
- 需要 [Longbridge 账户](https://open.longbridge.com) 才能使用
- 首次登录需要浏览器环境完成 OAuth 授权
- 市场温度指数范围 0-100，越高越偏多头情绪
