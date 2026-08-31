package com.taskcat.audio;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * 音频下载器：使用 JDK {@link HttpClient} 从后端下载音频文件字节。
 *
 * <p>对应 FastAPI 后端的 {@code GET /sounds/{filename}} 接口。
 */
public final class SoundDownloader {

    private static final Duration CONNECT_TIMEOUT = Duration.ofSeconds(5);
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(10);

    private final HttpClient client;

    public SoundDownloader() {
        this.client = HttpClient.newBuilder()
                .connectTimeout(CONNECT_TIMEOUT)
                .build();
    }

    /**
     * 下载指定 URL 的音频内容。
     *
     * @param url 完整的音频 URL（如 {@code http://127.0.0.1:8000/sounds/notification.wav}）
     * @return 音频文件字节
     * @throws Exception 网络异常或服务端返回非 200 状态码
     */
    public byte[] download(String url) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(REQUEST_TIMEOUT)
                .GET()
                .build();

        HttpResponse<byte[]> response = client.send(request, HttpResponse.BodyHandlers.ofByteArray());
        if (response.statusCode() != 200) {
            throw new IllegalStateException(
                    "Failed to download sound, HTTP " + response.statusCode() + ": " + url);
        }
        return response.body();
    }
}