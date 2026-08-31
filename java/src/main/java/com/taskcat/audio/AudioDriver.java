package com.taskcat.audio;

import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 音频驱动门面：对外提供统一接口，屏蔽下载与播放细节。
 *
 * <p>职责：
 * <ol>
 *   <li>接收后端响应中的 {@code sound} 字段（相对路径或完整 URL）</li>
 *   <li>通过 {@link SoundDownloader} 从 FastAPI 后端下载音频</li>
 *   <li>通过 {@link AudioPlayer} 播放 WAV 数据</li>
 * </ol>
 *
 * <p>线程安全：本类是可重用的（下载与播放均为无状态操作），多个调用方可以共享同一个实例。
 */
public final class AudioDriver {

    /** 匹配 FastAPI 响应 JSON 中的 "sound" 字段值，如 {"sound": "/sounds/notification.wav"}。 */
    private static final Pattern SOUND_FIELD_PATTERN = Pattern.compile("\"sound\"\\s*:\\s*\"([^\"]+)\"");

    /** 后端 API 默认前缀（与 src/__init__.py 中的 include_router 前缀一致）。 */
    public static final String DEFAULT_API_PREFIX = "/TaskCat/api/ver1.0";

    private final String baseUrl;
    private final String apiPrefix;
    private final SoundDownloader downloader;

    public AudioDriver(String baseUrl) {
        this(baseUrl, DEFAULT_API_PREFIX);
    }

    /**
     * @param baseUrl   后端地址，如 {@code http://127.0.0.1:8000}
     * @param apiPrefix 路由前缀，如 {@code /TaskCat/api/ver1.0}；无需前缀时传空字符串
     */
    public AudioDriver(String baseUrl, String apiPrefix) {
        this.baseUrl = normalizeBaseUrl(baseUrl);
        this.apiPrefix = apiPrefix == null ? "" : apiPrefix;
        this.downloader = new SoundDownloader();
    }

    /**
     * 播放一条提示音。支持相对路径（相对后端 baseUrl）或完整 URL。
     *
     * @param sound 后端返回的 sound 字段值，如 "/sounds/notification.wav"
     * @throws Exception 下载或播放失败
     */
    public void play(String sound) throws Exception {
        Objects.requireNonNull(sound, "sound must not be null");
        if (sound.isEmpty()) {
            return;
        }
        String url = resolveUrl(sound);
        byte[] data = downloader.download(url);
        AudioPlayer.play(data);
    }

    /**
     * 从 FastAPI 的 JSON 响应中提取 "sound" 字段并播放。
     *
     * <p>适用于直接对接 {@code GET /task}、{@code POST /task}、{@code POST /tasks/sync} 的响应。
     *
     * @param json 后端返回的 JSON 字符串
     * @return true 表示 JSON 中存在 sound 字段且已播放；false 表示无 sound 字段
     * @throws Exception 下载或播放失败
     */
    public boolean playFromApiResponse(String json) throws Exception {
        Matcher matcher = SOUND_FIELD_PATTERN.matcher(json == null ? "" : json);
        if (!matcher.find()) {
            return false;
        }
        play(matcher.group(1));
        return true;
    }

    private String resolveUrl(String sound) {
        if (sound.startsWith("http://") || sound.startsWith("https://")) {
            return sound;
        }
        String path = sound.startsWith("/") ? sound : "/" + sound;
        return baseUrl + apiPrefix + path;
    }

    private static String normalizeBaseUrl(String baseUrl) {
        Objects.requireNonNull(baseUrl, "baseUrl must not be null");
        String url = baseUrl.endsWith("/")
                ? baseUrl.substring(0, baseUrl.length() - 1)
                : baseUrl;
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            throw new IllegalArgumentException("baseUrl must start with http:// or https://: " + baseUrl);
        }
        return url;
    }
}