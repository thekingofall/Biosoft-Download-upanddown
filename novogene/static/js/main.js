// 主要JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initializePage();
});

function initializePage() {
    // 添加页面加载动画
    document.body.classList.add('fade-in');
    
    // 初始化提示工具
    initializeTooltips();
    
    // 初始化自动刷新
    initializeAutoRefresh();
    
    // 初始化键盘快捷键
    initializeKeyboardShortcuts();
    
    // 初始化表单验证
    initializeFormValidation();
}

function initializeTooltips() {
    // 如果使用Bootstrap 5，初始化tooltip
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeAutoRefresh() {
    // 如果页面包含需要自动刷新的元素，启动自动刷新
    const refreshElements = document.querySelectorAll('[data-auto-refresh]');
    refreshElements.forEach(element => {
        const interval = parseInt(element.getAttribute('data-auto-refresh')) || 5000;
        setInterval(() => {
            // 这里可以添加具体的刷新逻辑
            refreshElement(element);
        }, interval);
    });
}

function refreshElement(element) {
    // 刷新特定元素的内容
    const url = element.getAttribute('data-refresh-url');
    if (url) {
        fetch(url)
            .then(response => response.text())
            .then(html => {
                element.innerHTML = html;
            })
            .catch(error => {
                console.error('刷新元素失败:', error);
            });
    }
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+R 或 F5 - 刷新页面
        if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
            // 默认行为，不需要额外处理
            return;
        }
        
        // Ctrl+N - 新建任务
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/';
        }
        
        // Ctrl+L - 任务列表
        if (e.ctrlKey && e.key === 'l') {
            e.preventDefault();
            window.location.href = '/tasks';
        }
        
        // Escape - 关闭模态框或返回
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            if (modals.length === 0) {
                // 如果没有模态框，尝试返回上一页
                if (window.history.length > 1) {
                    window.history.back();
                }
            }
        }
    });
}

function initializeFormValidation() {
    // Bootstrap 5 表单验证
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// 通用工具函数
class Utils {
    // 格式化文件大小
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // 格式化时间
    static formatDuration(seconds) {
        if (seconds < 60) return seconds + '秒';
        if (seconds < 3600) return Math.floor(seconds / 60) + '分钟';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return hours + '小时' + (minutes > 0 ? minutes + '分钟' : '');
    }
    
    // 显示通知
    static showNotification(message, type = 'info', duration = 5000) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // 自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    // 复制到剪贴板
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            Utils.showNotification('已复制到剪贴板', 'success', 2000);
            return true;
        } catch (err) {
            console.error('复制失败:', err);
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                Utils.showNotification('已复制到剪贴板', 'success', 2000);
                return true;
            } catch (err2) {
                Utils.showNotification('复制失败', 'danger', 3000);
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    }
    
    // 确认对话框
    static confirm(message, title = '确认操作') {
        return new Promise((resolve) => {
            // 如果可用，使用原生确认框
            const result = window.confirm(message);
            resolve(result);
        });
    }
    
    // 延迟执行
    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // 防抖函数
    static debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }
    
    // 节流函数
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// API 调用包装器
class API {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API请求失败:', error);
            Utils.showNotification('网络请求失败', 'danger');
            throw error;
        }
    }
    
    static async get(url) {
        return this.request(url, { method: 'GET' });
    }
    
    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    
    static async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
    
    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// 任务管理相关函数
class TaskManager {
    static async getTaskStatus(taskId) {
        return API.get(`/api/task/${taskId}/status`);
    }
    
    static async cancelTask(taskId) {
        return API.post(`/api/task/${taskId}/cancel`, {});
    }
    
    static async removeTask(taskId) {
        return API.post(`/api/task/${taskId}/remove`, {});
    }
    
    static async getTaskLogs(taskId, start = 0, limit = 100) {
        return API.get(`/api/task/${taskId}/logs?start=${start}&limit=${limit}`);
    }
}

