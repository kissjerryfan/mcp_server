"""
Technical indicators tools for MCP server.
Provides technical analysis capabilities including MACD, RSI, KDJ, Bollinger Bands, etc.
"""
import logging
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import pandas_ta as ta
except ImportError:
    ta = None

from mcp.server.fastmcp import FastMCP
from src.data_source_interface import FinancialDataSource, NoDataFoundError, LoginError, DataSourceError
from src.formatting.markdown_formatter import format_df_to_markdown

logger = logging.getLogger(__name__)


def _ensure_pandas_ta():
    """Ensure pandas_ta is available, raise error if not."""
    if ta is None:
        raise ImportError("pandas-ta library is required for technical indicators. Install with: pip install pandas-ta")


def _calculate_manual_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate basic indicators manually if pandas-ta is not available."""
    result = {}
    
    # Ensure we have the required columns
    if 'close' not in df.columns:
        return result
    
    close_prices = pd.to_numeric(df['close'], errors='coerce')
    high_prices = pd.to_numeric(df['high'], errors='coerce') if 'high' in df.columns else close_prices
    low_prices = pd.to_numeric(df['low'], errors='coerce') if 'low' in df.columns else close_prices
    volume = pd.to_numeric(df['volume'], errors='coerce') if 'volume' in df.columns else None
    
    # Simple Moving Averages
    result['SMA_5'] = close_prices.rolling(window=5).mean()
    result['SMA_10'] = close_prices.rolling(window=10).mean()
    result['SMA_20'] = close_prices.rolling(window=20).mean()
    result['SMA_50'] = close_prices.rolling(window=50).mean()
    
    # RSI calculation
    if len(close_prices) >= 14:
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (20-day, 2 std)
    if len(close_prices) >= 20:
        sma20 = close_prices.rolling(window=20).mean()
        std20 = close_prices.rolling(window=20).std()
        result['BB_Upper'] = sma20 + (std20 * 2)
        result['BB_Lower'] = sma20 - (std20 * 2)
        result['BB_Middle'] = sma20
    
    # MACD (12, 26, 9)
    if len(close_prices) >= 26:
        ema12 = close_prices.ewm(span=12).mean()
        ema26 = close_prices.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        result['MACD'] = macd_line
        result['MACD_Signal'] = signal_line
        result['MACD_Histogram'] = macd_line - signal_line
    
    return result


def register_technical_indicator_tools(app: FastMCP, active_data_source: FinancialDataSource):
    """
    Register technical indicator tools with the MCP app.

    Args:
        app: The FastMCP app instance
        active_data_source: The active financial data source
    """

    @app.tool()
    def get_technical_indicators(
        code: str,
        start_date: str,
        end_date: str,
        indicators: Optional[List[str]] = None
    ) -> str:
        """
        计算股票的技术指标，包括MACD、RSI、KDJ、布林带、威廉指标、随机震荡器等。

        Args:
            code: 股票代码，如'sh.600000'
            start_date: 开始日期，格式'YYYY-MM-DD'
            end_date: 结束日期，格式'YYYY-MM-DD'
            indicators: 指标列表，可选值包括:
                       ['MACD', 'RSI', 'KDJ', 'BOLL', 'WR', 'STOCH', 'CCI', 'ATR']
                       如果为空，则计算所有支持的指标

        Returns:
            包含技术指标数据的Markdown表格
        """
        logger.info(f"Tool 'get_technical_indicators' called for {code} ({start_date}-{end_date})")
        
        try:
            # 获取历史K线数据
            df = active_data_source.get_historical_k_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjust_flag="2"  # 使用前复权数据进行技术分析
            )
            
            if df.empty:
                return f"Error: No data found for {code} in the specified date range."
            
            # 设置默认指标
            if indicators is None:
                indicators = ['MACD', 'RSI', 'BOLL', 'WR', 'STOCH']
            
            # 确保日期列为datetime类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            # 转换数值列
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            result_df = df[['close']].copy()  # 保留收盘价作为基准
            
            try:
                _ensure_pandas_ta()
                use_pandas_ta = True
            except ImportError:
                logger.warning("pandas-ta not available, using manual calculations")
                use_pandas_ta = False
            
            if use_pandas_ta:
                # 使用pandas-ta计算指标
                for indicator in indicators:
                    try:
                        if indicator.upper() == 'MACD':
                            macd_data = ta.macd(df['close'])
                            if macd_data is not None:
                                result_df = pd.concat([result_df, macd_data], axis=1)
                        
                        elif indicator.upper() == 'RSI':
                            rsi = ta.rsi(df['close'], length=14)
                            if rsi is not None:
                                result_df['RSI'] = rsi
                        
                        elif indicator.upper() in ['BOLL', 'BB']:
                            bb = ta.bbands(df['close'], length=20, std=2)
                            if bb is not None:
                                result_df = pd.concat([result_df, bb], axis=1)
                        
                        elif indicator.upper() == 'WR':
                            wr = ta.willr(df['high'], df['low'], df['close'], length=14)
                            if wr is not None:
                                result_df['WR'] = wr
                        
                        elif indicator.upper() == 'STOCH':
                            stoch = ta.stoch(df['high'], df['low'], df['close'])
                            if stoch is not None:
                                result_df = pd.concat([result_df, stoch], axis=1)
                        
                        elif indicator.upper() == 'KDJ':
                            stoch = ta.stoch(df['high'], df['low'], df['close'], k=9, d=3)
                            if stoch is not None:
                                # KDJ是Stoch的变种
                                result_df = pd.concat([result_df, stoch], axis=1)
                        
                        elif indicator.upper() == 'CCI':
                            cci = ta.cci(df['high'], df['low'], df['close'], length=20)
                            if cci is not None:
                                result_df['CCI'] = cci
                        
                        elif indicator.upper() == 'ATR':
                            atr = ta.atr(df['high'], df['low'], df['close'], length=14)
                            if atr is not None:
                                result_df['ATR'] = atr
                                
                    except Exception as e:
                        logger.warning(f"Failed to calculate {indicator}: {e}")
                        continue
            else:
                # 使用手动计算
                manual_indicators = _calculate_manual_indicators(df)
                for key, value in manual_indicators.items():
                    result_df[key] = value
            
            # 重置索引以便格式化
            result_df = result_df.reset_index()
            
            # 只保留最近30个交易日的数据以避免输出过长
            if len(result_df) > 30:
                result_df = result_df.tail(30)
            
            # 格式化数值
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns
            result_df[numeric_cols] = result_df[numeric_cols].round(4)
            
            logger.info(f"Successfully calculated technical indicators for {code}")
            return format_df_to_markdown(result_df)
            
        except Exception as e:
            logger.exception(f"Error calculating technical indicators for {code}: {e}")
            return f"Error: Failed to calculate technical indicators: {e}"

    @app.tool()
    def get_moving_averages(
        code: str,
        start_date: str,
        end_date: str,
        periods: Optional[List[int]] = None
    ) -> str:
        """
        计算多种周期的移动平均线（5、10、20、50、120、250日），包括SMA、EMA、WMA等类型。

        Args:
            code: 股票代码，如'sh.600000'
            start_date: 开始日期，格式'YYYY-MM-DD'
            end_date: 结束日期，格式'YYYY-MM-DD'
            periods: 移动平均线周期列表，如[5, 10, 20, 50]，默认使用常用周期

        Returns:
            包含各种移动平均线数据的Markdown表格
        """
        logger.info(f"Tool 'get_moving_averages' called for {code} ({start_date}-{end_date})")
        
        try:
            # 获取历史K线数据
            df = active_data_source.get_historical_k_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjust_flag="2"
            )
            
            if df.empty:
                return f"Error: No data found for {code} in the specified date range."
            
            # 设置默认周期
            if periods is None:
                periods = [5, 10, 20, 50, 120, 250]
            
            # 确保日期列为datetime类型
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # 转换收盘价为数值
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            result_df = df[['date', 'close']].copy()
            
            # 计算不同类型的移动平均线
            for period in periods:
                if len(df) >= period:
                    # 简单移动平均线 (SMA)
                    result_df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
                    
                    # 指数移动平均线 (EMA)
                    result_df[f'EMA_{period}'] = df['close'].ewm(span=period).mean()
                    
                    # 加权移动平均线 (WMA) - 简化版本
                    weights = np.arange(1, period + 1)
                    result_df[f'WMA_{period}'] = df['close'].rolling(window=period).apply(
                        lambda x: np.dot(x, weights) / weights.sum(), raw=True
                    )
            
            # 添加均线分析
            if len(result_df) > 0:
                latest_close = result_df['close'].iloc[-1]
                analysis = [f"\n## 移动平均线分析 (最新收盘价: {latest_close:.2f})"]
                
                for period in periods:
                    sma_col = f'SMA_{period}'
                    if sma_col in result_df.columns:
                        latest_sma = result_df[sma_col].iloc[-1]
                        if pd.notna(latest_sma):
                            deviation = ((latest_close / latest_sma) - 1) * 100
                            trend = "上方" if deviation > 0 else "下方"
                            analysis.append(f"- {period}日SMA: {latest_sma:.2f} (股价在{trend} {abs(deviation):.2f}%)")
            
            # 只保留最近30个交易日
            if len(result_df) > 30:
                result_df = result_df.tail(30)
            
            # 格式化数值
            numeric_cols = result_df.select_dtypes(include=[np.number]).columns
            result_df[numeric_cols] = result_df[numeric_cols].round(4)
            
            result_markdown = format_df_to_markdown(result_df)
            if 'analysis' in locals():
                result_markdown += "\n".join(analysis)
            
            logger.info(f"Successfully calculated moving averages for {code}")
            return result_markdown
            
        except Exception as e:
            logger.exception(f"Error calculating moving averages for {code}: {e}")
            return f"Error: Failed to calculate moving averages: {e}"

    @app.tool()
    def calculate_risk_metrics(
        code: str,
        benchmark_code: str = "sh.000300",  # 默认使用沪深300
        period: str = "1Y"
    ) -> str:
        """
        计算风险指标，包括贝塔值、夏普比率、最大回撤、波动率、下行风险等，与基准指数比较。

        Args:
            code: 股票代码，如'sh.600000'
            benchmark_code: 基准指数代码，默认'sh.000300'(沪深300)，可选'sh.000016'(上证50)
            period: 分析周期，'1Y'(1年)、'6M'(6个月)、'3M'(3个月)、'2Y'(2年)

        Returns:
            包含风险指标的详细分析报告
        """
        logger.info(f"Tool 'calculate_risk_metrics' called for {code} vs {benchmark_code}, period={period}")
        
        try:
            # 计算日期范围
            end_date = datetime.now().strftime("%Y-%m-%d")
            if period == "1Y":
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            elif period == "6M":
                start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            elif period == "3M":
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            elif period == "2Y":
                start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # 获取股票数据
            stock_df = active_data_source.get_historical_k_data(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjust_flag="2"
            )
            
            # 获取基准指数数据
            benchmark_df = active_data_source.get_historical_k_data(
                code=benchmark_code,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjust_flag="2"
            )
            
            if stock_df.empty or benchmark_df.empty:
                return f"Error: Unable to fetch data for {code} or {benchmark_code}."
            
            # 数据预处理
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
            stock_df['close'] = pd.to_numeric(stock_df['close'], errors='coerce')
            benchmark_df['close'] = pd.to_numeric(benchmark_df['close'], errors='coerce')
            
            # 合并数据
            merged_df = pd.merge(stock_df[['date', 'close']], 
                               benchmark_df[['date', 'close']], 
                               on='date', suffixes=('_stock', '_benchmark'))
            merged_df = merged_df.dropna()
            
            if len(merged_df) < 20:
                return f"Error: Insufficient data for risk calculation (only {len(merged_df)} valid data points)."
            
            # 计算日收益率
            merged_df['stock_return'] = merged_df['close_stock'].pct_change()
            merged_df['benchmark_return'] = merged_df['close_benchmark'].pct_change()
            merged_df = merged_df.dropna()
            
            # 计算风险指标
            stock_returns = merged_df['stock_return']
            benchmark_returns = merged_df['benchmark_return']
            
            # 1. 贝塔值
            covariance = stock_returns.cov(benchmark_returns)
            benchmark_variance = benchmark_returns.var()
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
            
            # 2. 波动率 (年化)
            stock_volatility = stock_returns.std() * np.sqrt(252)
            benchmark_volatility = benchmark_returns.std() * np.sqrt(252)
            
            # 3. 年化收益率
            total_days = len(merged_df)
            stock_total_return = (merged_df['close_stock'].iloc[-1] / merged_df['close_stock'].iloc[0]) - 1
            benchmark_total_return = (merged_df['close_benchmark'].iloc[-1] / merged_df['close_benchmark'].iloc[0]) - 1
            stock_annual_return = (1 + stock_total_return) ** (252 / total_days) - 1
            benchmark_annual_return = (1 + benchmark_total_return) ** (252 / total_days) - 1
            
            # 4. 夏普比率 (假设无风险利率为3%)
            risk_free_rate = 0.03
            stock_sharpe = (stock_annual_return - risk_free_rate) / stock_volatility if stock_volatility != 0 else 0
            benchmark_sharpe = (benchmark_annual_return - risk_free_rate) / benchmark_volatility if benchmark_volatility != 0 else 0
            
            # 5. 最大回撤
            stock_cumulative = (1 + stock_returns).cumprod()
            stock_rolling_max = stock_cumulative.expanding().max()
            stock_drawdown = (stock_cumulative - stock_rolling_max) / stock_rolling_max
            max_drawdown = stock_drawdown.min()
            
            # 6. 下行风险 (相对于基准的负偏差)
            excess_returns = stock_returns - benchmark_returns
            negative_excess = excess_returns[excess_returns < 0]
            downside_risk = negative_excess.std() * np.sqrt(252) if len(negative_excess) > 0 else 0
            
            # 7. 相关系数
            correlation = stock_returns.corr(benchmark_returns)
            
            # 8. 信息比率
            excess_return = stock_annual_return - benchmark_annual_return
            tracking_error = (stock_returns - benchmark_returns).std() * np.sqrt(252)
            information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
            
            # 生成报告
            report = f"# {code} 风险指标分析报告\n\n"
            report += f"**分析周期**: {period} ({start_date} 至 {end_date})\n"
            report += f"**基准指数**: {benchmark_code}\n"
            report += f"**数据点数**: {len(merged_df)} 个交易日\n\n"
            
            report += "## 收益率指标\n"
            report += f"- **股票年化收益率**: {stock_annual_return:.2%}\n"
            report += f"- **基准年化收益率**: {benchmark_annual_return:.2%}\n"
            report += f"- **超额收益率**: {excess_return:.2%}\n\n"
            
            report += "## 风险指标\n"
            report += f"- **贝塔值**: {beta:.3f} (相对于{benchmark_code})\n"
            report += f"- **股票波动率**: {stock_volatility:.2%} (年化)\n"
            report += f"- **基准波动率**: {benchmark_volatility:.2%} (年化)\n"
            report += f"- **最大回撤**: {max_drawdown:.2%}\n"
            report += f"- **下行风险**: {downside_risk:.2%} (年化)\n\n"
            
            report += "## 风险调整收益指标\n"
            report += f"- **夏普比率**: {stock_sharpe:.3f}\n"
            report += f"- **基准夏普比率**: {benchmark_sharpe:.3f}\n"
            report += f"- **信息比率**: {information_ratio:.3f}\n"
            report += f"- **跟踪误差**: {tracking_error:.2%}\n"
            report += f"- **相关系数**: {correlation:.3f}\n\n"
            
            report += "## 指标解读\n"
            report += f"- **贝塔解读**: {'高风险高收益' if beta > 1.2 else '低风险低收益' if beta < 0.8 else '风险适中'} (β={beta:.2f})\n"
            report += f"- **夏普比率**: {'优秀' if stock_sharpe > 1 else '良好' if stock_sharpe > 0.5 else '一般' if stock_sharpe > 0 else '较差'}\n"
            report += f"- **相关性**: {'高度相关' if abs(correlation) > 0.7 else '中度相关' if abs(correlation) > 0.3 else '低相关'}与基准指数\n"
            
            report += "\n**免责声明**: 以上指标基于历史数据计算，不构成投资建议。"
            
            logger.info(f"Successfully calculated risk metrics for {code}")
            return report
            
        except Exception as e:
            logger.exception(f"Error calculating risk metrics for {code}: {e}")
            return f"Error: Failed to calculate risk metrics: {e}" 