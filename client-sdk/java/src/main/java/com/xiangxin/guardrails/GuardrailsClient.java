package com.xiangxin.guardrails;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.xiangxin.guardrails.models.*;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * 象信AI安全护栏 Java 客户端SDK (v2.0)
 * 
 * 支持双服务架构：
 * - 检测服务：高并发内容检测 (通常端口5000)
 * - 管理服务：配置管理和结果查询 (通常端口5001)
 * 
 * 认证方式：
 * - API Key 认证（推荐）
 * - JWT 认证（向后兼容）
 * 
 * 使用示例:
 * <pre>
 * // 方式一：使用API Key（推荐）
 * GuardrailsClient client = new GuardrailsClient.Builder()
 *     .detectionUrl("http://your-guardrails-detection:5000")
 *     .adminUrl("http://your-guardrails-admin:5001") 
 *     .apiKey("your-api-key")
 *     .build();
 * 
 * // 方式二：使用JWT密钥（向后兼容）
 * GuardrailsClient client = new GuardrailsClient.Builder()
 *     .detectionUrl("http://your-guardrails-detection:5000")
 *     .adminUrl("http://your-guardrails-admin:5001")
 *     .jwtSecret("your-jwt-secret-key")
 *     .build();
 * 
 * // 检测内容
 * List&lt;Message&gt; messages = Arrays.asList(
 *     new Message("user", "要检测的内容")
 * );
 * DetectionResult result = client.checkContent(messages);
 * </pre>
 * 
 * @author XiangxinAI
 * @version 2.0.0
 */
public class GuardrailsClient {
    private static final Logger logger = LoggerFactory.getLogger(GuardrailsClient.class);
    private static final String USER_AGENT = "GuardrailsClient-Java/2.0.0";
    
    private final String detectionUrl;
    private final String adminUrl;
    private final String apiKey;
    private final String jwtSecret;
    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final int maxRetries;

