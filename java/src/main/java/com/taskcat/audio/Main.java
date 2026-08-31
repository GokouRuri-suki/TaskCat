package com.taskcat.audio;

/**
 * 命令行演示：从后端下载提示音并播放。
 *
 * <p>用法：
 * <pre>
 * java -jar taskcat-audio-driver.jar [baseUrl] [soundPath]
 * java -jar taskcat-audio-driver.jar http://127.0.0.1:8000 /sounds/notification.wav
 * </pre>
 */
public final class Main {

    private Main() {
    }

    public static void main(String[] args) {
        String baseUrl = args.length > 0 ? args[0] : "http://127.0.0.1:8000";
        String sound = args.length > 1 ? args[1] : "/sounds/notification.wav";

        AudioDriver driver = new AudioDriver(baseUrl);
        try {
            System.out.println("TaskCat 音频驱动");
            System.out.println("  后端:  " + baseUrl);
            System.out.println("  音频:  " + sound);
            System.out.println("开始播放...");
            driver.play(sound);
            System.out.println("播放完成");
        } catch (Exception e) {
            System.err.println("播放失败: " + e.getMessage());
            System.exit(1);
        }
    }
}