// 页面特定功能
const PageFeatures = {
    // 邮件解析页面
    emailParser: {
        validateEmail(text) {
            const requiredFields = ['登录账号', '登录密码', '数据路径'];
            return requiredFields.every(field => text.includes(field));
        },
        
        extractPreview(text) {
            const lines = text.split('\n').slice(0, 5);
            return lines.join('\n') + (text.split('\n').length > 5 ? '\n...' : '');
        }
    },
    
    // 任务状态页面
    taskStatus: {
        updateInterval: null,
        
        startUpdating(taskId) {
            this.updateInterval = setInterval(() => {
                this.updateStatus(taskId);
            }, 2000);
        },
        
        stopUpdating() {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        },
        
        async updateStatus(taskId) {
            try {
                const status = await TaskManager.getTaskStatus(taskId);
                this.renderStatus(status);
            } catch (error) {
                console.error('更新状态失败:', error);
            }
        },
        
        renderStatus(status) {
            // 更新DOM元素
            const elements = {
                progress: document.getElementById('progressBar'),
                progressText: document.getElementById('progressText'),
                currentStep: document.getElementById('currentStep'),
                statusBadge: document.getElementById('statusBadge')
            };
            
            if (elements.progress) {
                elements.progress.style.width = status.progress + '%';
            }
            
            if (elements.progressText) {
                elements.progressText.textContent = status.progress.toFixed(1) + '%';
            }
            
            if (elements.currentStep) {
                elements.currentStep.textContent = status.current_step || '等待中';
            }
            
            if (elements.statusBadge) {
                elements.statusBadge.textContent = status.status;
                elements.statusBadge.className = `badge bg-${this.getStatusColor(status.status)} fs-6`;
            }
        },
        
        getStatusColor(status) {
            const colors = {
                'pending': 'secondary',
                'logging_in': 'info',
                'listing': 'info',
                'downloading': 'primary',
                'validating': 'warning',
                'completed': 'success',
                'failed': 'danger',
                'cancelled': 'dark'
            };
            return colors[status] || 'secondary';
        }
    }
};

