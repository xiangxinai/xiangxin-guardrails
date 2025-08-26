package com.xiangxin.guardrails.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * 分页的检测结果
 */
public class ResultsPage {
    @JsonProperty("items")
    private List<DetectionResultSummary> items;
    
    @JsonProperty("total")
    private int total;
    
    @JsonProperty("page")
    private int page;
    
    @JsonProperty("per_page")
    private int perPage;
    
    @JsonProperty("pages")
    private int pages;

    // Getters and Setters
    public List<DetectionResultSummary> getItems() {
        return items;
    }

    public void setItems(List<DetectionResultSummary> items) {
        this.items = items;
    }

    public int getTotal() {
        return total;
    }

    public void setTotal(int total) {
        this.total = total;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }

    public int getPerPage() {
        return perPage;
    }

    public void setPerPage(int perPage) {
        this.perPage = perPage;
    }

    public int getPages() {
        return pages;
    }

    public void setPages(int pages) {
        this.pages = pages;
    }

    @Override
    public String toString() {
        return "ResultsPage{" +
                "items=" + items +
                ", total=" + total +
                ", page=" + page +
                ", perPage=" + perPage +
                ", pages=" + pages +
                '}';
    }
}
