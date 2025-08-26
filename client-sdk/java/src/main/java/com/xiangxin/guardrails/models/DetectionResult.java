package com.xiangxin.guardrails.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * 检测结果
 */
public class DetectionResult {
    @JsonProperty("id")
    private String id;
    
    @JsonProperty("overall_risk_level")
    private String overallRiskLevel;
    
    @JsonProperty("suggest_action")
    private String suggestAction;
    
    @JsonProperty("suggest_answer")
    private String suggestAnswer;
    
    @JsonProperty("result")
    private Result result;

    public static class Result {
        @JsonProperty("compliance")
        private RiskInfo compliance;
        
        @JsonProperty("security")
        private RiskInfo security;

        public RiskInfo getCompliance() {
            return compliance;
        }

        public void setCompliance(RiskInfo compliance) {
            this.compliance = compliance;
        }

        public RiskInfo getSecurity() {
            return security;
        }

        public void setSecurity(RiskInfo security) {
            this.security = security;
        }
    }

    public static class RiskInfo {
        @JsonProperty("risk_level")
        private String riskLevel;
        
        @JsonProperty("categories")
        private List<String> categories;

        public String getRiskLevel() {
            return riskLevel;
        }

        public void setRiskLevel(String riskLevel) {
            this.riskLevel = riskLevel;
        }

        public List<String> getCategories() {
            return categories;
        }

        public void setCategories(List<String> categories) {
            this.categories = categories;
        }
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getOverallRiskLevel() {
        return overallRiskLevel;
    }

    public void setOverallRiskLevel(String overallRiskLevel) {
        this.overallRiskLevel = overallRiskLevel;
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

    public Result getResult() {
        return result;
    }

    public void setResult(Result result) {
        this.result = result;
    }

    @Override
    public String toString() {
        return "DetectionResult{" +
                "id='" + id + '\'' +
                ", overallRiskLevel='" + overallRiskLevel + '\'' +
                ", suggestAction='" + suggestAction + '\'' +
                ", suggestAnswer='" + suggestAnswer + '\'' +
                ", result=" + result +
                '}';
    }
}
