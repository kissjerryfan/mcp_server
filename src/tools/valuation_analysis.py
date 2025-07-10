"""
Valuation analysis tools for MCP server.
Provides comprehensive valuation metrics including P/E, P/B, P/S, PEG, DCF and DDM analysis.
"""
import logging
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP
from src.data_source_interface import FinancialDataSource, NoDataFoundError, LoginError, DataSourceError
from src.formatting.markdown_formatter import format_df_to_markdown

logger = logging.getLogger(__name__)


def _calculate_ddm_value(
    current_dividend: float,
    growth_rates: List[Tuple[float, int]],
    discount_rate: float
) -> Dict[str, float]:
    """
    Calculate DDM (Dividend Discount Model) valuation.
    
    Args:
        current_dividend: Current annual dividend
        growth_rates: List of (growth_rate, years) tuples for different growth phases
        discount_rate: Required rate of return
    
    Returns:
        Dictionary with DDM components and results
    """
    if current_dividend <= 0:
        return {"error": "Current dividend must be positive"}
    
    total_value = 0
    current_year = 0
    projected_dividends = []
    
    # Calculate present value for each growth phase
    current_div = current_dividend
    for growth_rate, years in growth_rates:
        for year in range(years):
            current_year += 1
            current_div *= (1 + growth_rate)
            present_value = current_div / ((1 + discount_rate) ** current_year)
            total_value += present_value
            projected_dividends.append((current_year, current_div, present_value))
    
    # Calculate terminal value if there's stable growth
    if growth_rates[-1][0] < discount_rate:  # Only if growth rate is less than discount rate
        terminal_value = (current_div * (1 + growth_rates[-1][0])) / (discount_rate - growth_rates[-1][0])
        terminal_pv = terminal_value / ((1 + discount_rate) ** current_year)
        total_value += terminal_pv
    else:
        terminal_pv = 0
    
    return {
        "intrinsic_value": total_value,
        "projected_dividends": projected_dividends,
        "terminal_value": terminal_pv,
        "total_years": current_year
    }


