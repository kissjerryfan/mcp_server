<div align="center">

# 📊 a-share-mcp 📈

<img src="https://img.shields.io/badge/A股数据-MCP%20工具-E6162D?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB2ZXJzaW9uPSIxLjEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiB2aWV3Qm94PSIwIDAgMjQgMjQiPg0KPHBhdGggZmlsbD0iI2ZmZiIgZD0iTTggMTAuOGMwIDAgMC44LTEuNSAyLjQtMS41IDEuNyAwIDIuOCAxLjUgNC44IDEuNSAxLjcgMCAyLjgtMC42IDIuOC0wLjZ2LTIuMmMwIDAtMS4xIDEuMS0yLjggMS4xLTIgMC0zLjEtMS41LTQuOC0xLjUtMS42IDAtMi40IDAuOS0yLjQgMC45djIuM3pNOCAxNC44YzAgMCAwLjgtMS41IDIuNC0xLjUgMS43IDAgMi44IDEuNSA0LjggMS41IDEuNyAwIDIuOC0wLjYgMi44LTAuNnYtMi4yYzAgMC0xLjEgMS4xLTIuOCAxLjEtMiAwLTMuMS0xLjUtNC44LTEuNS0xLjYgMC0yLjQgMC45LTIuNCAwLjl2Mi4zeiI+PC9wYXRoPg0KPC9zdmc+">

