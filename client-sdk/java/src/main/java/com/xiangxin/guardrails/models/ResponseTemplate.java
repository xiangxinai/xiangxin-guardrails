package com.xiangxin.guardrails.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

/**
 * 代答模板
 */
public class ResponseTemplate {
    @JsonProperty("id")
    private Integer id;
    
    @JsonProperty("category")
    private String category;
    
    @JsonProperty("risk_level")
    private String riskLevel;
    
    @JsonProperty("template_content")
    private String templateContent;
    
    @JsonProperty("is_default")
    private Boolean isDefault;
    
    @JsonProperty("is_active")
    private Boolean isActive;
    
    @JsonProperty("created_at")
    private LocalDateTime createdAt;
    
    @JsonProperty("updated_at")
    private LocalDateTime updatedAt;

    // Getters and Setters
    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getTemplateContent() {
        return templateContent;
    }

    public void setTemplateContent(String templateContent) {
        this.templateContent = templateContent;
    }

    public Boolean getIsDefault() {
        return isDefault;
    }

    public void setIsDefault(Boolean isDefault) {
        this.isDefault = isDefault;
    }

    public Boolean getIsActive() {
        return isActive;
    }

    public void setIsActive(Boolean isActive) {
        this.isActive = isActive;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    @Override
    public String toString() {
        return "ResponseTemplate{" +
                "id=" + id +
                ", category='" + category + '\'' +
                ", riskLevel='" + riskLevel + '\'' +
                ", templateContent='" + templateContent + '\'' +
                ", isDefault=" + isDefault +
                ", isActive=" + isActive +
                ", createdAt=" + createdAt +
                ", updatedAt=" + updatedAt +
                '}';
    }
}
