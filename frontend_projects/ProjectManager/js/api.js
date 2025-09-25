/**
 * API客户端
 * 负责与后端API网关通信
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8050', apiPrefix = '/api/v1') {
        this.baseURL = baseURL;
        this.apiPrefix = apiPrefix;
        this.websocket = null;
        this.wsCallbacks = new Map();
        this.wsCallbackId = 0;
    }

    /**
     * 发送HTTP请求
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${this.apiPrefix}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    /**
     * GET请求
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * POST请求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * 健康检查
     */
    async healthCheck() {
        try {
            return await this.get('/health');
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }

    /**
     * 获取系统信息
     */
    async getInfo() {
        try {
            return await this.get('/info');
        } catch (error) {
            return { error: error.message };
        }
    }

    /**
     * 项目管理API
     */
    async getProjectStatus(projectName = null) {
        const endpoint = projectName 
            ? `/project_manager/get_status?project_name=${projectName}`
            : '/project_manager/get_status';
        return this.post(endpoint);
    }

    async startProject(projectName, component = 'all') {
        return this.post('/project_manager/start_project', {
            project_name: projectName,
            component: component
        });
    }

    async stopProject(projectName, component = 'all') {
        return this.post('/project_manager/stop_project', {
            project_name: projectName,
            component: component
        });
    }

    async restartProject(projectName, component = 'all') {
        return this.post('/project_manager/restart_project', {
            project_name: projectName,
            component: component
        });
    }

    async getPortUsage() {
        return this.post('/project_manager/get_ports');
    }

    async performHealthCheck() {
        return this.post('/project_manager/health_check');
    }
    
    /**
     * 项目管理API
     */
    async getManagedProjects() {
        return this.post('/project_manager/get_managed_projects');
    }

    async importProject(formData) {
        const url = `${this.baseURL}${this.apiPrefix}/project_manager/import_project`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData, // 直接使用FormData，不需要JSON序列化
                // 不设置Content-Type，让浏览器自动设置multipart/form-data
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('导入项目失败:', error);
            throw error;
        }
    }

    /**
     * 将zip嵌入PNG图片
     * 后端函数：project_manager.embed_zip_into_image
     */
    async embedZipIntoImage(formData) {
        const url = `${this.baseURL}${this.apiPrefix}/project_manager/embed_zip_into_image`;
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData, // multipart/form-data 自动由浏览器设置
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || data.message || `HTTP ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error('嵌入zip到图片失败:', error);
            throw error;
        }
    }

    /**
     * 从PNG图片反嵌入zip并导入项目
     * 后端函数：project_manager.import_project_from_image
     */
    async importProjectFromImage(formData) {
        const url = `${this.baseURL}${this.apiPrefix}/project_manager/import_project_from_image`;
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || data.message || `HTTP ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error('从图片导入项目失败:', error);
            throw error;
        }
    }

    async deleteProject(projectName) {
        return this.post('/project_manager/delete_project', {
            project_name: projectName
        });
    }

    async updateProjectPorts(projectName, ports) {
        return this.post('/project_manager/update_ports', {
            project_name: projectName,
            ports: ports
        });
    }

    async installProjectDependencies(projectName) {
        return this.post('/project_manager/install_project', {
            project_name: projectName
        });
    }

    /**
     * WebSocket连接
     */
    connectWebSocket() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            return;
        }

        const wsURL = this.baseURL.replace('http', 'ws') + '/ws';
        this.websocket = new WebSocket(wsURL);

        this.websocket.onopen = () => {
            console.log('WebSocket连接已建立');
        };

        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('WebSocket消息解析失败:', error);
            }
        };

        this.websocket.onclose = () => {
            console.log('WebSocket连接已关闭');
            // 5秒后尝试重连
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket错误:', error);
        };
    }

    /**
     * 处理WebSocket消息
     */
    handleWebSocketMessage(data) {
        if (data.callback_id && this.wsCallbacks.has(data.callback_id)) {
            const callback = this.wsCallbacks.get(data.callback_id);
            callback(data);
            this.wsCallbacks.delete(data.callback_id);
        }

        // 广播消息给所有监听器
        window.dispatchEvent(new CustomEvent('websocket-message', { detail: data }));
    }

    /**
     * 通过WebSocket调用函数
     */
    callFunctionWS(functionName, params = {}) {
        return new Promise((resolve, reject) => {
            if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                reject(new Error('WebSocket未连接'));
                return;
            }

            const callbackId = ++this.wsCallbackId;
            
            this.wsCallbacks.set(callbackId, (data) => {
                if (data.error) {
                    reject(new Error(data.error));
                } else {
                    resolve(data.result);
                }
            });

            const message = {
                type: 'function_call',
                function: functionName,
                params: params,
                callback_id: callbackId
            };

            this.websocket.send(JSON.stringify(message));

            // 30秒超时
            setTimeout(() => {
                if (this.wsCallbacks.has(callbackId)) {
                    this.wsCallbacks.delete(callbackId);
                    reject(new Error('WebSocket调用超时'));
                }
            }, 30000);
        });
    }

    /**
     * 断开WebSocket连接
     */
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
}

// 创建全局API客户端实例
window.apiClient = new APIClient();

// 页面加载完成后连接WebSocket
document.addEventListener('DOMContentLoaded', () => {
    window.apiClient.connectWebSocket();
});

// 页面卸载时断开WebSocket连接
window.addEventListener('beforeunload', () => {
    window.apiClient.disconnectWebSocket();
});