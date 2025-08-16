/**
 * 象信AI安全护栏 - Node.js客户端SDK
 * 
 * 使用示例:
 * const GuardrailsClient = require('./guardrails-client');
 * 
 * const client = new GuardrailsClient(
 *   'http://your-guardrails-api.com',
 *   'your-jwt-secret-key'
 * );
 * 
 * // 检测内容
 * const result = await client.checkContent(
 *   'user-uuid',
 *   'user@example.com',
 *   [{ role: 'user', content: '要检测的内容' }]
 * );
 */

const jwt = require('jsonwebtoken');
const axios = require('axios');

/**
 * 护栏系统基础错误类
 */
class GuardrailsError extends Error {
    constructor(message, code = null) {
        super(message);
        this.name = 'GuardrailsError';
        this.code = code;
    }
}

/**
 * 认证错误类
 */
class AuthenticationError extends GuardrailsError {
    constructor(message) {
        super(message);
        this.name = 'AuthenticationError';
    }
}

/**
 * 数据验证错误类
 */
class ValidationError extends GuardrailsError {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

/**
 * 资源不存在错误类
 */
class NotFoundError extends GuardrailsError {
    constructor(message) {
        super(message);
        this.name = 'NotFoundError';
    }
}

/**
 * 请求频率限制错误类
 */
class RateLimitError extends GuardrailsError {
    constructor(message) {
        super(message);
        this.name = 'RateLimitError';
    }
}

/**
 * 象信AI安全护栏客户端
 */
class GuardrailsClient {
    /**
     * 初始化客户端
     * 
     * @param {string} apiBaseUrl - API基础URL
     * @param {string} jwtSecret - JWT密钥（与护栏系统相同）
     * @param {object} options - 配置选项
     * @param {number} options.timeout - 请求超时时间（毫秒）
     * @param {number} options.maxRetries - 最大重试次数
     */
    constructor(apiBaseUrl, jwtSecret, options = {}) {
        this.apiBaseUrl = apiBaseUrl.replace(/\/+$/, '');
        this.jwtSecret = jwtSecret;
        this.timeout = options.timeout || 30000;
        this.maxRetries = options.maxRetries || 3;
        
        // 创建axios实例
        this.httpClient = axios.create({
            timeout: this.timeout,
            headers: {
                'User-Agent': 'GuardrailsClient-NodeJS/1.0.0'
            }
        });
        
        // 设置响应拦截器
        this.httpClient.interceptors.response.use(
            response => response,
            error => this._handleHttpError(error)
        );
    }

    /**
     * 为指定用户生成JWT token
     * 
     * @param {string} userId - 用户UUID字符串
     * @param {string} userEmail - 用户邮箱
     * @param {number} expireHours - token过期时间（小时）
     * @returns {string} JWT token字符串
     */
    generateUserToken(userId, userEmail, expireHours = 1) {
        const payload = {
            user_id: userId,
            sub: userId,
            email: userEmail,
            role: 'user',
            exp: Math.floor(Date.now() / 1000) + (expireHours * 60 * 60)
        };
        return jwt.sign(payload, this.jwtSecret, { algorithm: 'HS256' });
    }

    /**
     * 处理HTTP错误
     * 
     * @private
     * @param {object} error - axios错误对象
     * @throws {GuardrailsError} 相应的错误类型
     */
    _handleHttpError(error) {
        if (error.response) {
            const { status, data } = error.response;
            const message = data?.detail || data?.message || error.message;
            
            switch (status) {
                case 401:
                    throw new AuthenticationError('认证失败，请检查JWT密钥和用户信息');
                case 403:
                    throw new AuthenticationError('权限不足');
                case 404:
                    throw new NotFoundError('请求的资源不存在');
                case 422:
                    throw new ValidationError(`数据验证失败: ${JSON.stringify(data)}`);
                case 429:
                    throw new RateLimitError('请求频率超限，请稍后重试');
                default:
                    if (status >= 500) {
                        throw new GuardrailsError(`服务器内部错误: ${status}`, status);
                    } else {
                        throw new GuardrailsError(`请求失败 ${status}: ${message}`, status);
                    }
            }
        } else if (error.request) {
            throw new GuardrailsError(`网络请求失败: ${error.message}`);
        } else {
            throw new GuardrailsError(`请求配置错误: ${error.message}`);
        }
    }

