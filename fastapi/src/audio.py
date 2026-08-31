def play_task_sound(sound_name: str = "task_update") -> None:
    """音频播放入口。

    这里留一个统一调用点，后续可以接入浏览器 Audio、playsound、系统 beep 等。
    例如：
        - 浏览器端：new Audio('/sound/task.mp3').play()
        - Python：playsound('sound/task.mp3')
        - 桌面端：QSound / pygame / system beep
    """
    # TODO: 具体业务实现放这里
    return None
