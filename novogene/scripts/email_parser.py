#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
邮件解析模块
用于解析诺禾云邮件中的下载信息
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class NovoGeneInfo:
    """诺禾云下载信息数据类"""
    data_path: str
    username: str
    password: str
    release_date: str
    expire_date: str
    total_size: str
    sample_count: str
    sample_names: str
    batch_info: str = ""
    notes: str = ""


class EmailParser:
    """邮件解析器"""
    
    def __init__(self):
        self.patterns = {
            'data_path': r'数据路径为[:：]\s*(.+?)(?:\n|$)',
            'username': r'登录账号[:：]\s*(.+?)(?:\n|$)',
            'password': r'登录密码[:：]\s*(.+?)(?:\n|$)',
            'release_date': r'数据释放日期[:：]\s*(.+?)(?:\n|$)',
            'expire_date': r'数据有效期至[:：]\s*(.+?)(?:\n|$)',
            'total_size': r'交付文件总大小[:：]\s*(.+?)(?:\n|$)',
            'sample_count': r'样品个数[:：]\s*(.+?)(?:\n|$)',
            'sample_names': r'样品名称[:：]\s*(.+?)(?:\n|$)',
            'batch_info': r'送样批次信息[:：]\s*(.+?)(?:\n|$)',
            'notes': r'备注信息[:：]\s*(.+?)(?:\n|$)'
        }
    
    def parse_email_text(self, email_text: str) -> Optional[NovoGeneInfo]:
        """
        解析邮件文本
        
        Args:
            email_text: 邮件内容文本
            
        Returns:
            NovoGeneInfo对象或None
        """
        if not email_text.strip():
            return None
        
        # 清理文本
        email_text = email_text.strip()
        
        # 提取各字段
        extracted_data = {}
        for field, pattern in self.patterns.items():
            match = re.search(pattern, email_text, re.MULTILINE)
            if match:
                extracted_data[field] = match.group(1).strip()
            else:
                extracted_data[field] = ""
        
        # 验证必要字段
        required_fields = ['data_path', 'username', 'password']
        missing_fields = [field for field in required_fields 
                         if not extracted_data.get(field)]
        
        if missing_fields:
            raise ValueError(f"缺少必要字段: {', '.join(missing_fields)}")
        
        # 格式化数据路径为OSS路径
        data_path = extracted_data['data_path']
        if not data_path.startswith('oss://'):
            # 将相对路径转换为OSS路径
            if data_path.startswith('CP'):
                data_path = f"oss://{data_path}"
            else:
                # 假设是完整路径但缺少oss://前缀
                data_path = f"oss://CP2024121200080/H101SC24127971/RSSQ01804/X101SC24127971-Z01/{data_path}/"
        
        return NovoGeneInfo(
            data_path=data_path,
            username=extracted_data['username'],
            password=extracted_data['password'],
            release_date=extracted_data['release_date'],
            expire_date=extracted_data['expire_date'],
            total_size=extracted_data['total_size'],
            sample_count=extracted_data['sample_count'],
            sample_names=extracted_data['sample_names'],
            batch_info=extracted_data['batch_info'],
            notes=extracted_data['notes']
        )
    
    def validate_info(self, info: NovoGeneInfo) -> Dict[str, str]:
        """
        验证解析的信息
        
        Args:
            info: NovoGeneInfo对象
            
        Returns:
            验证错误字典，键为字段名，值为错误信息
        """
        errors = {}
        
        # 验证用户名格式
        if not re.match(r'^X\d+SC\d+-Z\d+-[A-Z]\d+$', info.username):
            errors['username'] = '用户名格式不正确'
        
        # 验证密码
        if len(info.password) < 6:
            errors['password'] = '密码长度至少6位'
        
        # 验证数据路径
        if not info.data_path.startswith('oss://'):
            errors['data_path'] = '数据路径格式不正确'
        
        # 验证日期格式
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if info.release_date and not re.match(date_pattern, info.release_date):
            errors['release_date'] = '发布日期格式不正确'
        
        if info.expire_date and not re.match(date_pattern, info.expire_date):
            errors['expire_date'] = '到期日期格式不正确'
        
        return errors
    
    def format_for_display(self, info: NovoGeneInfo) -> Dict[str, str]:
        """
        格式化信息用于界面显示
        
        Args:
            info: NovoGeneInfo对象
            
        Returns:
            格式化后的信息字典
        """
        return {
            '数据路径': info.data_path,
            '登录账号': info.username,
            '登录密码': info.password,
            '数据释放日期': info.release_date or '未提供',
            '数据有效期至': info.expire_date or '未提供',
            '交付文件总大小': info.total_size or '未提供',
            '样品个数': info.sample_count or '未提供',
            '样品名称': info.sample_names or '未提供',
            '送样批次信息': info.batch_info or '未提供',
            '备注信息': info.notes or '无'
        }


def main():
    """测试函数"""
    # 测试邮件文本
    test_email = """
    数据路径为：CP2024121200080/H101SC24127971/RSSQ01804/X101SC24127971-Z01/X101SC24127971-Z01-J083/
    登录账号：X101SC24127971-Z01-J083
    登录密码：cfyyu3cy
    数据释放日期：2025-08-05
    数据有效期至：2025-09-04
    交付文件总大小: 7.75 G;
    样品个数: 5 个;
    样品名称: TCRAB_AD,smRNA_8,smRNA_5,smRNA_7,smRNA_6;
    """
    
    parser = EmailParser()
    try:
        info = parser.parse_email_text(test_email)
        if info:
            print("解析成功:")
            display_info = parser.format_for_display(info)
            for key, value in display_info.items():
                print(f"{key}: {value}")
            
            errors = parser.validate_info(info)
            if errors:
                print("\n验证错误:")
                for field, error in errors.items():
                    print(f"{field}: {error}")
            else:
                print("\n验证通过")
        else:
            print("解析失败")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
