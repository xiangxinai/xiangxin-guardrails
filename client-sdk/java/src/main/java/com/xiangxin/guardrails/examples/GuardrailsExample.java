package com.xiangxin.guardrails.examples;

import com.xiangxin.guardrails.*;
import com.xiangxin.guardrails.models.*;
import java.util.*;

/**
 * 象信AI安全护栏 Java SDK 使用示例
 */
public class GuardrailsExample {
    
    public static void main(String[] args) {
        System.out.println("============================================");
        System.out.println("示例1: 使用API Key（推荐方式）");
        System.out.println("============================================");
        
        // 方式一：使用API Key（推荐）
        GuardrailsClient client = new GuardrailsClient.Builder()
            .detectionUrl("http://localhost:5000")
            .adminUrl("http://localhost:5001")
            .apiKey("your-api-key")  // 替换为实际API密钥
            .build();
        
        try {
            // 检查服务健康状态
            Map<String, Object> detectionHealth = client.healthCheck(GuardrailsClient.ServiceType.DETECTION);
            System.out.println("检测服务状态: " + detectionHealth);
            
            Map<String, Object> adminHealth = client.healthCheck(GuardrailsClient.ServiceType.ADMIN);
            System.out.println("管理服务状态: " + adminHealth);
            
            // 检测内容（API Key方式）
            List<Message> messages = Arrays.asList(new Message("user", "这是一个测试内容"));
            DetectionResult detectionResult = client.checkContent(messages);
            System.out.println("检测结果: " + detectionResult);
            
            // 获取黑名单列表
            List<BlacklistItem> blacklists = client.getBlacklists();
            System.out.println("黑名单列表: " + blacklists);
            
            // 创建黑名单
            BlacklistItem blacklistResult = client.createBlacklist(
                "测试黑名单",
                Arrays.asList("敏感词1", "敏感词2"),
                "Java SDK v2.0测试用黑名单",
                true
            );
            System.out.println("创建黑名单: " + blacklistResult);
            
            // 获取检测结果
            ResultsQueryOptions options = new ResultsQueryOptions()
                .setPage(1)
                .setPerPage(10);
            ResultsPage results = client.getResults(options);
            System.out.println("检测结果列表: " + results);
            
            // 批量检测示例
            List<String> contentList = Arrays.asList("内容1", "内容2", "内容3");
            List<BatchResult> batchResults = client.batchCheckContent(contentList);
            System.out.println("批量检测结果: " + batchResults);
            
        } catch (GuardrailsException e) {
            System.err.println("护栏系统错误: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("其他错误: " + e.getMessage());
            e.printStackTrace();
        } finally {
            client.close();
        }
        
        System.out.println("\n============================================");
        System.out.println("示例2: 使用JWT密钥（向后兼容）");
        System.out.println("============================================");
        
        // 方式二：使用JWT密钥（向后兼容）
        GuardrailsClient jwtClient = new GuardrailsClient.Builder()
            .detectionUrl("http://localhost:5000")
            .adminUrl("http://localhost:5001")
            .jwtSecret("your-jwt-secret-key")  // 替换为实际JWT密钥
            .build();
        
        String userId = "550e8400-e29b-41d4-a716-446655440001";
        String userEmail = "user@example.com";
        
        try {
            // 检测内容（JWT方式）
            List<Message> messages = Arrays.asList(new Message("user", "这是JWT方式的测试内容"));
            DetectionResult detectionResult = jwtClient.checkContent(messages, userId, userEmail);
            System.out.println("JWT检测结果: " + detectionResult);
            
            // 创建代答模板
            List<Map<String, Object>> templates = createDefaultResponseTemplates();
            for (int i = 0; i < Math.min(3, templates.size()); i++) { // 只创建前3个作为示例
                Map<String, Object> template = templates.get(i);
                ResponseTemplate result = jwtClient.createResponseTemplate(
                    (String) template.get("category"),
                    (String) template.get("risk_level"),
                    (String) template.get("template_content"),
                    (Boolean) template.get("is_default"),
                    (Boolean) template.get("is_active"),
                    userId,
                    userEmail
                );
                System.out.println("创建模板: " + result);
            }
            
        } catch (GuardrailsException e) {
            System.err.println("护栏系统错误: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("其他错误: " + e.getMessage());
            e.printStackTrace();
        } finally {
            jwtClient.close();
        }
    }
    
    /**
     * 创建默认代答模板列表
     */
    private static List<Map<String, Object>> createDefaultResponseTemplates() {
        List<Map<String, Object>> templates = new ArrayList<>();
        
        Map<String, Map<String, String>> riskCategories = new HashMap<>();
        riskCategories.put("S1", createCategory("一般政治话题", "中风险"));
        riskCategories.put("S2", createCategory("敏感政治话题", "高风险"));
        riskCategories.put("S3", createCategory("损害国家形象", "高风险"));
        riskCategories.put("S4", createCategory("伤害未成年人", "中风险"));
        riskCategories.put("S5", createCategory("暴力犯罪", "高风险"));
        riskCategories.put("S6", createCategory("违法犯罪", "中风险"));
        riskCategories.put("S7", createCategory("色情", "中风险"));
        riskCategories.put("S8", createCategory("歧视内容", "低风险"));
        riskCategories.put("S9", createCategory("提示词攻击", "高风险"));
        riskCategories.put("S10", createCategory("辱骂", "低风险"));
        riskCategories.put("S11", createCategory("侵犯个人隐私", "低风险"));
        riskCategories.put("S12", createCategory("商业违法违规", "低风险"));
        riskCategories.put("default", createCategory("默认模板", "通用"));
        
        for (Map.Entry<String, Map<String, String>> entry : riskCategories.entrySet()) {
            String code = entry.getKey();
            Map<String, String> info = entry.getValue();
            
            String templateContent;
            if ("default".equals(code)) {
                templateContent = "很抱歉，我不能回答这个问题。如有疑问请联系客服。";
            } else if ("高风险".equals(info.get("level"))) {
                templateContent = "很抱歉，我不能提供涉及" + info.get("name") + "的内容。";
            } else if ("中风险".equals(info.get("level"))) {
                templateContent = "抱歉，我不能回答涉及" + info.get("name") + "的问题。";
            } else { // 低风险
                templateContent = "我理解您的问题，但不能提供涉及" + info.get("name") + "的具体回答。";
            }
            
            Map<String, Object> template = new HashMap<>();
            template.put("category", code);
            template.put("risk_level", info.get("level"));
            template.put("template_content", templateContent);
            template.put("is_default", true);
            template.put("is_active", true);
            
            templates.add(template);
        }
        
        return templates;
    }
    
    private static Map<String, String> createCategory(String name, String level) {
        Map<String, String> category = new HashMap<>();
        category.put("name", name);
        category.put("level", level);
        return category;
    }
}
