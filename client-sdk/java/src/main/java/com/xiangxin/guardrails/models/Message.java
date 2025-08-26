package com.xiangxin.guardrails.models;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 消息对象
 */
public class Message {
    @JsonProperty("role")
    private String role;
    
    @JsonProperty("content")
    private String content;

    public Message() {}

    public Message(String role, String content) {
        this.role = role;
        this.content = content;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    @Override
    public String toString() {
        return "Message{" +
                "role='" + role + '\'' +
                ", content='" + content + '\'' +
                '}';
    }
}
