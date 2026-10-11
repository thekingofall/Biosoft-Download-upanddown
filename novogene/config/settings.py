#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置设置模块
"""

import os
import secrets
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Flask配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    PORT = int(os.environ.get('FLASK_PORT', 3683))

# 下载配置
class DownloadConfig:
    # lnd命令路径
    LND_CMD_PATH = os.environ.get('LND_CMD_PATH', 'lnd')
    
    # 默认下载目录
    DEFAULT_DOWNLOAD_DIR = str(DATA_DIR)
    
    # 最大并发下载任务数
    MAX_CONCURRENT_TASKS = int(os.environ.get('MAX_CONCURRENT_TASKS', 3))
    
    # 任务超时时间(秒)
    TASK_TIMEOUT = int(os.environ.get('TASK_TIMEOUT', 3600))  # 1小时
    
    # 日志保留天数
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'novogene_download': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}
