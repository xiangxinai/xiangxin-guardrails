package com.xiangxin.guardrails.models;

/**
 * 批量操作结果
 */
public class BatchResult {
    private boolean success;
    private String content;
    private DetectionResult result;
    private String error;

    public BatchResult() {}

    public BatchResult(boolean success, String content, DetectionResult result, String error) {
        this.success = success;
        this.content = content;
        this.result = result;
        this.error = error;
    }

    // Getters and Setters
    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public DetectionResult getResult() {
        return result;
    }

    public void setResult(DetectionResult result) {
        this.result = result;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    @Override
    public String toString() {
        return "BatchResult{" +
                "success=" + success +
                ", content='" + content + '\'' +
                ", result=" + result +
                ", error='" + error + '\'' +
                '}';
    }
}
