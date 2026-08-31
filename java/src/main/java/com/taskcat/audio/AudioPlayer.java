package com.taskcat.audio;

import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import javax.sound.sampled.LineEvent;
import javax.sound.sampled.LineListener;
import java.io.ByteArrayInputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * 音频播放器：使用 {@link Clip} 播放 WAV 数据。
 *
 * <p>设计要点：
 * <ul>
 *   <li>非阻塞：播放期间通过 {@link CountDownLatch} 等待自然播完，避免占用主线程太久</li>
 *   <li>带超时：最多等待 10 秒，防止音频异常导致线程永久阻塞</li>
 *   <li>纯 JDK 实现：只依赖 {@code javax.sound.sampled}，无需第三方库</li>
 * </ul>
 */
public final class AudioPlayer {

    /** 最长播放等待时间（秒），防止异常音频导致永久阻塞。 */
    private static final long PLAY_TIMEOUT_SECONDS = 10;

    private AudioPlayer() {
    }

    /**
     * 播放一段 WAV 音频数据，返回时表示播放已结束（或超时）。
     *
     * @param wavData WAV 格式的音频字节
     * @throws Exception 音频格式不支持、无法打开音频线路或播放失败
     */
    public static void play(byte[] wavData) throws Exception {
        if (wavData == null || wavData.length == 0) {
            throw new IllegalArgumentException("wav data is empty");
        }

        try (AudioInputStream ais = AudioSystem.getAudioInputStream(new ByteArrayInputStream(wavData));
             Clip clip = AudioSystem.getClip()) {

            clip.open(ais);

            CountDownLatch finished = new CountDownLatch(1);
            clip.addLineListener(new LineListener() {
                @Override
                public void update(LineEvent event) {
                    if (event.getType() == LineEvent.Type.STOP) {
                        finished.countDown();
                    }
                }
            });

            clip.start();
            finished.await(PLAY_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        }
    }
}