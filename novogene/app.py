#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask Web应用主模块
"""

import os
import sys
import subprocess
from pathlib import Path
import logging
import logging.config
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config, DownloadConfig, LOGGING_CONFIG
from scripts.email_parser import EmailParser, NovoGeneInfo
from scripts.download_manager import DownloadManager, DownloadStatus
from scripts.file_validator import FileValidator
from scripts.settings_manager import settings_manager

# 配置日志
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('novogene_download')

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 全局对象
email_parser = EmailParser()

# 根据用户设置初始化下载管理器
user_settings = settings_manager.get_all()
lnd_path = user_settings.get('lnd_cmd_path', DownloadConfig.LND_CMD_PATH)
download_manager = DownloadManager(lnd_path)
file_validator = FileValidator()


@app.route('/')
def index():
    """主页"""
    # 检查是否需要显示初始设置弹窗
    is_first_run = settings_manager.is_first_run()
    current_settings = settings_manager.get_all()
    
    return render_template('index.html', 
                         is_first_run=is_first_run, 
                         current_settings=current_settings)


@app.route('/parse', methods=['POST'])
def parse_email():
    """解析邮件内容"""
    try:
        email_text = request.form.get('email_text', '').strip()
        
        if not email_text:
            flash('请输入邮件内容', 'error')
            return redirect(url_for('index'))
        
        # 解析邮件
        info = email_parser.parse_email_text(email_text)
        
        if not info:
            flash('邮件解析失败，请检查邮件格式', 'error')
            return redirect(url_for('index'))
        
        # 验证信息
        errors = email_parser.validate_info(info)
        if errors:
            error_msgs = ["{}: {}".format(field, msg) for field, msg in errors.items()]
            flash('验证失败: {}'.format("; ".join(error_msgs)), 'error')
            return redirect(url_for('index'))
        
        # 格式化显示信息
        display_info = email_parser.format_for_display(info)
        current_settings = settings_manager.get_all()
        
        return render_template('download.html', 
                             info=display_info, 
                             raw_info=info.__dict__,
                             current_settings=current_settings)
        
    except ValueError as e:
        flash(f'解析错误: {str(e)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"解析邮件时发生错误: {e}")
        flash('解析过程中发生错误，请重试', 'error')
        return redirect(url_for('index'))


@app.route('/download', methods=['POST'])
def start_download():
    """开始下载"""
    try:
        # 获取表单数据
        form_data = request.form.to_dict()
        
        # 重构NovoGeneInfo对象
        info = NovoGeneInfo(
            data_path=form_data.get('data_path', ''),
            username=form_data.get('username', ''),
            password=form_data.get('password', ''),
            release_date=form_data.get('release_date', ''),
            expire_date=form_data.get('expire_date', ''),
            total_size=form_data.get('total_size', ''),
            sample_count=form_data.get('sample_count', ''),
            sample_names=form_data.get('sample_names', ''),
            batch_info=form_data.get('batch_info', ''),
            notes=form_data.get('notes', '')
        )
        
        # 获取下载目录，优先使用用户设置
        user_settings = settings_manager.get_all()
        default_dir = user_settings.get('default_download_dir', DownloadConfig.DEFAULT_DOWNLOAD_DIR)
        download_dir = form_data.get('download_dir', default_dir)
        if not download_dir:
            download_dir = default_dir
        
        # 创建任务特定的下载目录
        task_dir = os.path.join(download_dir, f"{info.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # 创建下载任务
        task_id = download_manager.create_task(info, task_dir)
        
        # 启动下载
        if download_manager.start_download(task_id):
            flash(f'下载任务已启动，任务ID: {task_id}', 'success')
            return redirect(url_for('task_status', task_id=task_id))
        else:
            flash('启动下载任务失败', 'error')
            return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"启动下载时发生错误: {e}")
        flash('启动下载时发生错误，请重试', 'error')
        return redirect(url_for('index'))


@app.route('/tasks')
def task_list():
    """任务列表页面"""
    tasks = download_manager.get_all_tasks()
    return render_template('task_list.html', tasks=tasks)


@app.route('/task/<task_id>')
def task_status(task_id):
    """任务状态页面"""
    task = download_manager.get_task(task_id)
    if not task:
        flash('任务不存在', 'error')
        return redirect(url_for('task_list'))
    
    return render_template('task_status.html', task=task, task_id=task_id)


@app.route('/api/task/<task_id>/status')
def api_task_status(task_id):
    """获取任务状态API"""
    task = download_manager.get_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify({
        'task_id': task_id,
        'status': task.status.value,
        'progress': task.progress,
        'current_step': task.current_step,
        'start_time': task.start_time.isoformat() if task.start_time else None,
        'end_time': task.end_time.isoformat() if task.end_time else None,
        'error_message': task.error_message,
        'log_messages': task.log_messages[-50:],  # 只返回最近50条日志
        'is_finished': task.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
    })


@app.route('/api/task/<task_id>/cancel', methods=['POST'])
def api_cancel_task(task_id):
    """取消任务API"""
    if download_manager.cancel_download(task_id):
        return jsonify({'success': True, 'message': '任务已取消'})
    else:
        return jsonify({'success': False, 'message': '取消任务失败'}), 400


@app.route('/api/task/<task_id>/remove', methods=['POST'])
def api_remove_task(task_id):
    """删除任务API"""
    if download_manager.remove_task(task_id):
        return jsonify({'success': True, 'message': '任务已删除'})
    else:
        return jsonify({'success': False, 'message': '删除任务失败'}), 400


@app.route('/api/task/<task_id>/logs')
def api_task_logs(task_id):
    """获取任务日志API"""
    task = download_manager.get_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    # 获取日志范围
    start = request.args.get('start', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    logs = task.log_messages[start:start+limit]
    
    return jsonify({
        'logs': logs,
        'total': len(task.log_messages),
        'start': start,
        'limit': limit
    })


@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """获取当前设置"""
    settings = settings_manager.get_all()
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """保存设置"""
    try:
        data = request.get_json()
        
        # 创建新的设置字典
        new_settings = {
            'lnd_cmd_path': data.get('lnd_cmd_path', ''),
            'default_download_dir': data.get('default_download_dir', ''),
            'max_concurrent_tasks': int(data.get('max_concurrent_tasks', 3)),
            'auto_validate': bool(data.get('auto_validate', True)),
            'generate_report': bool(data.get('generate_report', True)),
            'send_notification': bool(data.get('send_notification', False)),
            'first_run': False
        }
        
        # 基本验证
        if not new_settings['lnd_cmd_path'] or not new_settings['default_download_dir']:
            return jsonify({
                'success': False,
                'errors': {'general': '必填字段不能为空'}
            }), 400
        
        # 保存设置
        if settings_manager.update(new_settings):
            # 更新全局下载管理器
            global download_manager
            download_manager = DownloadManager(new_settings['lnd_cmd_path'])
            
            return jsonify({
                'success': True,
                'message': '设置保存成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '设置保存失败'
            }), 500
            
    except Exception as e:
        logger.error("保存设置时发生错误: {}".format(e))
        return jsonify({
            'success': False,
            'message': '保存设置时发生错误'
        }), 500


@app.route('/api/settings/validate', methods=['POST'])
def api_validate_settings():
    """验证设置"""
    try:
        data = request.get_json()
        
        # 基本验证
        lnd_path = data.get('lnd_cmd_path', '').strip()
        download_dir = data.get('default_download_dir', '').strip()
        
        errors = {}
        
        if not lnd_path:
            errors['lnd_cmd_path'] = 'LND命令路径不能为空'
        elif not os.path.exists(lnd_path):
            errors['lnd_cmd_path'] = 'LND命令文件不存在'
        elif not os.access(lnd_path, os.X_OK):
            errors['lnd_cmd_path'] = 'LND命令文件不可执行'
        
        if not download_dir:
            errors['default_download_dir'] = '下载目录不能为空'
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })
        
    except Exception as e:
        logger.error("验证设置时发生错误: {}".format(e))
        return jsonify({
            'valid': False,
            'errors': {'general': '验证过程中发生错误'}
        }), 500


@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    """重置设置为默认值"""
    try:
        if settings_manager.reset_to_default():
            # 重新初始化下载管理器
            global download_manager
            default_settings = settings_manager.get_all()
            download_manager = DownloadManager(default_settings.get('lnd_cmd_path', DownloadConfig.LND_CMD_PATH))
            
            return jsonify({
                'success': True,
                'message': '设置已重置为默认值'
            })
        else:
            return jsonify({
                'success': False,
                'message': '重置设置失败'
            }), 500
    except Exception as e:
        logger.error("重置设置时发生错误: {}".format(e))
        return jsonify({
            'success': False,
            'message': '重置设置时发生错误'
        }), 500


@app.route('/api/settings/check-first-run')
def api_check_first_run():
    """检查是否为首次运行"""
    is_first_run = settings_manager.is_first_run()
    return jsonify({
        'first_run': is_first_run
    })


@app.route('/api/settings/system-info')
def api_system_info():
    """获取系统信息"""
    import platform
    import psutil
    import sys
    
    try:
        # 获取磁盘使用情况
        disk_usage = psutil.disk_usage('/')
        
        system_info = {
            'platform': platform.system() + ' ' + platform.release(),
            'architecture': platform.machine(),
            'python_version': sys.version.split()[0],
            'home_dir': os.path.expanduser('~'),
            'current_dir': os.getcwd(),
            'disk_usage': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free
            }
        }
        
        return jsonify(system_info)
    except Exception as e:
        logger.error("获取系统信息时发生错误: {}".format(e))
        return jsonify({
            'error': '获取系统信息失败'
        }), 500


@app.route('/api/settings/validate-lnd', methods=['POST'])
def api_validate_lnd():
    """验证LND命令路径"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({
                'valid': False,
                'message': '路径不能为空'
            })
        
        # 检查文件是否存在
        if not os.path.exists(path):
            return jsonify({
                'valid': False,
                'message': '文件不存在'
            })
        
        # 检查是否为文件
        if not os.path.isfile(path):
            return jsonify({
                'valid': False,
                'message': '路径不是文件'
            })
        
        # 检查是否可执行
        if not os.access(path, os.X_OK):
            return jsonify({
                'valid': False,
                'message': '文件没有执行权限'
            })
        
        # 尝试执行版本命令测试
        try:
            result = subprocess.run(
                [path, '--version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                universal_newlines=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                return jsonify({
                    'valid': True,
                    'message': 'LND命令验证成功'
                })
            else:
                return jsonify({
                    'valid': False,
                    'message': '命令执行失败，可能不是有效的LND程序'
                })
        except subprocess.TimeoutExpired:
            return jsonify({
                'valid': False,
                'message': '命令执行超时'
            })
        except Exception as e:
            return jsonify({
                'valid': False,
                'message': '命令测试失败: {}'.format(str(e))
            })
            
    except Exception as e:
        logger.error("验证LND路径时发生错误: {}".format(e))
        return jsonify({
            'valid': False,
            'message': '验证过程中发生错误'
        }), 500


