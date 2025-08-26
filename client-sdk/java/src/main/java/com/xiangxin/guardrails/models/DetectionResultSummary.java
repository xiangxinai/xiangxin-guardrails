package com.xiangxin.guardrails.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 检测结果摘要（用于列表显示）
 */
public class DetectionResultSummary {
    @JsonProperty("id")
    private Integer id;
    
    @JsonProperty("request_id")
    private String requestId;
    
    @JsonProperty("content")
    private String content;
    
    @JsonProperty("suggest_action")
    private String suggestAction;
    
    @JsonProperty("suggest_answer")
    private String suggestAnswer;
    
    @JsonProperty("created_at")
    private LocalDateTime createdAt;
    
    @JsonProperty("ip_address")
    private String ipAddress;
    
    @JsonProperty("security_risk_level")
    private String securityRiskLevel;
    
    @JsonProperty("security_categories")
    private List<String> securityCategories;
    
    @JsonProperty("compliance_risk_level")
    private String complianceRiskLevel;
    
    @JsonProperty("compliance_categories")
    private List<String> complianceCategories;

    // Getters and Setters
    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getRequestId() {
        return requestId;
    }

    public void setRequestId(String requestId) {
        this.requestId = requestId;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getSuggestAction() {
        return suggestAction;
    }

    public void setSuggestAction(String suggestAction) {
        this.suggestAction = suggestAction;
    }

    public String getSuggestAnswer() {
        return suggestAnswer;
    }

    public void setSuggestAnswer(String suggestAnswer) {
        this.suggestAnswer = suggestAnswer;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public String getIpAddress() {
        return ipAddress;
    }

    public void setIpAddress(String ipAddress) {
        this.ipAddress = ipAddress;
    }

    public String getSecurityRiskLevel() {
        return securityRiskLevel;
    }

    public void setSecurityRiskLevel(String securityRiskLevel) {
        this.securityRiskLevel = securityRiskLevel;
    }

    public List<String> getSecurityCategories() {
        return securityCategories;
    }

    public void setSecurityCategories(List<String> securityCategories) {
        this.securityCategories = securityCategories;
    }

    public String getComplianceRiskLevel() {
        return complianceRiskLevel;
    }

    public void setComplianceRiskLevel(String complianceRiskLevel) {
        this.complianceRiskLevel = complianceRiskLevel;
    }

    public List<String> getComplianceCategories() {
        return complianceCategories;
    }

    public void setComplianceCategories(List<String> complianceCategories) {
        this.complianceCategories = complianceCategories;
    }

    @Override
    public String toString() {
        return "DetectionResultSummary{" +
                "id=" + id +
                ", requestId='" + requestId + '\'' +
                ", content='" + content + '\'' +
                ", suggestAction='" + suggestAction + '\'' +
                ", createdAt=" + createdAt +
                ", securityRiskLevel='" + securityRiskLevel + '\'' +
                ", complianceRiskLevel='" + complianceRiskLevel + '\'' +
                '}';
    }
}