// 全局设置相关功能
const GlobalSettings = {
    modal: null,
    
    // 显示设置弹窗
    async show() {
        if (!this.modal) {
            this.modal = new bootstrap.Modal(document.getElementById('globalSettingsModal'));
        }
        
        // 加载当前设置
        await this.loadCurrentSettings();
        this.loadSystemInfo();
        
        this.modal.show();
    },
    
    // 加载当前设置
    async loadCurrentSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            
            // 填充表单
            document.getElementById('global_lnd_path').value = settings.lnd_cmd_path || '';
            document.getElementById('global_download_dir').value = settings.default_download_dir || '';
            document.getElementById('global_max_tasks').value = settings.max_concurrent_tasks || 3;
            document.getElementById('global_task_timeout').value = settings.task_timeout || 3600;
            document.getElementById('global_auto_validate').checked = settings.auto_validate !== false;
            document.getElementById('global_generate_report').checked = settings.generate_report !== false;
            
        } catch (error) {
            console.error('加载设置失败:', error);
            Utils.showNotification('加载设置失败', 'danger');
        }
    },
    
    // 加载系统信息
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/settings/system-info');
            const info = await response.json();
            
            const systemInfoDiv = document.getElementById('global_system_info');
            systemInfoDiv.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>操作系统:</strong> ${info.platform || 'Unknown'}<br>
                        <strong>架构:</strong> ${info.architecture || 'Unknown'}<br>
                        <strong>Python版本:</strong> ${info.python_version || 'Unknown'}
                    </div>
                    <div class="col-md-6">
                        <strong>用户目录:</strong> ${info.home_dir || 'Unknown'}<br>
                        <strong>当前目录:</strong> ${info.current_dir || 'Unknown'}<br>
                        <strong>可用空间:</strong> ${Utils.formatFileSize(info.disk_usage?.free || 0)}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('加载系统信息失败:', error);
            document.getElementById('global_system_info').innerHTML = '<span class="text-danger">加载系统信息失败</span>';
        }
    },
    
    // 保存设置
    async save() {
        const settings = {
            lnd_cmd_path: document.getElementById('global_lnd_path').value.trim(),
            default_download_dir: document.getElementById('global_download_dir').value.trim(),
            max_concurrent_tasks: parseInt(document.getElementById('global_max_tasks').value),
            task_timeout: parseInt(document.getElementById('global_task_timeout').value),
            auto_validate: document.getElementById('global_auto_validate').checked,
            generate_report: document.getElementById('global_generate_report').checked,
            first_run: false
        };
        
        // 基本验证
        if (!settings.lnd_cmd_path || !settings.default_download_dir) {
            Utils.showNotification('请填写必要的路径信息', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.modal.hide();
                Utils.showNotification('设置保存成功', 'success');
            } else {
                Utils.showNotification(result.message || '保存设置失败', 'danger');
            }
            
        } catch (error) {
            console.error('保存设置失败:', error);
            Utils.showNotification('保存设置时发生错误', 'danger');
        }
    },
    
    // 重置设置
    async reset() {
        if (!confirm('确定要重置为默认设置吗？这将覆盖当前的配置。')) {
            return;
        }
        
        try {
            const response = await fetch('/api/settings/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                await this.loadCurrentSettings();
                Utils.showNotification('设置已重置为默认值', 'success');
            } else {
                Utils.showNotification(result.message || '重置设置失败', 'danger');
            }
            
        } catch (error) {
            console.error('重置设置失败:', error);
            Utils.showNotification('重置设置时发生错误', 'danger');
        }
    },
    
    // 验证LND路径
    async validateLndPath() {
        const path = document.getElementById('global_lnd_path').value.trim();
        const validationDiv = document.getElementById('global_lnd_validation');
        
        if (!path) {
            this.showValidationResult(validationDiv, false, '请输入LND命令路径');
            return;
        }
        
        try {
            const response = await fetch('/api/settings/validate-lnd', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            });
            
            const result = await response.json();
            this.showValidationResult(validationDiv, result.valid, result.message);
            
        } catch (error) {
            console.error('验证LND路径失败:', error);
            this.showValidationResult(validationDiv, false, '验证过程中出现错误');
        }
    },
    
    // 验证下载目录
    async validateDownloadDir() {
        const path = document.getElementById('global_download_dir').value.trim();
        const validationDiv = document.getElementById('global_dir_validation');
        
        if (!path) {
            this.showValidationResult(validationDiv, false, '请输入下载目录路径');
            return;
        }
        
        try {
            const response = await fetch('/api/settings/validate-dir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            });
            
            const result = await response.json();
            let message = result.message;
            
            if (result.valid && result.space_available) {
                message += ` (可用空间: ${Utils.formatFileSize(result.space_available)})`;
            }
            
            this.showValidationResult(validationDiv, result.valid, message);
            
        } catch (error) {
            console.error('验证下载目录失败:', error);
            this.showValidationResult(validationDiv, false, '验证过程中出现错误');
        }
    },
    
    // 显示验证结果
    showValidationResult(element, isValid, message) {
        element.style.display = 'block';
        element.className = isValid ? 'validation-result validation-success' : 'validation-result validation-error';
        element.innerHTML = `<i class="bi bi-${isValid ? 'check-circle' : 'x-circle'}"></i> ${message}`;
    }
};

// 全局函数，供HTML调用
function showSettingsModal() {
    GlobalSettings.show();
}

function saveGlobalSettings() {
    GlobalSettings.save();
}

function resetGlobalSettings() {
    GlobalSettings.reset();
}

function validateGlobalLndPath() {
    GlobalSettings.validateLndPath();
}

function validateGlobalDownloadDir() {
    GlobalSettings.validateDownloadDir();
}

// 全局暴露工具类
window.Utils = Utils;
window.API = API;
window.TaskManager = TaskManager;
window.PageFeatures = PageFeatures;
window.GlobalSettings = GlobalSettings;