    /**
     * 发起API请求
     * 
     * @private
     * @param {string} method - HTTP方法
     * @param {string} endpoint - API端点
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {object} config - axios配置
     * @returns {Promise<any>} 响应数据
     */
    async _makeRequest(method, endpoint, userId, userEmail, config = {}) {
        const token = this.generateUserToken(userId, userEmail);
        
        const requestConfig = {
            method,
            url: `${this.apiBaseUrl}${endpoint}`,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...config.headers
            },
            ...config
        };

        // 重试机制
        let lastError;
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                console.debug(`请求 ${method} ${requestConfig.url} (尝试 ${attempt + 1})`);
                const response = await this.httpClient.request(requestConfig);
                return response.data;
            } catch (error) {
                lastError = error;
                if (attempt < this.maxRetries && error.code >= 500) {
                    console.warn(`服务器错误 ${error.code}，准备重试...`);
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                    continue;
                }
                break;
            }
        }
        
        throw lastError;
    }

    // ========== 内容检测接口 ==========

    /**
     * 检测内容安全性
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {Array<object>} messages - 消息列表，每个消息包含role和content字段
     * @returns {Promise<object>} 检测结果对象
     * 
     * @example
     * const result = await client.checkContent(
     *   'user-uuid',
     *   'user@example.com',
     *   [{ role: 'user', content: '要检测的内容' }]
     * );
     */
    async checkContent(userId, userEmail, messages) {
        return await this._makeRequest('POST', '/v1/guardrails', userId, userEmail, {
            data: { messages }
        });
    }

    /**
     * 获取可用模型列表
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @returns {Promise<object>} 模型列表
     */
    async getAvailableModels(userId, userEmail) {
        return await this._makeRequest('GET', '/v1/guardrails/models', userId, userEmail);
    }

    /**
     * 检测服务健康检查（不需要认证）
     * 
     * @returns {Promise<object>} 健康状态信息
     */
    async healthCheck() {
        const response = await this.httpClient.get(`${this.apiBaseUrl}/health`);
        return response.data;
    }

    // ========== 黑名单管理接口 ==========

    /**
     * 获取用户黑名单列表
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @returns {Promise<Array>} 黑名单列表
     */
    async getBlacklists(userId, userEmail) {
        return await this._makeRequest('GET', '/config/blacklist', userId, userEmail);
    }

    /**
     * 创建黑名单
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {string} name - 黑名单名称
     * @param {Array<string>} keywords - 关键词列表
     * @param {string} description - 描述信息
     * @param {boolean} isActive - 是否启用
     * @returns {Promise<object>} 创建结果
     */
    async createBlacklist(userId, userEmail, name, keywords, description = '', isActive = true) {
        return await this._makeRequest('POST', '/config/blacklist', userId, userEmail, {
            data: {
                name,
                keywords,
                description,
                is_active: isActive
            }
        });
    }

    /**
     * 更新黑名单
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {number} blacklistId - 黑名单ID
     * @param {string} name - 黑名单名称
     * @param {Array<string>} keywords - 关键词列表
     * @param {string} description - 描述信息
     * @param {boolean} isActive - 是否启用
     * @returns {Promise<object>} 更新结果
     */
    async updateBlacklist(userId, userEmail, blacklistId, name, keywords, description = '', isActive = true) {
        return await this._makeRequest('PUT', `/config/blacklist/${blacklistId}`, userId, userEmail, {
            data: {
                name,
                keywords,
                description,
                is_active: isActive
            }
        });
    }

    /**
     * 删除黑名单
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {number} blacklistId - 黑名单ID
     * @returns {Promise<object>} 删除结果
     */
    async deleteBlacklist(userId, userEmail, blacklistId) {
        return await this._makeRequest('DELETE', `/config/blacklist/${blacklistId}`, userId, userEmail);
    }

    // ========== 白名单管理接口 ==========

    /**
     * 获取用户白名单列表
     */
    async getWhitelists(userId, userEmail) {
        return await this._makeRequest('GET', '/config/whitelist', userId, userEmail);
    }

    /**
     * 创建白名单
     */
    async createWhitelist(userId, userEmail, name, keywords, description = '', isActive = true) {
        return await this._makeRequest('POST', '/config/whitelist', userId, userEmail, {
            data: {
                name,
                keywords,
                description,
                is_active: isActive
            }
        });
    }

    /**
     * 更新白名单
     */
    async updateWhitelist(userId, userEmail, whitelistId, name, keywords, description = '', isActive = true) {
        return await this._makeRequest('PUT', `/config/whitelist/${whitelistId}`, userId, userEmail, {
            data: {
                name,
                keywords,
                description,
                is_active: isActive
            }
        });
    }

    /**
     * 删除白名单
     */
    async deleteWhitelist(userId, userEmail, whitelistId) {
        return await this._makeRequest('DELETE', `/config/whitelist/${whitelistId}`, userId, userEmail);
    }

    // ========== 代答模板管理接口 ==========

    /**
     * 获取用户代答模板列表
     */
    async getResponseTemplates(userId, userEmail) {
        return await this._makeRequest('GET', '/config/responses', userId, userEmail);
    }

    /**
     * 创建代答模板
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {string} category - 风险类别代码 (S1-S12或default)
     * @param {string} riskLevel - 风险等级 (无风险/低风险/中风险/高风险)
     * @param {string} templateContent - 模板内容
     * @param {boolean} isDefault - 是否为默认模板
     * @param {boolean} isActive - 是否启用
     * @returns {Promise<object>} 创建结果
     */
    async createResponseTemplate(userId, userEmail, category, riskLevel, templateContent, isDefault = true, isActive = true) {
        return await this._makeRequest('POST', '/config/responses', userId, userEmail, {
            data: {
                category,
                risk_level: riskLevel,
                template_content: templateContent,
                is_default: isDefault,
                is_active: isActive
            }
        });
    }

    /**
     * 更新代答模板
     */
    async updateResponseTemplate(userId, userEmail, templateId, category, riskLevel, templateContent, isDefault = true, isActive = true) {
        return await this._makeRequest('PUT', `/config/responses/${templateId}`, userId, userEmail, {
            data: {
                category,
                risk_level: riskLevel,
                template_content: templateContent,
                is_default: isDefault,
                is_active: isActive
            }
        });
    }

    /**
     * 删除代答模板
     */
    async deleteResponseTemplate(userId, userEmail, templateId) {
        return await this._makeRequest('DELETE', `/config/responses/${templateId}`, userId, userEmail);
    }

    // ========== 系统信息接口 ==========

    /**
     * 获取系统信息
     */
    async getSystemInfo(userId, userEmail) {
        return await this._makeRequest('GET', '/config/system-info', userId, userEmail);
    }

    /**
     * 获取缓存状态信息
     */
    async getCacheInfo(userId, userEmail) {
        return await this._makeRequest('GET', '/config/cache-info', userId, userEmail);
    }

    /**
     * 手动刷新缓存
     */
    async refreshCache(userId, userEmail) {
        return await this._makeRequest('POST', '/config/cache/refresh', userId, userEmail);
    }

    // ========== 批量操作辅助方法 ==========

    /**
     * 批量创建黑名单
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {Array<object>} blacklists - 黑名单定义列表
     * @returns {Promise<Array>} 创建结果列表
     * 
     * @example
     * const results = await client.batchCreateBlacklists(
     *   'user-uuid',
     *   'user@example.com',
     *   [
     *     { name: '敏感词1', keywords: ['词1', '词2'], description: '描述1' },
     *     { name: '敏感词2', keywords: ['词3', '词4'], description: '描述2' }
     *   ]
     * );
     */
    async batchCreateBlacklists(userId, userEmail, blacklists) {
        const results = [];
        
        for (const blacklistData of blacklists) {
            try {
                const result = await this.createBlacklist(
                    userId,
                    userEmail,
                    blacklistData.name,
                    blacklistData.keywords,
                    blacklistData.description || '',
                    blacklistData.is_active !== undefined ? blacklistData.is_active : true
                );
                results.push({ success: true, data: result });
            } catch (error) {
                results.push({ success: false, error: error.message, data: blacklistData });
            }
        }
        
        return results;
    }

    /**
     * 批量检测内容
     * 
     * @param {string} userId - 用户ID
     * @param {string} userEmail - 用户邮箱
     * @param {Array<string>} contentList - 要检测的内容列表
     * @returns {Promise<Array>} 检测结果列表
     */
    async batchCheckContent(userId, userEmail, contentList) {
        const results = [];
        
        for (const content of contentList) {
            try {
                const result = await this.checkContent(
                    userId,
                    userEmail,
                    [{ role: 'user', content }]
                );
                results.push({ success: true, content, result });
            } catch (error) {
                results.push({ success: false, content, error: error.message });
            }
        }
        
        return results;
    }
}

