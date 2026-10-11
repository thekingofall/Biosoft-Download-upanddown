#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Novogene下载管理系统 - 环境管理模块
功能: Python版本的conda/mamba环境管理器
作者: Python架构师
"""

import os
import sys
import subprocess
import platform
from typing import Dict, List, Optional, Tuple


class EnvironmentManager:
    """conda/mamba环境管理器"""
    
    def __init__(self, env_name: str = "novogene-download"):
        """初始化环境管理器
        
        Args:
            env_name: conda环境名称
        """
        self.env_name = env_name
        self.project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.env_file = os.path.join(self.project_dir, "environment.yml")
        
    def _run_command(self, cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
        """运行命令并返回结果
        
        Args:
            cmd: 命令列表
            check: 是否检查返回码
            
        Returns:
            (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=check
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr
        except FileNotFoundError:
            return 127, "", "Command not found"
    
    def check_conda_available(self) -> Tuple[bool, Optional[str]]:
        """检查conda是否可用
        
        Returns:
            (is_available, conda_path)
        """
        for cmd in ['conda', 'mamba']:
            code, stdout, _ = self._run_command(['which', cmd], check=False)
            if code == 0:
                return True, stdout.strip()
        return False, None
    
    def check_mamba_available(self) -> bool:
        """检查mamba是否可用"""
        code, _, _ = self._run_command(['which', 'mamba'], check=False)
        return code == 0
    
    def get_conda_envs(self) -> List[str]:
        """获取conda环境列表"""
        code, stdout, _ = self._run_command(['conda', 'env', 'list'], check=False)
        if code != 0:
            return []
        
        envs = []
        for line in stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                env_name = line.split()[0]
                if env_name and env_name != 'base':
                    envs.append(env_name)
        return envs
    
    def env_exists(self) -> bool:
        """检查环境是否存在"""
        return self.env_name in self.get_conda_envs()
    
    def create_environment(self, force: bool = False) -> Tuple[bool, str]:
        """创建conda环境
        
        Args:
            force: 是否强制重建
            
        Returns:
            (success, message)
        """
        if not os.path.exists(self.env_file):
            return False, "环境配置文件不存在: {}".format(self.env_file)
        
        # 检查环境是否存在
        if self.env_exists():
            if not force:
                return True, "环境 '{}' 已存在".format(self.env_name)
            else:
                # 删除现有环境
                self.remove_environment()
        
        # 选择创建工具
        create_cmd = 'mamba' if self.check_mamba_available() else 'conda'
        
        # 创建环境
        cmd = [create_cmd, 'env', 'create', '-f', self.env_file]
        code, stdout, stderr = self._run_command(cmd, check=False)
        
        if code == 0:
            return True, "环境 '{}' 创建成功".format(self.env_name)
        else:
            return False, "环境创建失败: {}".format(stderr)
    
    def update_environment(self) -> Tuple[bool, str]:
        """更新conda环境"""
        if not self.env_exists():
            return False, "环境 '{}' 不存在".format(self.env_name)
        
        if not os.path.exists(self.env_file):
            return False, "环境配置文件不存在: {}".format(self.env_file)
        
        # 选择更新工具
        update_cmd = 'mamba' if self.check_mamba_available() else 'conda'
        
        # 更新环境
        cmd = [update_cmd, 'env', 'update', '-f', self.env_file]
        code, stdout, stderr = self._run_command(cmd, check=False)
        
        if code == 0:
            return True, "环境 '{}' 更新成功".format(self.env_name)
        else:
            return False, "环境更新失败: {}".format(stderr)
    
    def remove_environment(self) -> Tuple[bool, str]:
        """删除conda环境"""
        if not self.env_exists():
            return True, "环境 '{}' 不存在".format(self.env_name)
        
        cmd = ['conda', 'env', 'remove', '-n', self.env_name]
        code, stdout, stderr = self._run_command(cmd, check=False)
        
        if code == 0:
            return True, "环境 '{}' 删除成功".format(self.env_name)
        else:
            return False, "环境删除失败: {}".format(stderr)
    
    def get_environment_info(self) -> Dict[str, str]:
        """获取环境信息"""
        info = {
            'name': self.env_name,
            'exists': str(self.env_exists()),
            'project_dir': self.project_dir,
            'env_file': self.env_file,
            'system': platform.system(),
            'python_version': sys.version
        }
        
        # 检查conda可用性
        conda_available, conda_path = self.check_conda_available()
        info['conda_available'] = str(conda_available)
        info['conda_path'] = conda_path or "未找到"
        info['mamba_available'] = str(self.check_mamba_available())
        
        return info
    
    def validate_environment(self) -> Tuple[bool, List[str]]:
        """验证环境完整性
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 检查conda可用性
        conda_available, _ = self.check_conda_available()
        if not conda_available:
            errors.append("conda/mamba 未安装或不可用")
        
        # 检查环境配置文件
        if not os.path.exists(self.env_file):
            errors.append("环境配置文件不存在: {}".format(self.env_file))
        
        # 检查环境是否存在
        if not self.env_exists():
            errors.append("conda环境 '{}' 不存在".format(self.env_name))
        
        return len(errors) == 0, errors
    
    def get_activation_command(self) -> str:
        """获取环境激活命令"""
        return "conda activate {}".format(self.env_name)
    
    def get_deactivation_command(self) -> str:
        """获取环境退出命令"""
        return "conda deactivate"


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Novogene环境管理器')
    parser.add_argument('action', choices=['create', 'update', 'remove', 'info', 'validate'],
                       help='执行的操作')
    parser.add_argument('--force', action='store_true', help='强制执行操作')
    parser.add_argument('--env-name', default='novogene-download', help='环境名称')
    
    args = parser.parse_args()
    
    env_manager = EnvironmentManager(args.env_name)
    
    if args.action == 'create':
        success, message = env_manager.create_environment(args.force)
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.action == 'update':
        success, message = env_manager.update_environment()
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.action == 'remove':
        success, message = env_manager.remove_environment()
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.action == 'info':
        info = env_manager.get_environment_info()
        print("环境信息:")
        for key, value in info.items():
            print("  {}: {}".format(key, value))
    
    elif args.action == 'validate':
        is_valid, errors = env_manager.validate_environment()
        if is_valid:
            print("✅ 环境验证通过")
        else:
            print("❌ 环境验证失败:")
            for error in errors:
                print("  - {}".format(error))
        sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
