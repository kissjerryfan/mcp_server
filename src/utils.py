# Utility functions, including the Baostock login context manager and logging setup
import baostock as bs
import os
import sys
import logging
import platform
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from io import StringIO
from .data_source_interface import LoginError

# --- Logging Setup ---
def setup_logging(level=logging.WARNING):
    """配置基本日志"""
    # 设置第三方库的日志级别为 WARNING 或更高
    logging.getLogger('baostock').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('charset_normalizer').setLevel(logging.WARNING)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',  # 简化的日志格式
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Get a logger instance for this module (optional, but good practice)
logger = logging.getLogger(__name__)

# --- Baostock Context Manager ---
@contextmanager
def baostock_login_context():
    """处理 Baostock 登录和登出的上下文管理器"""
    # 创建一个空的 StringIO 对象来捕获输出
    stdout_redirect = StringIO()
    stderr_redirect = StringIO()
    
    try:
        # 重定向标准输出和标准错误
        with redirect_stdout(stdout_redirect), redirect_stderr(stderr_redirect):
            lg = bs.login()
            
        if lg.error_code != '0':
            error_msg = f"Baostock 登录失败: {lg.error_msg}"
            logger.error(error_msg)
            raise LoginError(error_msg)
            
        yield
        
    except Exception as e:
        logger.error(f"Baostock 错误: {str(e)}")
        raise
        
    finally:
        try:
            # 重定向输出来抑制登出消息
            with redirect_stdout(stdout_redirect), redirect_stderr(stderr_redirect):
                bs.logout()
        except Exception:
            pass  # 忽略登出错误

# You can add other utility functions or classes here if needed
