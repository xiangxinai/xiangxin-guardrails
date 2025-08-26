package com.xiangxin.guardrails.models;

/**
 * 检测结果查询选项
 */
public class ResultsQueryOptions {
    private int page = 1;
    private int perPage = 20;
    private String riskLevel;
    private String category;
    private String startDate;
    private String endDate;
    private String contentSearch;
    private String requestIdSearch;

    public ResultsQueryOptions() {}

    public ResultsQueryOptions(int page, int perPage) {
        this.page = page;
        this.perPage = perPage;
    }

    // Getters and Setters
    public int getPage() {
        return page;
    }

    public ResultsQueryOptions setPage(int page) {
        this.page = page;
        return this;
    }

    public int getPerPage() {
        return perPage;
    }

    public ResultsQueryOptions setPerPage(int perPage) {
        this.perPage = perPage;
        return this;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public ResultsQueryOptions setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
        return this;
    }

    public String getCategory() {
        return category;
    }

    public ResultsQueryOptions setCategory(String category) {
        this.category = category;
        return this;
    }

    public String getStartDate() {
        return startDate;
    }

    public ResultsQueryOptions setStartDate(String startDate) {
        this.startDate = startDate;
        return this;
    }

    public String getEndDate() {
        return endDate;
    }

    public ResultsQueryOptions setEndDate(String endDate) {
        this.endDate = endDate;
        return this;
    }

    public String getContentSearch() {
        return contentSearch;
    }

    public ResultsQueryOptions setContentSearch(String contentSearch) {
        this.contentSearch = contentSearch;
        return this;
    }

    public String getRequestIdSearch() {
        return requestIdSearch;
    }

    public ResultsQueryOptions setRequestIdSearch(String requestIdSearch) {
        this.requestIdSearch = requestIdSearch;
        return this;
    }

    @Override
    public String toString() {
        return "ResultsQueryOptions{" +
                "page=" + page +
                ", perPage=" + perPage +
                ", riskLevel='" + riskLevel + '\'' +
                ", category='" + category + '\'' +
                ", startDate='" + startDate + '\'' +
                ", endDate='" + endDate + '\'' +
                ", contentSearch='" + contentSearch + '\'' +
                ", requestIdSearch='" + requestIdSearch + '\'' +
                '}';
    }
}
