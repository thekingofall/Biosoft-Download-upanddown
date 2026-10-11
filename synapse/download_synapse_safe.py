#!/usr/bin/env python3
"""
Synapse 数据下载脚本 - 递归下载 Synapse 数据集

使用方法:
    1. 设置环境变量 SYNAPSE_AUTH_TOKEN 或创建 .env 文件
    2. 修改 SYNAPSE_ID 为你要下载的数据集 ID
    3. 运行: python download_synapse_safe.py

会自动:
1. 检查 synapseclient 依赖
2. 登录 Synapse
3. 递归下载数据集中的所有文件
"""

import argparse
import sys
import os

# ============================================
# 配置 - 修改这里
# ============================================
SYNAPSE_ID = "syn61592786"  # 要下载的 Synapse ID
DOWNLOAD_DIR = "./downloaded_data"  # 下载目录

# ============================================
# 获取认证令牌
# ============================================
def get_auth_token():
    """
    从环境变量或 .env 文件获取认证令牌
    优先级: 环境变量 > .env 文件
    """
    # 先检查环境变量
    token = os.environ.get("SYNAPSE_AUTH_TOKEN")
    if token:
        return token
    
    # 尝试从 .env 文件读取
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("SYNAPSE_AUTH_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    
    return None

# ============================================
# 自动安装依赖
# ============================================
# ============================================
# 递归下载函数
# ============================================
def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes > 1e9:
        return f"{size_bytes/1e9:.2f} GB"
    elif size_bytes > 1e6:
        return f"{size_bytes/1e6:.2f} MB"
    elif size_bytes > 1e3:
        return f"{size_bytes/1e3:.2f} KB"
    else:
        return f"{size_bytes} B"

def download_recursive(syn, synapse_id, local_path, indent="", stats=None):
    """
    递归下载 Synapse 实体
    
    参数:
        syn: Synapse 客户端
        synapse_id: Synapse ID
        local_path: 本地保存路径
        indent: 缩进（用于显示层级）
        stats: 统计信息字典
    """
    if stats is None:
        stats = {"files": 0, "folders": 0, "failed": 0, "total_size": 0}
    
    # 创建本地目录
    os.makedirs(local_path, exist_ok=True)
    
    # 获取子项
    try:
        children = list(syn.getChildren(synapse_id))
    except Exception as e:
        print(f"{indent}❌ 无法获取子项: {e}")
        stats["failed"] += 1
        return stats
    
    for child in children:
        child_id = child['id']
        child_name = child['name']
        child_type = child['type']
        if child_name in (".", "..") or "/" in child_name or "\\" in child_name or ":" in child_name:
            print(f"{indent}Invalid entity name: {child_id}")
            stats["failed"] += 1
            continue
        
        if child_type == 'org.sagebionetworks.repo.model.Folder':
            # 是文件夹，递归下载
            print(f"{indent}📁 {child_name}/")
            stats["folders"] += 1
            child_local_path = os.path.join(local_path, child_name)
            download_recursive(syn, child_id, child_local_path, indent + "  ", stats)
            
        elif child_type == 'org.sagebionetworks.repo.model.FileEntity':
            # 是文件，下载
            size_str = ""
            if 'dataFileSizeBytes' in child:
                size_str = f" ({format_size(child['dataFileSizeBytes'])})"
                stats["total_size"] += child['dataFileSizeBytes']
            
            print(f"{indent}📄 {child_name}{size_str}", end=" ")
            sys.stdout.flush()
            
            try:
                syn.get(child_id, downloadLocation=local_path)
                print("✅")
                stats["files"] += 1
            except Exception as e:
                print(f"❌ {e}")
                stats["failed"] += 1
        else:
            # 其他类型
            print(f"{indent}❓ {child_name} (类型: {child_type})")
    
    return stats

# ============================================
# 主程序
# ============================================
def main(argv=None):
    global SYNAPSE_ID, DOWNLOAD_DIR
    parser = argparse.ArgumentParser(description="Recursively download a Synapse project or folder")
    parser.add_argument("--synapse-id", default=SYNAPSE_ID)
    parser.add_argument("--output", default=DOWNLOAD_DIR)
    args = parser.parse_args(argv)
    SYNAPSE_ID, DOWNLOAD_DIR = args.synapse_id, args.output
    print("=" * 60)
    print("🧬 Synapse 数据下载工具")
    print("   数据集: " + SYNAPSE_ID)
    print("   模式: 递归下载所有文件")
    print("=" * 60)
    
    # 获取认证令牌
    auth_token = get_auth_token()
    if not auth_token:
        print("\n❌ 错误: 未找到 Synapse 认证令牌!")
        print("\n请设置环境变量或创建 .env 文件:")
        print("  方法1: 设置环境变量")
        print("    Windows: set SYNAPSE_AUTH_TOKEN=your_token_here")
        print("    Linux/Mac: export SYNAPSE_AUTH_TOKEN=your_token_here")
        print("\n  方法2: 创建 .env 文件")
        print("    在脚本目录创建 .env 文件，内容:")
        print("    SYNAPSE_AUTH_TOKEN=your_token_here")
        print("\n获取令牌: https://www.synapse.org/#!PersonalAccessTokens:")
        return 1
    
    # 检查依赖
    print("\n[1/4] 检查依赖...")
    try:
        import synapseclient
    except ImportError:
        print("Install dependencies: python -m pip install -r synapse/requirements.txt")
        return 1
    
    # 创建下载目录
    print(f"\n[2/4] 创建下载目录: {DOWNLOAD_DIR}")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # 登录
    print("\n[3/4] 登录 Synapse...")
    syn = synapseclient.Synapse()
    
    try:
        syn.login(authToken=auth_token)
        print("✅ 登录成功!")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        print("\n可能的原因:")
        print("1. 请检查网络和 Synapse 服务连接")
        print("2. Token 已过期或无效")
        return 1
    
    # 获取数据集信息并下载
    print(f"\n[4/4] 获取 {SYNAPSE_ID} 并递归下载...")
    
    try:
        # 获取实体信息
        entity = syn.get(SYNAPSE_ID, downloadFile=False)
        print(f"名称: {entity.name}")
        print(f"类型: {entity.__class__.__name__}")
        
        # 开始递归下载
        print("\n" + "=" * 60)
        print("开始递归下载所有文件...")
        print("=" * 60 + "\n")
        
        stats = download_recursive(syn, SYNAPSE_ID, DOWNLOAD_DIR)
        
        print("\n" + "=" * 60)
        print("下载结束" if stats["failed"] else "🎉 下载完成!")
        print(f"📊 统计:")
        print(f"   - 文件夹: {stats['folders']} 个")
        print(f"   - 文件: {stats['files']} 个")
        print(f"   - 失败: {stats['failed']} 个")
        print(f"   - 总大小: {format_size(stats['total_size'])}")
        print(f"📂 文件位置: {os.path.abspath(DOWNLOAD_DIR)}")
        print("=" * 60)
        return 1 if stats["failed"] else 0
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

