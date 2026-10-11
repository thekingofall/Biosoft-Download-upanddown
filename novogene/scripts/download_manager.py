#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载管理模块
管理诺禾云数据下载任务
"""

import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

from .email_parser import NovoGeneInfo


class DownloadStatus(Enum):
    """下载状态枚举"""
    PENDING = "pending"          # 等待开始
    LOGGING_IN = "logging_in"    # 正在登录
    LISTING = "listing"          # 列出文件
    DOWNLOADING = "downloading"  # 正在下载
    VALIDATING = "validating"    # 验证文件
    COMPLETED = "completed"      # 完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


@dataclass
class DownloadTask:
    """下载任务数据类"""
    task_id: str
    info: NovoGeneInfo
    download_dir: str
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    current_step: str = ""
    log_messages: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: str = ""
    downloaded_files: List[str] = field(default_factory=list)


class DownloadManager:
    """下载管理器"""
    
    def __init__(self, lnd_cmd_path: str = "lnd"):
        self.lnd_cmd = shutil.which(lnd_cmd_path) or lnd_cmd_path
        self.tasks: Dict[str, DownloadTask] = {}
        self._running_tasks: Dict[str, threading.Thread] = {}
        self._status_callbacks: List[Callable[[str, DownloadTask], None]] = []
    
    def add_status_callback(self, callback: Callable[[str, DownloadTask], None]):
        """添加状态变化回调函数"""
        self._status_callbacks.append(callback)
    
    def _notify_status_change(self, task_id: str, task: DownloadTask):
        """通知状态变化"""
        for callback in self._status_callbacks:
            try:
                callback(task_id, task)
            except Exception as e:
                print(f"回调函数执行错误: {e}")
    
    def create_task(self, info: NovoGeneInfo, download_dir: str) -> str:
        """
        创建下载任务
        
        Args:
            info: 诺禾云信息
            download_dir: 下载目录
            
        Returns:
            任务ID
        """
        task_id = f"task_{int(time.time())}_{info.username}"
        
        # 创建下载目录
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        
        task = DownloadTask(
            task_id=task_id,
            info=info,
            download_dir=str(Path(download_dir).resolve())
        )
        
        self.tasks[task_id] = task
        self._log_message(task_id, f"任务创建: {task_id}")
        
        return task_id
    
    def start_download(self, task_id: str) -> bool:
        """
        开始下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功启动
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status != DownloadStatus.PENDING:
            return False
        
        # 检查lnd命令
        if not self._check_lnd_command():
            self._set_task_failed(task_id, "lnd命令不可用")
            return False
        
        # 启动下载线程
        thread = threading.Thread(target=self._download_worker, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        self._running_tasks[task_id] = thread
        return True
    
    def cancel_download(self, task_id: str) -> bool:
        """
        取消下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
            return False
        
        self._update_task_status(task_id, DownloadStatus.CANCELLED)
        self._log_message(task_id, "任务已取消")
        
        return True
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, DownloadTask]:
        """获取所有任务"""
        return self.tasks.copy()
    
    def remove_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status not in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
            return False
        
        del self.tasks[task_id]
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
        
        return True
    
    def _check_lnd_command(self) -> bool:
        """检查lnd命令是否可用"""
        if not os.path.exists(self.lnd_cmd):
            return False
        if not os.access(self.lnd_cmd, os.X_OK):
            return False
        return True
    
    def _download_worker(self, task_id: str):
        """下载工作线程"""
        task = self.tasks[task_id]
        task.start_time = datetime.now()
        
        try:
            # 1. 登录
            self._update_task_status(task_id, DownloadStatus.LOGGING_IN, "正在登录...")
            if not self._login(task_id):
                return
            
            # 2. 列出文件
            self._update_task_status(task_id, DownloadStatus.LISTING, "正在列出文件...")
            if not self._list_files(task_id):
                return
            
            # 3. 下载文件
            self._update_task_status(task_id, DownloadStatus.DOWNLOADING, "正在下载文件...")
            if not self._download_files(task_id):
                return
            
            # 4. 验证文件
            self._update_task_status(task_id, DownloadStatus.VALIDATING, "正在验证文件...")
            if not self._validate_files(task_id):
                self._set_task_failed(task_id, "MD5校验失败或校验工具不可用")
                return
            
            # 5. 完成
            self._update_task_status(task_id, DownloadStatus.COMPLETED, "下载完成")
            task.end_time = datetime.now()
            self._log_message(task_id, f"任务完成，耗时: {task.end_time - task.start_time}")
            
        except Exception as e:
            self._set_task_failed(task_id, f"下载过程中出现错误: {str(e)}")
    
    def _login(self, task_id: str) -> bool:
        """登录诺禾云"""
        task = self.tasks[task_id]
        
        try:
            cmd = [self.lnd_cmd, "login", "-u", task.info.username, "-p"]
            result = subprocess.run(
                cmd, input=task.info.password + "\n", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=60
            )
            
            if result.returncode == 0:
                self._log_message(task_id, "登录成功")
                self._update_progress(task_id, 20.0)
                return True
            else:
                self._set_task_failed(task_id, f"登录失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self._set_task_failed(task_id, "登录超时")
            return False
        except Exception as e:
            self._set_task_failed(task_id, f"登录异常: {str(e)}")
            return False
    
    def _list_files(self, task_id: str) -> bool:
        """列出远程文件"""
        task = self.tasks[task_id]
        
        try:
            # 切换到下载目录
            
            cmd = [self.lnd_cmd, "list", task.info.data_path]
            result = subprocess.run(
                cmd, cwd=task.download_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=120
            )
            
            if result.returncode == 0:
                # 保存文件列表
                with open(Path(task.download_dir) / "file_list.txt", "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                
                self._log_message(task_id, "文件列表获取成功")
                self._update_progress(task_id, 30.0)
                return True
            else:
                self._set_task_failed(task_id, f"列出文件失败: {result.stderr}")
                return False
                
        except Exception as e:
            self._set_task_failed(task_id, f"列出文件异常: {str(e)}")
            return False
    
    def _download_files(self, task_id: str) -> bool:
        """下载文件"""
        task = self.tasks[task_id]
        
        try:
            # 切换到下载目录
            
            cmd = [self.lnd_cmd, "cp", "-d", task.info.data_path, "./"]
            
            # 使用Popen实现实时输出
            process = subprocess.Popen(
                cmd, cwd=task.download_dir, stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1
            )
            
            progress_start = 30.0
            progress_range = 60.0  # 30% to 90%
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    line = output.strip()
                    self._log_message(task_id, line)
                    
                    # 简单的进度估算（可以根据实际输出优化）
                    if "%" in line:
                        try:
                            percent = float(line.split("%")[0].split()[-1])
                            progress = progress_start + (percent / 100.0) * progress_range
                            self._update_progress(task_id, progress)
                        except:
                            pass
            
            if process.returncode == 0:
                self._log_message(task_id, "文件下载完成")
                self._update_progress(task_id, 90.0)
                return True
            else:
                self._set_task_failed(task_id, "下载失败")
                return False
                
        except Exception as e:
            self._set_task_failed(task_id, f"下载异常: {str(e)}")
            return False
    
    def _validate_files(self, task_id: str):
        """验证下载的文件"""
        task = self.tasks[task_id]
        
        try:
            
            # 查找MD5文件
            md5_files = []
            for root, dirs, files in os.walk(task.download_dir):
                for file in files:
                    if file.endswith(".md5") or "md5" in file.lower():
                        md5_files.append(os.path.join(root, file))
            
            if md5_files:
                self._log_message(task_id, f"找到MD5文件: {', '.join(md5_files)}")
                
                for md5_file in md5_files:
                    md5_dir = os.path.dirname(md5_file)
                    md5_name = os.path.basename(md5_file)
                    
                    result = subprocess.run(
                        ["md5sum", "-c", md5_name], cwd=md5_dir, 
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
                    )
                    
                    if result.returncode == 0:
                        self._log_message(task_id, f"MD5验证通过: {md5_file}")
                    else:
                        self._log_message(task_id, f"MD5验证失败: {md5_file}")
                        return False
                    
            else:
                self._log_message(task_id, "未找到MD5文件")
            
            # 统计下载的文件
            file_count = 0
            for root, dirs, files in os.walk(task.download_dir):
                file_count += len(files)
            
            self._log_message(task_id, f"下载文件总数: {file_count}")
            self._update_progress(task_id, 100.0)
            return True
            
        except Exception as e:
            self._log_message(task_id, f"验证过程中出现警告: {str(e)}")
            return False
    
    def _update_task_status(self, task_id: str, status: DownloadStatus, step: str = ""):
        """更新任务状态"""
        task = self.tasks[task_id]
        task.status = status
        if step:
            task.current_step = step
        
        self._notify_status_change(task_id, task)
    
    def _update_progress(self, task_id: str, progress: float):
        """更新任务进度"""
        task = self.tasks[task_id]
        task.progress = min(100.0, max(0.0, progress))
        
        self._notify_status_change(task_id, task)
    
    def _log_message(self, task_id: str, message: str):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        
        task = self.tasks[task_id]
        task.log_messages.append(log_msg)
        
        # 保持日志数量在合理范围内
        if len(task.log_messages) > 1000:
            task.log_messages = task.log_messages[-800:]
        
        print(f"Task {task_id}: {log_msg}")
    
    def _set_task_failed(self, task_id: str, error_message: str):
        """设置任务失败"""
        task = self.tasks[task_id]
        task.status = DownloadStatus.FAILED
        task.error_message = error_message
        task.end_time = datetime.now()
        
        self._log_message(task_id, f"任务失败: {error_message}")
        self._notify_status_change(task_id, task)


def main():
    """测试函数"""
    # 这里可以添加测试代码
    pass


if __name__ == "__main__":
    main()
