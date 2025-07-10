# Main MCP server file
import logging
from datetime import datetime
import sys
import os
import platform
import asyncio

from mcp.server.fastmcp import FastMCP

# Import the interface and the concrete implementation
from src.data_source_interface import FinancialDataSource
from src.baostock_data_source import BaostockDataSource
from src.utils import setup_logging

# 导入各模块工具的注册函数
from src.tools.stock_market import register_stock_market_tools
from src.tools.financial_reports import register_financial_report_tools
from src.tools.indices import register_index_tools
from src.tools.market_overview import register_market_overview_tools
from src.tools.macroeconomic import register_macroeconomic_tools
from src.tools.date_utils import register_date_utils_tools
from src.tools.analysis import register_analysis_tools
from src.tools.technical_indicators import register_technical_indicator_tools
from src.tools.valuation_analysis import register_valuation_analysis_tools

# --- 系统特定配置 ---
def configure_system():
    """配置系统特定的设置"""
    system = platform.system().lower()
    
    if system == 'windows':
        # Windows 特定配置
        if platform.machine().endswith('64'):
            # 64位 Windows
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        os.environ['PYTHONUNBUFFERED'] = '1'
        # baostock 在 Windows TUN 模式下的配置
        os.environ['NO_PROXY'] = 'baostock.com,*.baostock.com,sse.com.cn,szse.cn'

# 应用系统配置
configure_system()

# --- Logging Setup ---
setup_logging(level=logging.WARNING)
logger = logging.getLogger(__name__)

# --- Dependency Injection ---
active_data_source: FinancialDataSource = BaostockDataSource()

# --- Get current date for system prompt ---
current_date = datetime.now().strftime("%Y-%m-%d")

# --- FastMCP App Initialization ---
app = FastMCP(
    server_name="a_share_data_provider",
    port=3000,
    description=f"""今天是{current_date}。提供中国A股市场数据分析工具。此服务提供客观数据分析，用户需自行做出投资决策。数据分析基于公开市场信息，不构成投资建议，仅供参考。

⚠️ 重要说明:
1. 最新交易日不一定是今天，需要从 get_latest_trading_date() 获取
2. 请始终使用 get_latest_trading_date() 工具获取实际当前最近的交易日，不要依赖训练数据中的日期认知
3. 当分析"最近"或"近期"市场情况时，必须首先调用 get_market_analysis_timeframe() 工具确定实际的分析时间范围
4. 任何涉及日期的分析必须基于工具返回的实际数据，不得使用过时或假设的日期
""")

# --- 注册各模块的工具 ---
register_stock_market_tools(app, active_data_source)
register_financial_report_tools(app, active_data_source)
register_index_tools(app, active_data_source)
register_market_overview_tools(app, active_data_source)
register_macroeconomic_tools(app, active_data_source)
register_date_utils_tools(app, active_data_source)
register_analysis_tools(app, active_data_source)
register_technical_indicator_tools(app, active_data_source)
register_valuation_analysis_tools(app, active_data_source)

# --- Main Execution Block ---
if __name__ == "__main__":
    logger.info(f"Starting A-Share MCP Server... Today is {current_date}")
    logger.info(f"Running on {platform.system()} {platform.machine()}")
    
    try:
        # 使用 streamable-http 传输运行服务器
        app.run(transport="streamable-http")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