    private GuardrailsClient(Builder builder) {
        this.detectionUrl = builder.detectionUrl.replaceAll("/+$", "");
        this.adminUrl = builder.adminUrl.replaceAll("/+$", "");
        this.apiKey = builder.apiKey;
        this.jwtSecret = builder.jwtSecret;
        this.maxRetries = builder.maxRetries;
        
        if (this.apiKey == null && this.jwtSecret == null) {
            throw new IllegalArgumentException("必须提供 apiKey 或 jwtSecret 其中之一");
        }
        
        this.httpClient = new OkHttpClient.Builder()
            .connectTimeout(builder.connectTimeout, TimeUnit.SECONDS)
            .readTimeout(builder.readTimeout, TimeUnit.SECONDS)
            .writeTimeout(builder.writeTimeout, TimeUnit.SECONDS)
            .addInterceptor(new UserAgentInterceptor())
            .build();
            
        this.objectMapper = new ObjectMapper()
            .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE)
            .setSerializationInclusion(JsonInclude.Include.NON_NULL);
    }

    /**
     * 检测内容安全性
     * 
     * @param messages 消息列表，每个消息包含role和content字段
     * @return 检测结果
     * @throws GuardrailsException 检测失败时抛出异常
     */
    public DetectionResult checkContent(List<Message> messages) throws GuardrailsException {
        return checkContent(messages, null, null);
    }

    /**
     * 检测内容安全性（JWT模式）
     * 
     * @param messages 消息列表
     * @param userId 用户ID (JWT方式需要)
     * @param userEmail 用户邮箱 (JWT方式需要)
     * @return 检测结果
     * @throws GuardrailsException 检测失败时抛出异常
     */
    public DetectionResult checkContent(List<Message> messages, String userId, String userEmail) 
            throws GuardrailsException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", "Xiangxin-Guardrails-Text");
        requestBody.put("messages", messages);
        
        String response = makeRequest("POST", "/v1/guardrails", ServiceType.DETECTION, 
                                    userId, userEmail, requestBody);
        
        try {
            return objectMapper.readValue(response, DetectionResult.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析检测结果失败: " + e.getMessage(), e);
        }
    }

    /**
     * 服务健康检查
     * 
     * @param serviceType 服务类型
     * @return 健康状态信息
     * @throws GuardrailsException 检查失败时抛出异常
     */
    public Map<String, Object> healthCheck(ServiceType serviceType) throws GuardrailsException {
        String url = (serviceType == ServiceType.DETECTION ? detectionUrl : adminUrl) + "/health";
        
        Request request = new Request.Builder()
            .url(url)
            .get()
            .build();
            
        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new GuardrailsException("健康检查失败: " + response.code());
            }
            
            String responseBody = response.body().string();
            return objectMapper.readValue(responseBody, new TypeReference<Map<String, Object>>() {});
        } catch (IOException e) {
            throw new GuardrailsException("健康检查请求失败: " + e.getMessage(), e);
        }
    }

    /**
     * 获取黑名单列表
     * 
     * @return 黑名单列表
     * @throws GuardrailsException 获取失败时抛出异常
     */
    public List<BlacklistItem> getBlacklists() throws GuardrailsException {
        return getBlacklists(null, null);
    }

    /**
     * 获取黑名单列表（JWT模式）
     * 
     * @param userId 用户ID (JWT方式需要)
     * @param userEmail 用户邮箱 (JWT方式需要)
     * @return 黑名单列表
     * @throws GuardrailsException 获取失败时抛出异常
     */
    public List<BlacklistItem> getBlacklists(String userId, String userEmail) throws GuardrailsException {
        String response = makeRequest("GET", "/api/v1/config/blacklist", ServiceType.ADMIN, 
                                    userId, userEmail, null);
        
        try {
            return objectMapper.readValue(response, new TypeReference<List<BlacklistItem>>() {});
        } catch (IOException e) {
            throw new GuardrailsException("解析黑名单列表失败: " + e.getMessage(), e);
        }
    }

    /**
     * 创建黑名单
     * 
     * @param name 黑名单名称
     * @param keywords 关键词列表
     * @param description 描述信息
     * @param isActive 是否启用
     * @return 创建结果
     * @throws GuardrailsException 创建失败时抛出异常
     */
    public BlacklistItem createBlacklist(String name, List<String> keywords, 
                                       String description, boolean isActive) throws GuardrailsException {
        return createBlacklist(name, keywords, description, isActive, null, null);
    }

    /**
     * 创建黑名单（JWT模式）
     * 
     * @param name 黑名单名称
     * @param keywords 关键词列表
     * @param description 描述信息
     * @param isActive 是否启用
     * @param userId 用户ID (JWT方式需要)
     * @param userEmail 用户邮箱 (JWT方式需要)
     * @return 创建结果
     * @throws GuardrailsException 创建失败时抛出异常
     */
    public BlacklistItem createBlacklist(String name, List<String> keywords, 
                                       String description, boolean isActive,
                                       String userId, String userEmail) throws GuardrailsException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("name", name);
        requestBody.put("keywords", keywords);
        requestBody.put("description", description);
        requestBody.put("is_active", isActive);
        
        String response = makeRequest("POST", "/api/v1/config/blacklist", ServiceType.ADMIN, 
                                    userId, userEmail, requestBody);
        
        try {
            return objectMapper.readValue(response, BlacklistItem.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析创建结果失败: " + e.getMessage(), e);
        }
    }

    /**
     * 更新黑名单
     * 
     * @param blacklistId 黑名单ID
     * @param name 黑名单名称
     * @param keywords 关键词列表
     * @param description 描述信息
     * @param isActive 是否启用
     * @return 更新结果
     * @throws GuardrailsException 更新失败时抛出异常
     */
    public BlacklistItem updateBlacklist(int blacklistId, String name, List<String> keywords, 
                                       String description, boolean isActive) throws GuardrailsException {
        return updateBlacklist(blacklistId, name, keywords, description, isActive, null, null);
    }

    /**
     * 更新黑名单（JWT模式）
     */
    public BlacklistItem updateBlacklist(int blacklistId, String name, List<String> keywords, 
                                       String description, boolean isActive,
                                       String userId, String userEmail) throws GuardrailsException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("name", name);
        requestBody.put("keywords", keywords);
        requestBody.put("description", description);
        requestBody.put("is_active", isActive);
        
        String response = makeRequest("PUT", "/api/v1/config/blacklist/" + blacklistId, 
                                    ServiceType.ADMIN, userId, userEmail, requestBody);
        
        try {
            return objectMapper.readValue(response, BlacklistItem.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析更新结果失败: " + e.getMessage(), e);
        }
    }

    /**
     * 删除黑名单
     * 
     * @param blacklistId 黑名单ID
     * @throws GuardrailsException 删除失败时抛出异常
     */
    public void deleteBlacklist(int blacklistId) throws GuardrailsException {
        deleteBlacklist(blacklistId, null, null);
    }

    /**
     * 删除黑名单（JWT模式）
     */
    public void deleteBlacklist(int blacklistId, String userId, String userEmail) throws GuardrailsException {
        makeRequest("DELETE", "/api/v1/config/blacklist/" + blacklistId, 
                  ServiceType.ADMIN, userId, userEmail, null);
    }

    /**
     * 获取白名单列表
     */
    public List<WhitelistItem> getWhitelists() throws GuardrailsException {
        return getWhitelists(null, null);
    }

    public List<WhitelistItem> getWhitelists(String userId, String userEmail) throws GuardrailsException {
        String response = makeRequest("GET", "/api/v1/config/whitelist", ServiceType.ADMIN, 
                                    userId, userEmail, null);
        
        try {
            return objectMapper.readValue(response, new TypeReference<List<WhitelistItem>>() {});
        } catch (IOException e) {
            throw new GuardrailsException("解析白名单列表失败: " + e.getMessage(), e);
        }
    }

    /**
     * 创建白名单
     */
    public WhitelistItem createWhitelist(String name, List<String> keywords, 
                                       String description, boolean isActive) throws GuardrailsException {
        return createWhitelist(name, keywords, description, isActive, null, null);
    }

    public WhitelistItem createWhitelist(String name, List<String> keywords, 
                                       String description, boolean isActive,
                                       String userId, String userEmail) throws GuardrailsException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("name", name);
        requestBody.put("keywords", keywords);
        requestBody.put("description", description);
        requestBody.put("is_active", isActive);
        
        String response = makeRequest("POST", "/api/v1/config/whitelist", ServiceType.ADMIN, 
                                    userId, userEmail, requestBody);
        
        try {
            return objectMapper.readValue(response, WhitelistItem.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析创建结果失败: " + e.getMessage(), e);
        }
    }

    /**
     * 获取代答模板列表
     */
    public List<ResponseTemplate> getResponseTemplates() throws GuardrailsException {
        return getResponseTemplates(null, null);
    }

    public List<ResponseTemplate> getResponseTemplates(String userId, String userEmail) throws GuardrailsException {
        String response = makeRequest("GET", "/api/v1/config/responses", ServiceType.ADMIN, 
                                    userId, userEmail, null);
        
        try {
            return objectMapper.readValue(response, new TypeReference<List<ResponseTemplate>>() {});
        } catch (IOException e) {
            throw new GuardrailsException("解析代答模板列表失败: " + e.getMessage(), e);
        }
    }

    /**
     * 创建代答模板
     * 
     * @param category 风险类别代码 (S1-S12或default)
     * @param riskLevel 风险等级 (无风险/低风险/中风险/高风险)
     * @param templateContent 模板内容
     * @param isDefault 是否为默认模板
     * @param isActive 是否启用
     * @return 创建结果
     * @throws GuardrailsException 创建失败时抛出异常
     */
    public ResponseTemplate createResponseTemplate(String category, String riskLevel, 
                                                 String templateContent, boolean isDefault, boolean isActive) 
                                                 throws GuardrailsException {
        return createResponseTemplate(category, riskLevel, templateContent, isDefault, isActive, null, null);
    }

    public ResponseTemplate createResponseTemplate(String category, String riskLevel, 
                                                 String templateContent, boolean isDefault, boolean isActive,
                                                 String userId, String userEmail) throws GuardrailsException {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("category", category);
        requestBody.put("risk_level", riskLevel);
        requestBody.put("template_content", templateContent);
        requestBody.put("is_default", isDefault);
        requestBody.put("is_active", isActive);
        
        String response = makeRequest("POST", "/api/v1/config/responses", ServiceType.ADMIN, 
                                    userId, userEmail, requestBody);
        
        try {
            return objectMapper.readValue(response, ResponseTemplate.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析创建结果失败: " + e.getMessage(), e);
        }
    }

    /**
     * 获取检测结果列表
     * 
     * @param options 查询选项
     * @return 分页的检测结果
     * @throws GuardrailsException 获取失败时抛出异常
     */
    public ResultsPage getResults(ResultsQueryOptions options) throws GuardrailsException {
        return getResults(options, null, null);
    }

    public ResultsPage getResults(ResultsQueryOptions options, String userId, String userEmail) 
            throws GuardrailsException {
        StringBuilder urlBuilder = new StringBuilder("/api/v1/results?");
        urlBuilder.append("page=").append(options.getPage());
        urlBuilder.append("&per_page=").append(options.getPerPage());
        
        if (options.getRiskLevel() != null) {
            urlBuilder.append("&risk_level=").append(options.getRiskLevel());
        }
        if (options.getCategory() != null) {
            urlBuilder.append("&category=").append(options.getCategory());
        }
        if (options.getStartDate() != null) {
            urlBuilder.append("&start_date=").append(options.getStartDate());
        }
        if (options.getEndDate() != null) {
            urlBuilder.append("&end_date=").append(options.getEndDate());
        }
        if (options.getContentSearch() != null) {
            urlBuilder.append("&content_search=").append(options.getContentSearch());
        }
        if (options.getRequestIdSearch() != null) {
            urlBuilder.append("&request_id_search=").append(options.getRequestIdSearch());
        }
        
        String response = makeRequest("GET", urlBuilder.toString(), ServiceType.ADMIN, 
                                    userId, userEmail, null);
        
        try {
            return objectMapper.readValue(response, ResultsPage.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析检测结果列表失败: " + e.getMessage(), e);
        }
    }

    /**
     * 获取单个检测结果详情
     * 
     * @param resultId 结果ID
     * @return 检测结果详情
     * @throws GuardrailsException 获取失败时抛出异常
     */
    public DetectionResultDetail getResult(int resultId) throws GuardrailsException {
        return getResult(resultId, null, null);
    }

    public DetectionResultDetail getResult(int resultId, String userId, String userEmail) 
            throws GuardrailsException {
        String response = makeRequest("GET", "/api/v1/results/" + resultId, ServiceType.ADMIN, 
                                    userId, userEmail, null);
        
        try {
            return objectMapper.readValue(response, DetectionResultDetail.class);
        } catch (IOException e) {
            throw new GuardrailsException("解析检测结果详情失败: " + e.getMessage(), e);
        }
    }

    /**
     * 批量检测内容
     * 
     * @param contentList 要检测的内容列表
     * @return 检测结果列表
     */
    public List<BatchResult> batchCheckContent(List<String> contentList) {
        return batchCheckContent(contentList, null, null);
    }

    public List<BatchResult> batchCheckContent(List<String> contentList, String userId, String userEmail) {
        List<BatchResult> results = new ArrayList<>();
        
        for (String content : contentList) {
            try {
                List<Message> messages = Arrays.asList(new Message("user", content));
                DetectionResult result = checkContent(messages, userId, userEmail);
                results.add(new BatchResult(true, content, result, null));
            } catch (Exception e) {
                results.add(new BatchResult(false, content, null, e.getMessage()));
            }
        }
        
        return results;
    }

    /**
     * 生成JWT token（仅在JWT模式下使用）
     * 
     * @param userId 用户ID
     * @param userEmail 用户邮箱
     * @param expireHours token过期时间（小时）
     * @return JWT token字符串
     */
    public String generateUserToken(String userId, String userEmail, int expireHours) {
        if (jwtSecret == null) {
            throw new IllegalStateException("JWT模式需要提供jwtSecret");
        }
        
        Algorithm algorithm = Algorithm.HMAC256(jwtSecret);
        return JWT.create()
            .withClaim("user_id", userId)
            .withSubject(userId)
            .withClaim("email", userEmail)
            .withClaim("role", "user")
            .withExpiresAt(Date.from(Instant.now().plus(expireHours, ChronoUnit.HOURS)))
            .sign(algorithm);
    }

    /**
     * 关闭客户端，释放资源
     */
    public void close() {
        if (httpClient != null) {
            httpClient.dispatcher().executorService().shutdown();
            httpClient.connectionPool().evictAll();
        }
    }

    // ========== 私有方法 ==========

    private String makeRequest(String method, String endpoint, ServiceType serviceType, 
                             String userId, String userEmail, Object requestBody) 
                             throws GuardrailsException {
        String baseUrl = serviceType == ServiceType.DETECTION ? detectionUrl : adminUrl;
        String url = baseUrl + endpoint;
        
        Request.Builder requestBuilder = new Request.Builder().url(url);
        
        // 设置认证头
        if (apiKey != null) {
            requestBuilder.addHeader("Authorization", "Bearer " + apiKey);
        } else {
            if (userId == null || userEmail == null) {
                throw new IllegalArgumentException("使用JWT认证时必须提供userId和userEmail");
            }
            String token = generateUserToken(userId, userEmail, 1);
            requestBuilder.addHeader("Authorization", "Bearer " + token);
        }
        
        // 设置请求体
        if ("GET".equals(method) || "DELETE".equals(method)) {
            requestBuilder.method(method, null);
        } else if (requestBody != null) {
            try {
                String jsonBody = objectMapper.writeValueAsString(requestBody);
                RequestBody body = RequestBody.create(jsonBody, MediaType.get("application/json"));
                requestBuilder.method(method, body);
            } catch (IOException e) {
                throw new GuardrailsException("序列化请求体失败: " + e.getMessage(), e);
            }
        }
        
        Request request = requestBuilder.build();
        
        // 重试机制
        Exception lastException = null;
        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                logger.debug("请求 {} {} (尝试 {})", method, url, attempt + 1);
                
                try (Response response = httpClient.newCall(request).execute()) {
                    if (response.isSuccessful()) {
                        return response.body().string();
                    } else {
                        handleHttpError(response);
                    }
                }
            } catch (IOException e) {
                lastException = e;
                if (attempt < maxRetries) {
                    logger.warn("请求异常，准备重试: {}", e.getMessage());
                    try {
                        Thread.sleep(1000 * attempt);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new GuardrailsException("请求被中断", ie);
                    }
                    continue;
                }
            }
        }
        
        throw new GuardrailsException("请求失败，已重试" + maxRetries + "次: " + 
                                    (lastException != null ? lastException.getMessage() : "未知错误"));
    }

    private void handleHttpError(Response response) throws GuardrailsException, IOException {
        int code = response.code();
        String message = response.body() != null ? response.body().string() : "Unknown error";
        
        switch (code) {
            case 401:
                throw new AuthenticationException("认证失败，请检查API密钥或JWT配置");
            case 403:
                throw new AuthenticationException("权限不足");
            case 404:
                throw new NotFoundException("请求的资源不存在");
            case 422:
                throw new ValidationException("数据验证失败: " + message);
            case 429:
                throw new RateLimitException("请求频率超限，请稍后重试");
            default:
                if (code >= 500) {
                    throw new GuardrailsException("服务器内部错误: " + code);
                } else {
                    throw new GuardrailsException("请求失败 " + code + ": " + message);
                }
        }
    }

    // ========== 内部类 ==========

    private static class UserAgentInterceptor implements Interceptor {
        @Override
        public Response intercept(Chain chain) throws IOException {
            Request originalRequest = chain.request();
            Request newRequest = originalRequest.newBuilder()
                .header("User-Agent", USER_AGENT)
                .build();
            return chain.proceed(newRequest);
        }
    }

    /**
     * 服务类型枚举
     */
    public enum ServiceType {
        DETECTION, ADMIN
    }

    /**
     * Builder 类用于构建 GuardrailsClient 实例
     */
    public static class Builder {
        private String detectionUrl;
        private String adminUrl;
        private String apiKey;
        private String jwtSecret;
        private int connectTimeout = 30;
        private int readTimeout = 30;
        private int writeTimeout = 30;
        private int maxRetries = 3;

        public Builder detectionUrl(String detectionUrl) {
            this.detectionUrl = detectionUrl;
            return this;
        }

        public Builder adminUrl(String adminUrl) {
            this.adminUrl = adminUrl;
            return this;
        }

        public Builder apiKey(String apiKey) {
            this.apiKey = apiKey;
            return this;
        }

        public Builder jwtSecret(String jwtSecret) {
            this.jwtSecret = jwtSecret;
            return this;
        }

        public Builder connectTimeout(int seconds) {
            this.connectTimeout = seconds;
            return this;
        }

        public Builder readTimeout(int seconds) {
            this.readTimeout = seconds;
            return this;
        }

        public Builder writeTimeout(int seconds) {
            this.writeTimeout = seconds;
            return this;
        }

        public Builder maxRetries(int maxRetries) {
            this.maxRetries = maxRetries;
            return this;
        }

        public GuardrailsClient build() {
            if (detectionUrl == null || adminUrl == null) {
                throw new IllegalArgumentException("detectionUrl 和 adminUrl 不能为空");
            }
            return new GuardrailsClient(this);
        }
    }
}
