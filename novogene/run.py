#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
运行入口脚本
"""

import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import main

if __name__ == '__main__':
    main()
