package com.taskcat.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.taskcat.model.Task;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * 后端 API 客户端：负责与 FastAPI 后端通信（JDK HttpClient + Jackson）。
 *
 * <p>接口前缀与后端一致：{@code /TaskCat/api/ver1.0}。
 */
public class TaskApiClient {

    /** 后端 API 默认前缀（与 fastapi/src/__init__.py 一致）。 */
    public static final String DEFAULT_API_PREFIX = "/TaskCat/api/ver1.0";

    private static final Duration CONNECT_TIMEOUT = Duration.ofSeconds(5);
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(10);

    private final HttpClient http;
    private final ObjectMapper mapper = JsonMapper.builder()
            .addModule(new JavaTimeModule())
            .build();
    private final String baseUrl;
    private final String apiPrefix;

    public TaskApiClient(String baseUrl) {
        this(baseUrl, DEFAULT_API_PREFIX);
    }

    public TaskApiClient(String baseUrl, String apiPrefix) {
        if (baseUrl.endsWith("/")) {
            baseUrl = baseUrl.substring(0, baseUrl.length() - 1);
        }
        this.baseUrl = baseUrl;
        this.apiPrefix = apiPrefix == null ? "" : apiPrefix;
        this.http = HttpClient.newBuilder()
                .connectTimeout(CONNECT_TIMEOUT)
                .build();
    }

    /** GET /task 返回体。 */
    public record TaskListResult(List<Task> tasks, String sound) {
    }

    /** POST /tasks/sync 返回体。 */
    public record SyncResult(List<Task> items, boolean changed, String sound, Instant timestamp) {
    }

    /** POST /task 返回体。 */
    public record CreateResult(Task task, String sound) {
    }

    /** 首次加载：拉取全部任务列表。 */
    public TaskListResult getTasks() throws Exception {
        String body = send("GET", "task", null);
        JsonNode root = mapper.readTree(body);
        List<Task> tasks = new ArrayList<>();
        for (JsonNode node : root.path("tasks")) {
            tasks.add(mapper.treeToValue(node, Task.class));
        }
        return new TaskListResult(tasks, root.path("sound").asText(null));
    }

    /** 双向增量同步：发送本地任务列表，返回服务端有更新的任务。 */
    public SyncResult sync(List<Task> clientTasks) throws Exception {
        String json = mapper.writeValueAsString(clientTasks == null ? List.of() : clientTasks);
        String body = send("POST", "tasks/sync", json);
        JsonNode root = mapper.readTree(body);
        List<Task> items = new ArrayList<>();
        for (JsonNode node : root.path("items")) {
            items.add(mapper.treeToValue(node, Task.class));
        }
        return new SyncResult(items, root.path("changed").asBoolean(false),
                root.path("sound").asText(null),
                root.path("timestamp").isMissingNode() ? Instant.now() : Instant.parse(root.path("timestamp").asText()));
    }

    /**
     * 新建任务。把表单字段整理成 JSON 发送给后端：
     * {@code {"title":..., "content":..., "status":..., "priority":...}}
     */
    public CreateResult create(String title, String content, String status, int priority) throws Exception {
        ObjectNode node = mapper.createObjectNode();
        node.put("title", title);
        node.put("content", content == null ? "" : content);
        node.put("status", status);
        node.put("priority", priority);
        String body = send("POST", "task", mapper.writeValueAsString(node));
        JsonNode root = mapper.readTree(body);
        return new CreateResult(mapper.treeToValue(root.path("task"), Task.class),
                root.path("sound").asText(null));
    }

    /** 按序号更新任务。只发送非 null 字段（部分更新，与后端 TaskUpdateModel 一致）。 */
    public Task update(int sequence, String title, String content, String status, Integer priority) throws Exception {
        ObjectNode node = mapper.createObjectNode();
        if (title != null) {
            node.put("title", title);
        }
        if (content != null) {
            node.put("content", content);
        }
        if (status != null) {
            node.put("status", status);
        }
        if (priority != null) {
            node.put("priority", priority);
        }
        String body = send("PATCH", "task/" + sequence, mapper.writeValueAsString(node));
        return mapper.readValue(body, Task.class);
    }

    /** 按序号软删除任务。 */
    public boolean delete(int sequence) throws Exception {
        String body = send("DELETE", "task/" + sequence, null);
        return mapper.readTree(body).path("ok").asBoolean(false);
    }

    private String send(String method, String path, String jsonBody) throws Exception {
        String url = baseUrl + apiPrefix + "/" + path;
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(REQUEST_TIMEOUT)
                .header("Accept", "application/json");
        if (jsonBody != null) {
            builder.header("Content-Type", "application/json")
                    .method(method, HttpRequest.BodyPublishers.ofString(jsonBody));
        } else if ("POST".equals(method)) {
            builder.method(method, HttpRequest.BodyPublishers.noBody());
        } else {
            builder.method(method, HttpRequest.BodyPublishers.noBody());
        }
        HttpResponse<String> response = http.send(builder.build(), HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() >= 400) {
            throw new IllegalStateException("HTTP " + response.statusCode() + " for " + method + " " + path);
        }
        return response.body();
    }
}