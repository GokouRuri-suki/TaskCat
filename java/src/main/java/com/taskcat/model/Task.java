package com.taskcat.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;

/**
 * 任务实体，镜像后端 {@code TaskItemModel}（fastapi/src/schemas.py）。
 *
 * <p>字段与后端 JSON 一一对应，由 Jackson 序列化/反序列化。
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class Task {

    public static final String STATUS_TODO = "todo";
    public static final String STATUS_DOING = "doing";
    public static final String STATUS_DONE = "done";
    public static final String STATUS_DELETED = "deleted";

    public static final int PRIORITY_MIN = 1;
    public static final int PRIORITY_MAX = 10;
    public static final int PRIORITY_DEFAULT = 5;

    private String id;
    private String title;
    private String content = "";
    private String status = STATUS_TODO;
    private int priority = PRIORITY_DEFAULT;
    private int modifyInt = 0;
    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    public Task() {
    }

    @JsonProperty("id")
    public String getId() {
        return id;
    }

    @JsonProperty("id")
    public void setId(String id) {
        this.id = id;
    }

    @JsonProperty("title")
    public String getTitle() {
        return title;
    }

    @JsonProperty("title")
    public void setTitle(String title) {
        this.title = title;
    }

    @JsonProperty("content")
    public String getContent() {
        return content;
    }

    @JsonProperty("content")
    public void setContent(String content) {
        this.content = content;
    }

    @JsonProperty("status")
    public String getStatus() {
        return status;
    }

    @JsonProperty("status")
    public void setStatus(String status) {
        this.status = status;
    }

    @JsonProperty("priority")
    public int getPriority() {
        return priority;
    }

    @JsonProperty("priority")
    public void setPriority(int priority) {
        this.priority = priority;
    }

    @JsonProperty("modify_int")
    public int getModifyInt() {
        return modifyInt;
    }

    @JsonProperty("modify_int")
    public void setModifyInt(int modifyInt) {
        this.modifyInt = modifyInt;
    }

    @JsonProperty("created_at")
    public Instant getCreatedAt() {
        return createdAt;
    }

    @JsonProperty("created_at")
    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    @JsonProperty("updated_at")
    public Instant getUpdatedAt() {
        return updatedAt;
    }

    @JsonProperty("updated_at")
    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }

    /** 本地编辑标记：修改内容后版本号自增，同步时用版本号判断谁更新。 */
    public void bumpVersion() {
        this.modifyInt += 1;
        this.updatedAt = Instant.now();
    }

    public boolean isDeleted() {
        return STATUS_DELETED.equals(status);
    }

    public Task copy() {
        Task copy = new Task();
        copy.id = id;
        copy.title = title;
        copy.content = content;
        copy.status = status;
        copy.priority = priority;
        copy.modifyInt = modifyInt;
        copy.createdAt = createdAt;
        copy.updatedAt = updatedAt;
        return copy;
    }

    @Override
    public String toString() {
        return "Task{id=" + id + ", title=" + title + ", status=" + status
                + ", priority=" + priority + ", modifyInt=" + modifyInt + "}";
    }
}