def _calculate_dcf_value(cash_flows: List[float], terminal_growth_rate: float = 0.025, 
                        discount_rate: float = 0.10, forecast_years: int = 5) -> Dict[str, float]:
    """
    Calculate DCF (Discounted Cash Flow) valuation.
    
    Args:
        cash_flows: Historical cash flows for extrapolation
        terminal_growth_rate: Long-term growth rate assumption (default 2.5%)
        discount_rate: Discount rate/WACC (default 10%)
        forecast_years: Forecast period in years (default 5)
    
    Returns:
        Dictionary with DCF components and results
    """
    if len(cash_flows) < 2:
        return {"error": "Insufficient cash flow data for DCF calculation"}
    
    # Calculate average growth rate from historical data
    cash_flows = [cf for cf in cash_flows if cf > 0]  # Filter positive cash flows
    if len(cash_flows) < 2:
        return {"error": "Insufficient positive cash flow data"}
    
    # Calculate compound annual growth rate (CAGR)
    historical_growth = (cash_flows[-1] / cash_flows[0]) ** (1 / (len(cash_flows) - 1)) - 1
    
    # Use conservative growth rate
    forecast_growth_rate = min(historical_growth, 0.15)  # Cap at 15%
    
    # Project future cash flows
    projected_cash_flows = []
    last_cf = cash_flows[-1]
    
    for year in range(1, forecast_years + 1):
        next_cf = last_cf * (1 + forecast_growth_rate) ** year
        projected_cash_flows.append(next_cf)
    
    # Calculate terminal value
    terminal_cf = projected_cash_flows[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_cf / (discount_rate - terminal_growth_rate)
    
    # Discount all cash flows to present value
    pv_cash_flows = []
    for i, cf in enumerate(projected_cash_flows, 1):
        pv = cf / (1 + discount_rate) ** i
        pv_cash_flows.append(pv)
    
    pv_terminal = terminal_value / (1 + discount_rate) ** forecast_years
    
    enterprise_value = sum(pv_cash_flows) + pv_terminal
    
    return {
        "enterprise_value": enterprise_value,
        "pv_cash_flows": sum(pv_cash_flows),
        "pv_terminal_value": pv_terminal,
        "terminal_value": terminal_value,
        "forecast_growth_rate": forecast_growth_rate,
        "historical_growth": historical_growth,
        "projected_cash_flows": projected_cash_flows
    }


def register_valuation_analysis_tools(app: FastMCP, active_data_source: FinancialDataSource):
    """
    Register valuation analysis tools with the MCP app.
    
    Args:
        app: The FastMCP app instance
        active_data_source: The active financial data source
    """

    @app.tool()
    def get_valuation_metrics(
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        获取股票的估值指标数据，包括市盈率(P/E)、市净率(P/B)、市销率(P/S)等的实时数据和历史趋势。

        Args:
            code: 股票代码，如'sh.600000'
            start_date: 开始日期，格式'YYYY-MM-DD'，默认为最近1年
            end_date: 结束日期，格式'YYYY-MM-DD'，默认为当前日期

        Returns:
            包含各种估值指标的Markdown表格和趋势分析
        """
        logger.info(f"Tool 'get_valuation_metrics' called for {code}")
        
        try:
            # 设置默认日期范围
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # 获取包含估值指标的历史数据
            df = active_data_source.get_historical_k_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjust_flag="3",
                fields=["date", "code", "close", "peTTM", "pbMRQ", "psTTM", "pcfNcfTTM"]
            )
            
            if df.empty:
                return f"Error: No valuation data found for {code}"
            
            # 数据预处理
            df['date'] = pd.to_datetime(df['date'])
            numeric_cols = ['close', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 过滤掉无效数据
            df = df.dropna(subset=['close'])
            
            # 获取股票基本信息
            basic_info = active_data_source.get_stock_basic_info(code=code)
            stock_name = basic_info['code_name'].values[0] if not basic_info.empty else code
            
            # 生成分析报告
            report = f"# {stock_name} ({code}) 估值指标分析\n\n"
            report += f"**分析期间**: {start_date} 至 {end_date}\n"
            report += f"**数据点数**: {len(df)} 个交易日\n\n"
            
            # 当前估值指标
            latest_data = df.iloc[-1]
            report += "## 最新估值指标\n"
            report += f"- **收盘价**: {latest_data['close']:.2f}\n"
            
            if pd.notna(latest_data.get('peTTM')):
                report += f"- **市盈率TTM**: {latest_data['peTTM']:.2f}\n"
            if pd.notna(latest_data.get('pbMRQ')):
                report += f"- **市净率MRQ**: {latest_data['pbMRQ']:.2f}\n"
            if pd.notna(latest_data.get('psTTM')):
                report += f"- **市销率TTM**: {latest_data['psTTM']:.2f}\n"
            if pd.notna(latest_data.get('pcfNcfTTM')):
                report += f"- **市现率TTM**: {latest_data['pcfNcfTTM']:.2f}\n"
            
            # 历史趋势分析
            report += "\n## 估值指标趋势分析\n"
            
            for metric in ['peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']:
                if metric in df.columns:
                    values = df[metric].dropna()
                    if len(values) > 0:
                        current_val = values.iloc[-1]
                        avg_val = values.mean()
                        min_val = values.min()
                        max_val = values.max()
                        
                        metric_name = {
                            'peTTM': '市盈率TTM',
                            'pbMRQ': '市净率MRQ', 
                            'psTTM': '市销率TTM',
                            'pcfNcfTTM': '市现率TTM'
                        }[metric]
                        
                        deviation = ((current_val / avg_val) - 1) * 100 if avg_val != 0 else 0
                        percentile = (values <= current_val).mean() * 100
                        
                        report += f"\n### {metric_name}\n"
                        report += f"- 当前值: {current_val:.2f}\n"
                        report += f"- 历史均值: {avg_val:.2f}\n"
                        report += f"- 历史区间: {min_val:.2f} - {max_val:.2f}\n"
                        report += f"- 相对均值: {deviation:+.1f}%\n"
                        report += f"- 历史分位: {percentile:.1f}%\n"
            
            # 最近30天数据表格
            recent_df = df.tail(30)[['date', 'close', 'peTTM', 'pbMRQ', 'psTTM']].copy()
            recent_df = recent_df.round(4)
            
            report += "\n## 最近30个交易日估值数据\n"
            report += format_df_to_markdown(recent_df)
            
            logger.info(f"Successfully generated valuation metrics for {code}")
            return report
            
        except Exception as e:
            logger.exception(f"Error generating valuation metrics for {code}: {e}")
            return f"Error: Failed to generate valuation metrics: {e}"

    @app.tool()
    def calculate_peg_ratio(
        code: str,
        year: str,
        quarter: int
    ) -> str:
        """
        计算PEG比率（市盈率相对盈利增长比率），PEG = PE / 净利润增长率。

        Args:
            code: 股票代码，如'sh.600000'
            year: 4位数字年份，如'2024'
            quarter: 季度，1、2、3或4

        Returns:
            包含PEG比率计算和分析的详细报告
        """
        logger.info(f"Tool 'calculate_peg_ratio' called for {code}, {year}Q{quarter}")
        
        try:
            # 获取当前估值数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            valuation_df = active_data_source.get_historical_k_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                fields=["date", "close", "peTTM"]
            )
            
            # 获取成长能力数据
            growth_data = active_data_source.get_growth_data(
                code=code, year=year, quarter=quarter
            )
            
            if valuation_df.empty or growth_data.empty:
                return f"Error: Unable to fetch required data for PEG calculation"
            
            # 获取股票基本信息
            basic_info = active_data_source.get_stock_basic_info(code=code)
            stock_name = basic_info['code_name'].values[0] if not basic_info.empty else code
            
            # 获取最新PE
            valuation_df['peTTM'] = pd.to_numeric(valuation_df['peTTM'], errors='coerce')
            latest_pe = valuation_df['peTTM'].dropna().iloc[-1] if not valuation_df['peTTM'].dropna().empty else None
            
            # 获取净利润增长率
            growth_columns = ['YOYNI', 'YOYProfit', 'YOYEPSBasic']  # 净利润增长率相关字段
            growth_rate = None
            growth_field = None
            
            for col in growth_columns:
                if col in growth_data.columns:
                    rate = pd.to_numeric(growth_data[col].iloc[0], errors='coerce')
                    if pd.notna(rate) and rate != 0:
                        growth_rate = rate
                        growth_field = col
                        break
            
            # 生成报告
            report = f"# {stock_name} ({code}) PEG比率分析\n\n"
            report += f"**分析时点**: {year}年第{quarter}季度\n\n"
            
            if latest_pe is None:
                report += "❌ **无法计算PEG**: 缺少有效的市盈率数据\n"
                return report
            
            if growth_rate is None:
                report += "❌ **无法计算PEG**: 缺少有效的净利润增长率数据\n"
                report += f"- 当前市盈率TTM: {latest_pe:.2f}\n"
                return report
            
            # 计算PEG比率
            peg_ratio = latest_pe / growth_rate if growth_rate != 0 else float('inf')
            
            report += "## PEG比率计算结果\n"
            report += f"- **市盈率TTM**: {latest_pe:.2f}\n"
            report += f"- **净利润增长率**: {growth_rate:.2f}%\n"
            report += f"- **PEG比率**: {peg_ratio:.3f}\n\n"
            
            # PEG比率解读
            report += "## PEG比率解读\n"
            if peg_ratio < 0:
                report += "⚠️ **负增长**: 公司净利润出现负增长，PEG比率失去参考意义\n"
            elif peg_ratio < 0.5:
                report += "🟢 **低估**: PEG < 0.5，股票可能被严重低估\n"
            elif peg_ratio <= 1.0:
                report += "🟡 **合理**: 0.5 ≤ PEG ≤ 1.0，估值相对合理\n"
            elif peg_ratio <= 1.5:
                report += "🟠 **偏高**: 1.0 < PEG ≤ 1.5，估值偏高但可接受\n"
            elif peg_ratio <= 2.0:
                report += "🔴 **高估**: 1.5 < PEG ≤ 2.0，股票可能被高估\n"
            else:
                report += "🔴 **严重高估**: PEG > 2.0，股票可能被严重高估\n"
            
            report += "\n## 说明\n"
            report += "- PEG比率结合了估值和成长性，比单纯的PE更全面\n"
            report += "- 一般认为PEG=1为合理估值的分水岭\n"
            report += f"- 本次计算基于{growth_field}字段的增长率数据\n"
            report += "- PEG分析应结合行业特点和市场环境综合判断\n"
            
            logger.info(f"Successfully calculated PEG ratio for {code}")
            return report
            
        except Exception as e:
            logger.exception(f"Error calculating PEG ratio for {code}: {e}")
            return f"Error: Failed to calculate PEG ratio: {e}"

    @app.tool()
    def calculate_ddm_valuation(
        code: str,
        years_back: int = 5,
        discount_rate: float = 0.10,
        terminal_growth_rate: float = 0.025
    ) -> str:
        """
        使用股息贴现模型(DDM)计算股票的内在价值。

        Args:
            code: 股票代码，如'sh.600000'
            years_back: 使用多少年的历史数据来计算增长率，默认5年
            discount_rate: 贴现率/要求回报率，默认10%
            terminal_growth_rate: 永续增长率，默认2.5%

        Returns:
            DDM估值分析报告（Markdown格式）
        """
        try:
            # 获取历史分红数据
            current_year = datetime.now().year
            dividend_data = []
            
            # 收集多年的分红数据
            for year in range(current_year - years_back, current_year + 1):
                try:
                    year_data = active_data_source.get_dividend_data(
                        code=code,
                        year=str(year)
                    )
                    if not year_data.empty:
                        year_data['year'] = year
                        dividend_data.append(year_data)
                except (NoDataFoundError, DataSourceError):
                    continue
            
            if not dividend_data:
                return f"无法获取 {code} 的分红数据。"
            
            # 合并所有年份的数据
            dividend_df = pd.concat(dividend_data, ignore_index=True)
            
            # 提取每股分红数据
            annual_dividends = []
            years = []
            
            for year in range(current_year - years_back, current_year + 1):
                year_data = dividend_df[dividend_df['year'] == year]
                if not year_data.empty:
                    # 尝试不同的字段名
                    dividend_fields = ['dividendPerShare', 'dividend_per_share', 'dividendsPerShare', 'div_cash_paid']
                    total_dividend = 0
                    for field in dividend_fields:
                        if field in year_data.columns:
                            try:
                                # 将所有分红累加（可能一年有多次分红）
                                values = year_data[field].apply(lambda x: float(x) if pd.notna(x) else 0)
                                total_dividend = values.sum()
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    if total_dividend > 0:
                        annual_dividends.append(total_dividend)
                        years.append(year)
            
            if len(annual_dividends) < 2:
                return f"无法获取足够的分红数据来进行 DDM 估值分析。"
            
            # 计算历史增长率
            growth_rates = []
            for i in range(1, len(annual_dividends)):
                if annual_dividends[i-1] > 0:  # 避免除以零
                    growth_rate = (annual_dividends[i] / annual_dividends[i-1]) - 1
                    growth_rates.append(growth_rate)
            
            # 使用平均增长率作为预测增长率
            if growth_rates:
                historical_growth = sum(growth_rates) / len(growth_rates)
                # 限制增长率在合理范围内
                forecast_growth_rate = max(min(historical_growth, 0.20), 0.01)
            else:
                forecast_growth_rate = 0.05  # 默认5%增长率
            
            # 获取最新股息
            latest_dividend = annual_dividends[-1]
            
            # 计算DDM估值
            # 使用两阶段DDM模型：
            # 1. 前5年使用预测增长率
            # 2. 之后使用永续增长率
            forecast_years = 5
            pv_dividends = []
            
            # 第一阶段：预测增长期
            for i in range(1, forecast_years + 1):
                future_dividend = latest_dividend * (1 + forecast_growth_rate) ** i
                present_value = future_dividend / (1 + discount_rate) ** i
                pv_dividends.append(present_value)
            
            # 第二阶段：永续增长期（使用戈登增长模型）
            terminal_dividend = latest_dividend * (1 + forecast_growth_rate) ** forecast_years * (1 + terminal_growth_rate)
            terminal_value = terminal_dividend / (discount_rate - terminal_growth_rate)
            pv_terminal_value = terminal_value / (1 + discount_rate) ** forecast_years
            
            # 计算每股内在价值
            intrinsic_value = sum(pv_dividends) + pv_terminal_value
            
            # 获取当前市场价格
            try:
                market_data = active_data_source.get_real_time_quotes(code)
                current_price = float(market_data['close'].iloc[0])
            except Exception as e:
                logger.warning(f"获取市场数据时出错: {e}")
                current_price = None
            
            # 生成分析报告
            report = f"# {code} DDM估值分析报告\n\n"
            
            report += "## 基本参数\n"
            report += f"- 历史增长率: {historical_growth*100:.1f}%\n"
            report += f"- 预测增长率: {forecast_growth_rate*100:.1f}%\n"
            report += f"- 永续增长率: {terminal_growth_rate*100:.1f}%\n"
            report += f"- 贴现率: {discount_rate*100:.1f}%\n"
            
            report += "\n## 历史分红数据\n"
            report += "| 年份 | 每股分红(元) |\n"
            report += "|------|-------------|\n"
            for year, div in zip(years, annual_dividends):
                report += f"| {year} | {div:.4f} |\n"
            
            report += "\n## 预测分红\n"
            report += "| 年份 | 预测分红 | 现值 |\n"
            report += "|------|----------|------|\n"
            future_dividends = []
            for i in range(1, forecast_years + 1):
                future_div = latest_dividend * (1 + forecast_growth_rate) ** i
                future_dividends.append(future_div)
                report += f"| {current_year + i} | ¥{future_div:.4f} | ¥{pv_dividends[i-1]:.4f} |\n"
            
            report += f"\n永续期现值: ¥{pv_terminal_value:.4f}\n"
            
            report += "\n## 估值结果\n"
            report += f"- 每股内在价值: ¥{intrinsic_value:.2f}\n"
            if current_price is not None:
                report += f"- 当前市场价格: ¥{current_price:.2f}\n"
                premium = (current_price / intrinsic_value - 1) * 100
                report += f"- 相对DDM估值: {'溢价' if premium > 0 else '折价'} {abs(premium):.1f}%\n"
            
            report += "\n## 估值假设和局限性\n"
            report += "1. DDM模型假设公司能够持续稳定分红\n"
            report += "2. 预测期增长率基于历史数据，可能不代表未来表现\n"
            report += "3. 终值计算对永续增长率和贴现率较为敏感\n"
            report += "4. 未考虑可能的分红政策变化\n"
            report += "5. 建议结合其他估值方法和定性分析\n"
            
            return report
            
        except Exception as e:
            logger.exception(f"计算 {code} 的DDM估值时出错: {str(e)}")
            return f"计算DDM估值时发生错误: {str(e)}"

    @app.tool()
    def calculate_dcf_valuation(
        code: str,
        years_back: int = 5,
        discount_rate: float = 0.10,
        terminal_growth_rate: float = 0.025
    ) -> str:
        """
        使用现金流贴现模型(DCF)计算股票的内在价值。

        Args:
            code: 股票代码，如'sh.600000'
            years_back: 使用多少年的历史数据来计算增长率，默认5年
            discount_rate: 贴现率/WACC，默认10%
            terminal_growth_rate: 永续增长率，默认2.5%

        Returns:
            DCF估值分析报告（Markdown格式）
        """
        try:
            # 获取历史现金流数据
            current_year = datetime.now().year
            cash_flow_data = []
            
            # 收集多年的现金流数据（使用第四季度数据作为年度数据）
            for year in range(current_year - years_back, current_year + 1):
                try:
                    year_data = active_data_source.get_cash_flow_data(
                        code=code,
                        year=str(year),
                        quarter=4  # 使用第四季度数据
                    )
                    if not year_data.empty:
                        year_data['year'] = year
                        cash_flow_data.append(year_data)
                except (NoDataFoundError, DataSourceError):
                    continue
            
            if not cash_flow_data:
                return f"无法获取 {code} 的现金流数据。"
            
            # 合并所有年份的数据
            cash_flow_df = pd.concat(cash_flow_data, ignore_index=True)
            
            # 提取经营现金流
            operating_cash_flows = []
            for _, row in cash_flow_df.iterrows():
                # 尝试不同的字段名（不同版本的数据可能字段名不同）
                for field in ['netCashOperating', 'NCFOperateA', 'operatingCashFlow']:
                    if field in row and pd.notna(row[field]):
                        try:
                            value = float(row[field])
                            operating_cash_flows.append(value)
                            break
                        except (ValueError, TypeError):
                            continue
            
            if len(operating_cash_flows) < 2:
                return f"无法获取足够的经营现金流数据来进行 DCF 估值分析。"
            
            # 计算DCF估值
            dcf_result = _calculate_dcf_value(
                cash_flows=operating_cash_flows,
                terminal_growth_rate=terminal_growth_rate,
                discount_rate=discount_rate
            )
            
            if "error" in dcf_result:
                return f"DCF估值计算错误: {dcf_result['error']}"
            
            # 获取当前市值和负债数据
            try:
                # 获取实时行情数据
                market_data = active_data_source.get_real_time_quotes(code)
                current_price = float(market_data['close'].iloc[0])
                
                # 获取最新的资产负债表数据
                balance_sheet = active_data_source.get_balance_data(
                    code=code,
                    year=str(current_year),
                    quarter=4
                )
                
                if balance_sheet.empty:
                    # 尝试获取上一年的数据
                    balance_sheet = active_data_source.get_balance_data(
                        code=code,
                        year=str(current_year - 1),
                        quarter=4
                    )
                
                if not balance_sheet.empty:
                    # 尝试不同的字段名
                    debt_fields = ['totalLiability', 'totalLiabilities', 'totalDebt']
                    total_debt = None
                    for field in debt_fields:
                        if field in balance_sheet.columns:
                            try:
                                total_debt = float(balance_sheet[field].iloc[0])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    if total_debt is None:
                        total_debt = 0  # 如果无法获取负债数据，假设为0
                else:
                    total_debt = 0
                
                # 获取总股本
                basic_info = active_data_source.get_stock_basic_info(code)
                if not basic_info.empty and 'totalShares' in basic_info.columns:
                    total_shares = float(basic_info['totalShares'].iloc[0])
                else:
                    # 如果无法获取总股本，使用成交量估算
                    total_shares = float(market_data['volume'].iloc[0])
                
            except Exception as e:
                logger.warning(f"获取市场数据时出错: {e}")
                return f"无法获取完整的市场数据进行估值比较: {str(e)}"
            
            # 计算每股价值
            enterprise_value = dcf_result['enterprise_value']
            equity_value = enterprise_value - total_debt
            per_share_value = equity_value / total_shares if total_shares > 0 else 0
            
            # 生成分析报告
            report = f"# {code} DCF估值分析报告\n\n"
            
            report += "## 基本参数\n"
            report += f"- 历史增长率: {dcf_result['historical_growth']*100:.1f}%\n"
            report += f"- 预测增长率: {dcf_result['forecast_growth_rate']*100:.1f}%\n"
            report += f"- 永续增长率: {terminal_growth_rate*100:.1f}%\n"
            report += f"- 贴现率(WACC): {discount_rate*100:.1f}%\n"
            
            report += "\n## 历史现金流数据\n"
            report += "| 年份 | 经营现金流(亿元) |\n"
            report += "|------|------------------|\n"
            for year, cf in zip(range(current_year - len(operating_cash_flows) + 1, current_year + 1), operating_cash_flows):
                report += f"| {year} | {cf/100000000:.2f} |\n"
            
            report += "\n## 估值结果\n"
            report += f"- 企业价值(EV): ¥{enterprise_value/100000000:.2f}亿\n"
            report += f"- 总负债: ¥{total_debt/100000000:.2f}亿\n"
            report += f"- 权益价值: ¥{equity_value/100000000:.2f}亿\n"
            report += f"- 每股内在价值: ¥{per_share_value:.2f}\n"
            report += f"- 当前市场价格: ¥{current_price:.2f}\n"
            
            # 计算溢价/折价
            if per_share_value > 0:
                premium = (current_price / per_share_value - 1) * 100
                report += f"- 相对DCF估值: {'溢价' if premium > 0 else '折价'} {abs(premium):.1f}%\n"
            
            report += "\n## 预测现金流\n"
            report += "| 年份 | 预测现金流(亿) | 现值(亿) |\n"
            report += "|------|---------------|----------|\n"
            
            pv_sum = 0
            for i, (cf, pv) in enumerate(zip(dcf_result['projected_cash_flows'], 
                                           [cf/(1+discount_rate)**(i+1) for i, cf in enumerate(dcf_result['projected_cash_flows'])]), 1):
                report += f"| {current_year + i} | ¥{cf/100000000:.2f} | ¥{pv/100000000:.2f} |\n"
                pv_sum += pv
            
            report += f"\n终值现值: ¥{dcf_result['pv_terminal_value']/100000000:.2f}亿\n"
            
            report += "\n## 估值假设和局限性\n"
            report += "1. DCF模型假设公司能够持续产生稳定的现金流\n"
            report += "2. 预测期增长率基于历史数据，可能不代表未来表现\n"
            report += "3. 终值计算对永续增长率和贴现率较为敏感\n"
            report += "4. 未考虑可能的重大资本支出或业务转型\n"
            report += "5. 建议结合其他估值方法和定性分析\n"
            
            return report
            
        except Exception as e:
            logger.exception(f"计算 {code} 的DCF估值时出错: {str(e)}")
            return f"计算DCF估值时发生错误: {str(e)}"

    @app.tool()
    def compare_industry_valuation(
        code: str,
        date: Optional[str] = None
    ) -> str:
        """
        进行同行业估值比较分析，对比目标股票与同行业其他公司的估值水平。

        Args:
            code: 目标股票代码，如'sh.600000'
            date: 比较基准日期，格式'YYYY-MM-DD'，默认为最新交易日

        Returns:
            包含同行业估值比较的详细分析报告
        """
        logger.info(f"Tool 'compare_industry_valuation' called for {code}")
        
        try:
            # 获取目标股票的行业信息
            industry_data = active_data_source.get_stock_industry(code=code, date=date)
            
            if industry_data.empty:
                return f"Error: Unable to fetch industry information for {code}"
            
            target_industry = industry_data['industry'].iloc[0]
            
            # 获取同行业所有股票
            all_industry_stocks = active_data_source.get_stock_industry(date=date)
            same_industry = all_industry_stocks[
                all_industry_stocks['industry'] == target_industry
            ].copy()
            
            if len(same_industry) < 2:
                return f"Error: Insufficient companies in industry '{target_industry}' for comparison"
            
            # 设置日期范围
            if date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            else:
                end_date = date
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
            
            # 收集同行业公司估值数据
            industry_valuations = []
            
            for _, stock in same_industry.iterrows():
                stock_code = stock['code']
                try:
                    valuation_df = active_data_source.get_historical_k_data(
                        code=stock_code,
                        start_date=start_date,
                        end_date=end_date,
                        frequency="d",
                        fields=["date", "code", "close", "peTTM", "pbMRQ", "psTTM"]
                    )
                    
                    if not valuation_df.empty:
                        latest_data = valuation_df.iloc[-1]
                        
                        # 转换数值
                        pe = pd.to_numeric(latest_data.get('peTTM'), errors='coerce')
                        pb = pd.to_numeric(latest_data.get('pbMRQ'), errors='coerce')
                        ps = pd.to_numeric(latest_data.get('psTTM'), errors='coerce')
                        price = pd.to_numeric(latest_data.get('close'), errors='coerce')
                        
                        industry_valuations.append({
                            'code': stock_code,
                            'code_name': stock.get('code_name', stock_code),
                            'pe_ttm': pe,
                            'pb_mrq': pb,
                            'ps_ttm': ps,
                            'price': price,
                            'is_target': stock_code == code
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {stock_code}: {e}")
                    continue
            
            if len(industry_valuations) < 2:
                return f"Error: Unable to fetch sufficient valuation data for industry comparison"
            
            # 转换为DataFrame
            valuation_df = pd.DataFrame(industry_valuations)
            
            # 计算行业统计
            metrics = ['pe_ttm', 'pb_mrq', 'ps_ttm']
            industry_stats = {}
            
            for metric in metrics:
                valid_data = valuation_df[metric].dropna()
                if len(valid_data) > 0:
                    industry_stats[metric] = {
                        'mean': valid_data.mean(),
                        'median': valid_data.median(),
                        'min': valid_data.min(),
                        'max': valid_data.max(),
                        'std': valid_data.std()
                    }
            
            # 获取目标公司数据
            target_data = valuation_df[valuation_df['is_target'] == True]
            if target_data.empty:
                return f"Error: Target company {code} not found in industry data"
            
            target_row = target_data.iloc[0]
            
            # 生成比较报告
            report = f"# {target_row['code_name']} ({code}) 行业估值比较\n\n"
            report += f"**所属行业**: {target_industry}\n"
            report += f"**同行业公司数量**: {len(industry_valuations)} 家\n"
            report += f"**比较基准日**: {end_date}\n\n"
            
            # 目标公司估值
            report += "## 目标公司当前估值\n"
            if pd.notna(target_row['pe_ttm']):
                report += f"- **市盈率TTM**: {target_row['pe_ttm']:.2f}\n"
            if pd.notna(target_row['pb_mrq']):
                report += f"- **市净率MRQ**: {target_row['pb_mrq']:.2f}\n"
            if pd.notna(target_row['ps_ttm']):
                report += f"- **市销率TTM**: {target_row['ps_ttm']:.2f}\n"
            
            # 行业估值统计
            report += f"\n## {target_industry}行业估值统计\n"
            
            for metric in metrics:
                if metric in industry_stats:
                    stats = industry_stats[metric]
                    target_value = target_row[metric]
                    
                    metric_name = {
                        'pe_ttm': '市盈率TTM',
                        'pb_mrq': '市净率MRQ',
                        'ps_ttm': '市销率TTM'
                    }[metric]
                    
                    report += f"\n### {metric_name}\n"
                    report += f"- 行业均值: {stats['mean']:.2f}\n"
                    report += f"- 行业中位数: {stats['median']:.2f}\n"
                    report += f"- 行业区间: {stats['min']:.2f} - {stats['max']:.2f}\n"
                    
                    if pd.notna(target_value):
                        deviation_from_mean = ((target_value / stats['mean']) - 1) * 100
                        percentile = (valuation_df[metric] <= target_value).mean() * 100
                        
                        report += f"- **目标公司**: {target_value:.2f}\n"
                        report += f"- **相对均值**: {deviation_from_mean:+.1f}%\n"
                        report += f"- **行业排名**: 第{percentile:.0f}分位\n"
            
            # 估值水平评价
            report += "\n## 估值水平评价\n"
            
            for metric in metrics:
                if metric in industry_stats and pd.notna(target_row[metric]):
                    target_value = target_row[metric]
                    mean_value = industry_stats[metric]['mean']
                    
                    metric_name = {
                        'pe_ttm': '市盈率',
                        'pb_mrq': '市净率',
                        'ps_ttm': '市销率'
                    }[metric]
                    
                    if target_value < mean_value * 0.8:
                        level = "明显低估"
                    elif target_value < mean_value * 0.95:
                        level = "轻微低估"
                    elif target_value <= mean_value * 1.05:
                        level = "估值合理"
                    elif target_value <= mean_value * 1.2:
                        level = "轻微高估"
                    else:
                        level = "明显高估"
                    
                    report += f"- **{metric_name}**: {level}（相对行业均值）\n"
            
            # 行业估值数据表格（前10家公司）
            display_df = valuation_df.head(10)[['code', 'code_name', 'pe_ttm', 'pb_mrq', 'ps_ttm']].copy()
            display_df = display_df.round(2)
            
            report += f"\n## 行业主要公司估值对比（前10家）\n"
            report += format_df_to_markdown(display_df)
            
            report += "\n**说明**: 以上比较基于公开市场数据，实际投资决策还需考虑公司基本面、成长性等因素。"
            
            logger.info(f"Successfully completed industry valuation comparison for {code}")
            return report
            
        except Exception as e:
            logger.exception(f"Error in industry valuation comparison for {code}: {e}")
            return f"Error: Failed to complete industry valuation comparison: {e}" 