[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square&logo=opensourceinitiative)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Package Manager](https://img.shields.io/badge/uv-package%20manager-5A45FF?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDEuNUwxIDEyLjVIMjNMMTIgMS41WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTEyIDIyLjVMMSAxMS41SDIzTDEyIDIyLjVaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-Protocol-FF6B00?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0Ij48cGF0aCBkPSJNMTIgMkM2LjQ4NiAyIDIgNi40ODYgMiAxMnM0LjQ4NiAxMCAxMCAxMHMxMC00LjQ4NiAxMC0xMFMxNy41MTQgMiAxMiAyem0tMSAxNHY1LjI1QTguMDA4IDguMDA4IDAgMCAxIDQuNzUgMTZ6bTIgMGg2LjI1QTguMDA4IDguMDA4IDAgMCAxIDEzIDE2em0xLTJWOWg1LjI1QTguMDIgOC4wMiAwIDAAxIDE0IDE0em0tMiAwSDYuNzVBOC4wMiA4LjAyIDAgMDEgMTEgMTR6bTAtNlY0Ljc1QTguMDA4IDguMDA4IDAgMCAxIDE5LjI1IDh6TTEwIDh2NUg0Ljc1QTguMDA3IDguMDA3IDAgMCAxIDEwIDh6IiBmaWxsPSJ3aGl0ZSIvPjwvc3ZnPg==)](https://github.com/model-context-protocol/mcp-spec)

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,15,20,24&height=200&section=header&text=A%20股%20MCP&fontSize=80&fontAlignY=35&desc=基于%20Model%20Context%20Protocol%20(MCP)&descAlignY=60&animation=fadeIn" />

</div>
A股mcp。

本项目是一个基于专注于 A 股市场的 MCP 服务器，它提供股票基本信息、历史 K 线数据、财务指标、宏观经济数据等多种查询功能，理论上来说，可以回答有关 A 股市场的任何问题，无论是针对大盘还是特定股票。

<div align="center">
<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%">
</div>

## 项目结构

```
a_share_mcp/
│
├── mcp_server.py           # 主服务器入口文件
├── pyproject.toml          # 项目依赖配置
├── README.md               # 项目说明文档
│
├── docs/                   # 项目文档
│   ├── baostock_com.md     # Baostock API文档
│   ├── mcp_server_docs.md  # 服务器文档
│   └── dev_docs/           # 开发文档
│       ├── AppFlow.md
│       ├── ImplementationPlan.md
│       └── PRD.md
│
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── baostock_data_source.py   # Baostock数据源实现
│   ├── data_source_interface.py  # 数据源接口定义
│   ├── utils.py                  # 通用工具函数
│   │
│   ├── formatting/         # 数据格式化模块
│   │   ├── __init__.py
│   │   └── markdown_formatter.py  # Markdown格式化工具
│   │
│   └── tools/              # MCP工具模块
│       ├── __init__.py
│       ├── base.py                # 基础工具函数
│       ├── stock_market.py        # 股票市场数据工具
│       ├── financial_reports.py   # 财务报表工具
│       ├── indices.py             # 指数相关工具
│       ├── market_overview.py     # 市场概览工具
│       ├── macroeconomic.py       # 宏观经济数据工具
│       ├── technical_indicators.py # 技术指标工具
│       ├── valuation_analysis.py  # 估值分析工具
│       ├── date_utils.py          # 日期工具
│       └── analysis.py            # 分析工具
│
└── resource/               # 资源文件
    └── img/                # 图片资源
        ├── img_1.png       # CherryStudio配置示例
        └── img_2.png       # CherryStudio配置示例
```

<div align="center">
<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%">
</div>

## 功能特点

<div align="center">
<table>
  <tr>
    <td align="center"><img src="https://img.icons8.com/fluency/48/null/stocks-growth.png" width="30px"/><br><b>股票基础数据</b></td>
    <td align="center"><img src="https://img.icons8.com/fluency/48/null/line-chart.png" width="30px"/><br><b>历史行情数据</b></td>
    <td align="center"><img src="https://img.icons8.com/fluency/48/null/bonds.png" width="30px"/><br><b>财务报表数据</b></td>
  </tr>
  <tr>
    <td align="center"><img src="https://img.icons8.com/fluency/48/null/economic-improvement.png" width="30px"/><br><b>宏观经济数据</b></td>
    <td align="center"><img src="https://img.icons8.com/fluency/48/null/statistics.png" width="30px"/><br><b>技术指标分析</b></td>
    <td align="center"><img src="https://img.icons8.com/fluency/48/null/fine-print.png" width="30px"/><br><b>估值分析工具</b></td>
  </tr>
</table>
</div>

## 系统要求

| 项目 | 要求 | 说明 |
|:---|:---|:---|
| **Python版本** | 3.10+ | 推荐使用最新稳定版 |
| **操作系统** | Windows/Linux/MacOS | 全平台支持 |
| **数据源** | Baostock (免费) | 无需付费API，感谢Baostock |
| **可选依赖** | pandas-ta | 用于高级技术指标计算 |
| **内存要求** | 推荐2GB+ | 用于大数据量处理 |

## 数据更新时间

> 以下是 Baostock 官方数据更新时间，请注意查询最新数据时的时间点 [Baostock 官网](http://baostock.com/baostock/index.php/%E9%A6%96%E9%A1%B5)

**每日数据更新时间：**

- 当前交易日 17:30，完成日 K 线数据入库
- 当前交易日 18:00，完成复权因子数据入库
- 第二自然日 11:00，完成分钟 K 线数据入库
- 第二自然日 1:30，完成前交易日"其它财务报告数据"入库
- 周六 17:30，完成周线数据入库

**每周数据更新时间：**

- 每周一下午，完成上证 50 成份股、沪深 300 成份股、中证 500 成份股信息数据入库

> 所以说，在交易日的当天，如果是在 17:30 之前询问当天的数据，是无法获取到的。

## 快速开始

### 1. 环境要求
- Python 3.10 或更高版本
- pip 包管理器

### 2. 安装依赖

在项目根目录下执行：

```bash
# 克隆项目
git clone https://github.com/kissjerryfan/mcp_server.git
cd mcp_server
```

```bash
# 安装基础依赖
pip install -r requirements.txt
```

```bash
# 可选：安装技术指标分析库（用于高级技术指标计算）
pip install pandas-ta
```

### 3. 运行服务器

```bash
python mcp_server.py
```

服务器启动后，将在端口3000上运行，并支持MCP协议连接。

### 4. 配置AI助手

将以下配置添加到您的AI助手（如Claude Desktop、CherryStudio等）的MCP配置中：

```json
{
  "mcpServers": {
    "a-share-mcp": {
      "command": "python",
      "args": ["path/to/your/mcp_server.py"],
      "cwd": "path/to/your/project"
    }
  }
}
```



## 工具列表

该 MCP 服务器提供以下工具：

<div align="center">
  <details>
    <summary><b>🔍 展开查看全部工具</b></summary>
    <br>
    <table>
      <tr>
        <th>🏛️ 股票市场数据</th>
        <th>📊 财务报表数据</th>
        <th>🔎 市场概览数据</th>
      </tr>
      <tr valign="top">
        <td>
          <ul>
            <li><code>get_historical_k_data</code></li>
            <li><code>get_stock_basic_info</code></li>
            <li><code>get_dividend_data</code></li>
            <li><code>get_adjust_factor_data</code></li>
          </ul>
        </td>
        <td>
          <ul>
            <li><code>get_profit_data</code></li>
            <li><code>get_operation_data</code></li>
            <li><code>get_growth_data</code></li>
            <li><code>get_balance_data</code></li>
            <li><code>get_cash_flow_data</code></li>
            <li><code>get_dupont_data</code></li>
          </ul>
        </td>
        <td>
          <ul>
            <li><code>get_trade_dates</code></li>
            <li><code>get_all_stock</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <th>📈 指数相关数据</th>
        <th>🌐 宏观经济数据</th>
        <th>⏰ 日期工具 & 分析</th>
      </tr>
      <tr valign="top">
        <td>
          <ul>
            <li><code>get_stock_industry</code></li>
            <li><code>get_sz50_stocks</code></li>
            <li><code>get_hs300_stocks</code></li>
            <li><code>get_zz500_stocks</code></li>
          </ul>
        </td>
        <td>
          <ul>
            <li><code>get_deposit_rate_data</code></li>
            <li><code>get_loan_rate_data</code></li>
            <li><code>get_required_reserve_ratio_data</code></li>
            <li><code>get_money_supply_data_month</code></li>
            <li><code>get_money_supply_data_year</code></li>
            <li><code>get_shibor_data</code></li>
          </ul>
        </td>
        <td>
          <ul>
            <li><code>get_latest_trading_date</code></li>
            <li><code>get_stock_analysis</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <th>📊 技术指标分析</th>
        <th>💰 估值分析工具</th>
        <th>🔧 其他工具</th>
      </tr>
      <tr valign="top">
        <td>
          <ul>
            <li><code>get_technical_indicators</code></li>
            <li><code>get_moving_averages</code></li>
            <li><code>calculate_bollinger_bands</code></li>
            <li><code>calculate_macd</code></li>
            <li><code>calculate_rsi</code></li>
          </ul>
        </td>
        <td>
          <ul>
            <li><code>get_valuation_metrics</code></li>
            <li><code>calculate_peg_ratio</code></li>
            <li><code>calculate_ddm_valuation</code></li>
            <li><code>calculate_dcf_valuation</code></li>
            <li><code>get_comparable_analysis</code></li>
          </ul>
        </td>
        <td>
          <ul>
            <li><code>get_market_analysis_timeframe</code></li>
            <li><code>format_trading_calendar</code></li>
            <li><code>validate_stock_code</code></li>
          </ul>
        </td>
      </tr>
    </table>
  </details>
</div>

## MCP工具接口说明

本服务器通过MCP协议向AI助手提供A股数据查询工具。

### 📚 完整接口文档

详细的工具接口说明请参考：**[DOCUMENTS.md](./DOCUMENTS.md)**

该文档包含：
- 🔧 **所有工具函数的详细参数说明**
- 📝 **输入输出格式规范**  
- 💡 **使用示例和最佳实践**
- 🏗️ **各模块功能架构说明**

### 🚀 快速接口预览

```python
# 基础数据查询
get_stock_basic_info(code="sh.600519")
get_historical_k_data(code="sz.000001", start_date="2024-01-01", end_date="2024-01-31")

# 财务分析
get_profit_data(code="sz.002594", year="2023", quarter="4")
get_balance_data(code="sz.002594", year="2023", quarter="4")

# 技术指标
get_technical_indicators(code="sz.300750", start_date="2024-01-01", end_date="2024-01-31")
calculate_risk_metrics(code="sh.600519", period="1Y")

# 估值分析
get_valuation_metrics(code="sz.000858")
calculate_dcf_valuation(code="sh.600519", years_back=5)
calculate_ddm_valuation(code="sh.600000", discount_rate=0.10)

# 市场数据
get_all_stock()
get_hs300_stocks()
get_trade_dates(start_date="2024-01-01", end_date="2024-12-31")

# 宏观经济
get_deposit_rate_data()
get_shibor_data(start_date="2024-01-01", end_date="2024-12-31")
```

## 功能亮点

- **🚀 零配置启动**：基于免费Baostock数据源，无需付费API
- **🎯 AI原生设计**：专为AI助手优化的查询接口和数据格式
- **📊 全面数据覆盖**：涵盖基本面、技术面、宏观面等9大维度
- **⚡ 实时更新**：支持最新交易日数据查询
- **🔧 模块化架构**：易于扩展和定制化开发

## 贡献指南

欢迎提交 Issue 或 Pull Request 来帮助改进项目。贡献前请先查看现有 Issue 和文档。

## 许可证

本项目采用 MIT 许可证 - 详情请查看 LICENSE 文件

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,15,20,24&section=footer&height=100&animation=fadeIn" />
</div>
