#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件验证模块
用于验证下载文件的完整性
"""

import os
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class FileValidator:
    """文件验证器"""
    
    def __init__(self):
        pass
    
    def find_md5_files(self, directory: str) -> List[str]:
        """
        查找目录中的MD5文件
        
        Args:
            directory: 搜索目录
            
        Returns:
            MD5文件路径列表
        """
        md5_files = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return md5_files
        
        # 递归查找MD5文件
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                name_lower = file_path.name.lower()
                if (name_lower.endswith('.md5') or 
                    'md5' in name_lower or 
                    name_lower.startswith('md5')):
                    md5_files.append(str(file_path))
        
        return sorted(md5_files)
    
    def validate_with_md5_file(self, md5_file_path: str) -> Dict[str, bool]:
        """
        使用MD5文件验证
        
        Args:
            md5_file_path: MD5文件路径
            
        Returns:
            验证结果字典，键为文件名，值为验证结果
        """
        results = {}
        md5_file = Path(md5_file_path)
        
        if not md5_file.exists():
            return results
        
        # 切换到MD5文件所在目录
        md5_file = md5_file.resolve()
        
        try:
            # 使用md5sum命令验证
            result = subprocess.run(
                ['md5sum', '-c', md5_file.name],
                capture_output=True, text=True, cwd=md5_file.parent
            )
            
            # 解析输出
            for line in result.stdout.split('\n'):
                line = line.strip()
                if ': OK' in line:
                    filename = line.replace(': OK', '')
                    results[filename] = True
                elif ': FAILED' in line:
                    filename = line.replace(': FAILED', '')
                    results[filename] = False
            
            # 处理stderr中的错误信息
            for line in result.stderr.split('\n'):
                line = line.strip()
                if 'No such file or directory' in line:
                    # 提取文件名
                    parts = line.split(':')
                    if len(parts) > 1:
                        filename = parts[1].strip().split()[0]
                        results[filename] = False
                        
        except Exception as e:
            print(f"MD5验证错误: {e}")
        
        return results
    
    def calculate_file_md5(self, file_path: str) -> Optional[str]:
        """
        计算文件的MD5值
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5值字符串，失败返回None
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算MD5失败 {file_path}: {e}")
            return None
    
    def validate_files_manually(self, directory: str) -> Dict[str, str]:
        """
        手动验证文件（当没有MD5文件时）
        
        Args:
            directory: 目录路径
            
        Returns:
            文件MD5值字典
        """
        file_md5s = {}
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return file_md5s
        
        # 遍历所有文件
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and not file_path.name.lower().endswith('.md5'):
                relative_path = str(file_path.relative_to(dir_path))
                md5_value = self.calculate_file_md5(str(file_path))
                if md5_value:
                    file_md5s[relative_path] = md5_value
        
        return file_md5s
    
    def get_file_statistics(self, directory: str) -> Dict[str, any]:
        """
        获取目录文件统计信息
        
        Args:
            directory: 目录路径
            
        Returns:
            统计信息字典
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'largest_files': [],
            'empty_files': []
        }
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return stats
        
        file_sizes = []
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                stats['total_files'] += 1
                
                try:
                    file_size = file_path.stat().st_size
                    stats['total_size'] += file_size
                    
                    # 记录文件类型
                    suffix = file_path.suffix.lower()
                    if suffix:
                        stats['file_types'][suffix] = stats['file_types'].get(suffix, 0) + 1
                    else:
                        stats['file_types']['无扩展名'] = stats['file_types'].get('无扩展名', 0) + 1
                    
                    # 记录文件大小用于排序
                    relative_path = str(file_path.relative_to(dir_path))
                    file_sizes.append((relative_path, file_size))
                    
                    # 记录空文件
                    if file_size == 0:
                        stats['empty_files'].append(relative_path)
                        
                except Exception as e:
                    print(f"获取文件信息失败 {file_path}: {e}")
        
        # 获取最大的10个文件
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = file_sizes[:10]
        
        return stats
    
    def format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            格式化的大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def generate_validation_report(self, directory: str) -> str:
        """
        生成验证报告
        
        Args:
            directory: 目录路径
            
        Returns:
            验证报告文本
        """
        report_lines = []
        report_lines.append("=" * 50)
        report_lines.append("文件验证报告")
        report_lines.append("=" * 50)
        report_lines.append(f"验证目录: {directory}")
        report_lines.append(f"验证时间: {__import__('datetime').datetime.now()}")
        report_lines.append("")
        
        # 基本统计
        stats = self.get_file_statistics(directory)
        report_lines.append("基本统计:")
        report_lines.append(f"  文件总数: {stats['total_files']}")
        report_lines.append(f"  总大小: {self.format_size(stats['total_size'])}")
        report_lines.append("")
        
        # 文件类型分布
        if stats['file_types']:
            report_lines.append("文件类型分布:")
            for ext, count in sorted(stats['file_types'].items()):
                report_lines.append(f"  {ext}: {count} 个")
            report_lines.append("")
        
        # 最大文件
        if stats['largest_files']:
            report_lines.append("最大文件 (前10个):")
            for filename, size in stats['largest_files']:
                report_lines.append(f"  {filename}: {self.format_size(size)}")
            report_lines.append("")
        
        # 空文件
        if stats['empty_files']:
            report_lines.append("空文件:")
            for filename in stats['empty_files']:
                report_lines.append(f"  {filename}")
            report_lines.append("")
        
        # MD5验证
        md5_files = self.find_md5_files(directory)
        if md5_files:
            report_lines.append("MD5验证结果:")
            for md5_file in md5_files:
                report_lines.append(f"  MD5文件: {md5_file}")
                validation_results = self.validate_with_md5_file(md5_file)
                
                passed = sum(1 for v in validation_results.values() if v)
                failed = sum(1 for v in validation_results.values() if not v)
                
                report_lines.append(f"    验证通过: {passed} 个")
                report_lines.append(f"    验证失败: {failed} 个")
                
                if failed > 0:
                    report_lines.append("    失败文件:")
                    for filename, result in validation_results.items():
                        if not result:
                            report_lines.append(f"      {filename}")
            report_lines.append("")
        else:
            report_lines.append("MD5验证: 未找到MD5文件")
            report_lines.append("")
        
        report_lines.append("=" * 50)
        
        return "\n".join(report_lines)


def main():
    """测试函数"""
    validator = FileValidator()
    
    # 测试目录
    test_dir = "/tmp/test_validation"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建测试文件
    with open(f"{test_dir}/test.txt", "w") as f:
        f.write("Hello World")
    
    # 生成报告
    report = validator.generate_validation_report(test_dir)
    print(report)


if __name__ == "__main__":
    main()