// ========== 辅助类和函数 ==========

/**
 * 护栏配置辅助类
 */
class GuardrailsConfig {
    static RISK_CATEGORIES = {
        'S1': { name: '一般政治话题', level: '中风险' },
        'S2': { name: '敏感政治话题', level: '高风险' },
        'S3': { name: '损害国家形象', level: '高风险' },
        'S4': { name: '伤害未成年人', level: '中风险' },
        'S5': { name: '暴力犯罪', level: '高风险' },
        'S6': { name: '违法犯罪', level: '中风险' },
        'S7': { name: '色情', level: '中风险' },
        'S8': { name: '歧视内容', level: '低风险' },
        'S9': { name: '提示词攻击', level: '高风险' },
        'S10': { name: '辱骂', level: '低风险' },
        'S11': { name: '侵犯个人隐私', level: '低风险' },
        'S12': { name: '商业违法违规', level: '低风险' },
        'default': { name: '默认模板', level: '通用' }
    };

    /**
     * 根据类别代码获取类别名称
     */
    static getCategoryName(categoryCode) {
        return this.RISK_CATEGORIES[categoryCode]?.name || '未知类别';
    }

    /**
     * 根据类别代码获取风险等级
     */
    static getRiskLevel(categoryCode) {
        return this.RISK_CATEGORIES[categoryCode]?.level || '未知';
    }