@app.route('/api/settings/validate-dir', methods=['POST'])
def api_validate_dir():
    """验证下载目录"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({
                'valid': False,
                'message': '路径不能为空'
            })
        
        try:
            # 尝试创建目录
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # 检查写权限
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                
                # 获取磁盘空间信息
                import psutil
                disk_usage = psutil.disk_usage(str(dir_path))
                
                return jsonify({
                    'valid': True,
                    'message': '目录验证成功',
                    'space_available': disk_usage.free
                })
                
            except Exception:
                return jsonify({
                    'valid': False,
                    'message': '目录没有写权限'
                })
                
        except Exception as e:
            return jsonify({
                'valid': False,
                'message': '无法创建目录: {}'.format(str(e))
            })
            
    except Exception as e:
        logger.error("验证下载目录时发生错误: {}".format(e))
        return jsonify({
            'valid': False,
            'message': '验证过程中发生错误'
        }), 500


@app.route('/validate/<task_id>')
def validate_files(task_id):
    """文件验证页面"""
    task = download_manager.get_task(task_id)
    if not task:
        flash('任务不存在', 'error')
        return redirect(url_for('task_list'))
    
    if task.status != DownloadStatus.COMPLETED:
        flash('任务未完成，无法验证文件', 'warning')
        return redirect(url_for('task_status', task_id=task_id))
    
    # 生成验证报告
    report = file_validator.generate_validation_report(task.download_dir)
    
    return render_template('validation_result.html', 
                         task=task, 
                         task_id=task_id, 
                         report=report)


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message='页面未找到'), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {error}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message='内部服务器错误'), 500


@app.template_filter('datetime')
def datetime_filter(dt):
    """日期时间格式化过滤器"""
    if dt is None:
        return '未开始'
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    return dt.strftime('%Y-%m-%d %H:%M:%S')


@app.template_filter('file_size')
def file_size_filter(size_str):
    """文件大小格式化过滤器"""
    if not size_str or size_str == '未提供':
        return size_str
    return size_str


@app.template_filter('status_badge')
def status_badge_filter(status):
    """状态徽章样式过滤器"""
    status_map = {
        DownloadStatus.PENDING.value: 'secondary',
        DownloadStatus.LOGGING_IN.value: 'info',
        DownloadStatus.LISTING.value: 'info',
        DownloadStatus.DOWNLOADING.value: 'primary',
        DownloadStatus.VALIDATING.value: 'warning',
        DownloadStatus.COMPLETED.value: 'success',
        DownloadStatus.FAILED.value: 'danger',
        DownloadStatus.CANCELLED.value: 'dark'
    }
    return status_map.get(status, 'secondary')


def main():
    """主函数"""
    logger.info("启动Novogene下载管理器")
    logger.info(f"下载目录: {DownloadConfig.DEFAULT_DOWNLOAD_DIR}")
    logger.info(f"LND命令路径: {DownloadConfig.LND_CMD_PATH}")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )


if __name__ == '__main__':
    main()
