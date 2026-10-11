#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设置管理模块
用于管理用户配置和系统设置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class SettingsManager:
    """设置管理器"""
    
    def __init__(self, settings_file: str = "user_settings.json"):
        self.base_dir = Path(__file__).parent.parent
        self.settings_file = self.base_dir / settings_file
        self.default_settings = {
            "lnd_cmd_path": os.environ.get("LND_CMD_PATH", "lnd"),
            "default_download_dir": str(self.base_dir / "data"),
            "max_concurrent_tasks": 3,
            "task_timeout": 3600,
            "auto_validate": True,
            "generate_report": True,
            "first_run": True
        }
        self._settings = None
    
    def _load_settings(self) -> Dict[str, Any]:
        """加载设置"""
        if self._settings is not None:
            return self._settings
            
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 合并默认设置，确保新增的设置项存在
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)
                self._settings = merged_settings
                return self._settings
            except Exception as e:
                print("加载设置文件失败: {}".format(e))
                
        # 返回默认设置
        self._settings = self.default_settings.copy()
        return self._settings
    
    def _save_settings(self) -> bool:
        """保存设置"""
        try:
            # 确保目录存在
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("保存设置文件失败: {}".format(e))
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        settings = self._load_settings()
        return settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        settings = self._load_settings()
        settings[key] = value
        return self._save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有设置"""
        return self._load_settings().copy()
    
    def update(self, new_settings: Dict[str, Any]) -> bool:
        """批量更新设置"""
        settings = self._load_settings()
        settings.update(new_settings)
        return self._save_settings()
    
    def reset_to_default(self) -> bool:
        """重置为默认设置"""
        self._settings = self.default_settings.copy()
        return self._save_settings()
    
    def is_first_run(self) -> bool:
        """检查是否为首次运行"""
        return self.get("first_run", True)
    
    def mark_setup_complete(self) -> bool:
        """标记初始设置完成"""
        return self.set("first_run", False)
    
    def validate_lnd_path(self, path: str) -> Dict[str, Any]:
        """验证LND命令路径"""
        result = {
            "valid": False,
            "message": "",
            "exists": False,
            "executable": False
        }
        
        if not path:
            result["message"] = "路径不能为空"
            return result
        
        path_obj = Path(path)
        
        # 检查文件是否存在
        if not path_obj.exists():
            result["message"] = "文件不存在: {}".format(path)
            return result
        
        result["exists"] = True
        
        # 检查是否为文件
        if not path_obj.is_file():
            result["message"] = "指定路径不是文件: {}".format(path)
            return result
        
        # 检查是否可执行
        if not os.access(path, os.X_OK):
            result["message"] = "文件不可执行: {}".format(path)
            return result
        
        result["executable"] = True
        result["valid"] = True
        result["message"] = "LND命令验证成功"
        
        return result
    
    def validate_download_dir(self, path: str) -> Dict[str, Any]:
        """验证下载目录"""
        result = {
            "valid": False,
            "message": "",
            "exists": False,
            "writable": False,
            "space_available": 0
        }
        
        if not path:
            result["message"] = "路径不能为空"
            return result
        
        path_obj = Path(path)
        
        # 尝试创建目录
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            result["exists"] = True
        except Exception as e:
            result["message"] = "无法创建目录: {}".format(str(e))
            return result
        
        # 检查是否为目录
        if not path_obj.is_dir():
            result["message"] = "指定路径不是目录: {}".format(path)
            return result
        
        # 检查是否可写
        if not os.access(path, os.W_OK):
            result["message"] = "目录不可写: {}".format(path)
            return result
        
        result["writable"] = True
        
        # 检查可用空间
        try:
            statvfs = os.statvfs(path)
            # 可用空间（字节）
            available_space = statvfs.f_frsize * statvfs.f_bavail
            result["space_available"] = available_space
        except Exception:
            result["space_available"] = 0
        
        result["valid"] = True
        result["message"] = "下载目录验证成功"
        
        return result
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        import shutil
        
        info = {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "home_dir": str(Path.home()),
            "current_dir": str(Path.cwd()),
            "disk_usage": {}
        }
        
        # 获取磁盘使用情况
        try:
            total, used, free = shutil.disk_usage(Path.home())
            info["disk_usage"] = {
                "total": total,
                "used": used,
                "free": free
            }
        except Exception:
            pass
        
        return info
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return "{:.1f} {}".format(size, size_names[i])


# 全局设置管理器实例
settings_manager = SettingsManager()


def main():
    """测试函数"""
    sm = SettingsManager()
    
    print("当前设置:")
    for key, value in sm.get_all().items():
        print("  {}: {}".format(key, value))
    
    print("\n系统信息:")
    info = sm.get_system_info()
    for key, value in info.items():
        print("  {}: {}".format(key, value))
    
    # 测试LND路径验证
    lnd_result = sm.validate_lnd_path(sm.get("lnd_cmd_path"))
    print("\nLND验证结果: {}".format(lnd_result))
    
    # 测试下载目录验证
    dir_result = sm.validate_download_dir(sm.get("default_download_dir"))
    print("下载目录验证结果: {}".format(dir_result))


if __name__ == "__main__":
    main()