    /**
     * 获取所有风险类别
     */
    static getAllCategories() {
        return { ...this.RISK_CATEGORIES };
    }
}

/**
 * 创建默认代答模板列表
 * 
 * @returns {Array<object>} 默认模板配置列表
 */
function createDefaultResponseTemplates() {
    const templates = [];
    
    for (const [code, info] of Object.entries(GuardrailsConfig.RISK_CATEGORIES)) {
        let templateContent;
        
        if (code === 'default') {
            templateContent = '很抱歉，我不能回答这个问题。如有疑问请联系客服。';
        } else if (info.level === '高风险') {
            templateContent = `很抱歉，我不能提供涉及${info.name}的内容。`;
        } else if (info.level === '中风险') {
            templateContent = `抱歉，我不能回答涉及${info.name}的问题。`;
        } else { // 低风险
            templateContent = `我理解您的问题，但不能提供涉及${info.name}的具体回答。`;
        }
        
        templates.push({
            category: code,
            risk_level: info.level,
            template_content: templateContent,
            is_default: true,
            is_active: true
        });
    }
    
    return templates;
}

// ========== 导出 ==========

module.exports = {
    GuardrailsClient,
    GuardrailsConfig,
    createDefaultResponseTemplates,
    // 错误类
    GuardrailsError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError
};

// ========== 使用示例 ==========

if (require.main === module) {
    // 示例代码，仅在直接运行此文件时执行
    (async () => {
        const client = new GuardrailsClient(
            'http://localhost:5000',    // 替换为实际API地址
            'your-jwt-secret-key'       // 替换为实际JWT密钥
        );
        
        const userId = '550e8400-e29b-41d4-a716-446655440001';
        const userEmail = 'user@example.com';
        
        try {
            // 检查服务健康状态
            const health = await client.healthCheck();
            console.log('服务状态:', health);
            
            // 创建黑名单
            const blacklistResult = await client.createBlacklist(
                userId,
                userEmail,
                '测试黑名单',
                ['敏感词1', '敏感词2'],
                'Node.js SDK测试用黑名单'
            );
            console.log('创建黑名单:', blacklistResult);
            
            // 获取黑名单列表
            const blacklists = await client.getBlacklists(userId, userEmail);
            console.log('黑名单列表:', blacklists);
            
            // 创建默认代答模板
            const templates = createDefaultResponseTemplates();
            for (const template of templates.slice(0, 3)) { // 只创建前3个作为示例
                const result = await client.createResponseTemplate(
                    userId,
                    userEmail,
                    template.category,
                    template.risk_level,
                    template.template_content,
                    template.is_default,
                    template.is_active
                );
                console.log('创建模板:', result);
            }
            
            // 检测内容
            const detectionResult = await client.checkContent(
                userId,
                userEmail,
                [{ role: 'user', content: '这是一个测试内容' }]
            );
            console.log('检测结果:', detectionResult);
            
            // 批量检测示例
            const batchResults = await client.batchCheckContent(
                userId,
                userEmail,
                ['内容1', '内容2', '内容3']
            );
            console.log('批量检测结果:', batchResults);
            
        } catch (error) {
            if (error instanceof GuardrailsError) {
                console.error('护栏系统错误:', error.message);
            } else {
                console.error('其他错误:', error.message);
            }
        }
    })();
}