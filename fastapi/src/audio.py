import functools
import inspect
import subprocess
import sys
from pathlib import Path
from typing import Optional


class AudioPlayer:
    """跨平台音频播放器。"""
    
    def __init__(self):
        self.supported_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.mp4'}
        self._detect_players()
    
    def _detect_players(self):
        """检测系统可用的音频播放器。"""
        self.players = []
        
        if sys.platform == "darwin":  # macOS
            self.players.extend([
                ("afplay", ["{file}"]),  # macOS内置播放器
                ("ffplay", ["-nodisp", "-autoexit", "{file}"]),  # FFmpeg
                ("mpg123", ["{file}"]),  # MP3播放器
            ])
        elif sys.platform == "win32":  # Windows
            self.players.extend([
                ("powershell", ["-c", "(New-Object Media.SoundPlayer '{file}').PlaySync()"]),  # PowerShell播放WAV
                ("ffplay", ["-nodisp", "-autoexit", "{file}"]),  # FFmpeg
            ])
        else:  # Linux和其他Unix-like系统
            self.players.extend([
                ("paplay", ["{file}"]),  # PulseAudio
                ("aplay", ["{file}"]),   # ALSA
                ("mpg123", ["{file}"]),  # MP3播放器
                ("mpg321", ["{file}"]),  # 另一个MP3播放器
                ("ffplay", ["-nodisp", "-autoexit", "{file}"]),  # FFmpeg
                ("cvlc", ["--play-and-exit", "{file}"]),  # VLC
                ("mplayer", ["{file}"]),  # MPlayer
            ])
    
    def _find_working_player(self) -> Optional[str]:
        """查找系统中可用的音频播放器。"""
        for player_cmd, _ in self.players:
            try:
                # 检查命令是否存在
                if sys.platform == "win32":
                    # Windows使用where命令
                    result = subprocess.run(
                        ["where", player_cmd],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                else:
                    # Unix-like系统使用which命令
                    result = subprocess.run(
                        ["which", player_cmd],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                
                if result.returncode == 0:
                    return player_cmd
            except Exception:
                continue
        return None
    
    def play(self, file_path: str) -> bool:
        """播放音频文件。
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bool: 播放是否成功
        """
        try:
            audio_file = Path(file_path)
            
            # 验证文件
            if not audio_file.exists():
                return False
            
            if not audio_file.is_file():
                return False
            
            # 检查文件格式
            if audio_file.suffix.lower() not in self.supported_extensions:
                return False
            
            # 查找可用的播放器
            player_cmd = self._find_working_player()
            if not player_cmd:
                return False
            
            # 获取该播放器的参数
            player_args = None
            for cmd, args in self.players:
                if cmd == player_cmd:
                    player_args = args
                    break
            
            if not player_args:
                return False
            
            # 构建命令
            cmd_args = []
            for arg in player_args:
                cmd_args.append(arg.format(file=str(audio_file)))
            
            # 执行播放命令
            subprocess.run(
                [player_cmd] + cmd_args,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30  # 30秒超时
            )
            
            return True
            
        except Exception:
            return False


# 全局音频播放器实例
_audio_player = AudioPlayer()


def play_task_sound(sound_path: Optional[str] = None) -> bool:
    """播放指定路径的音频文件。
    
    这是一个完整可用的音频播放函数，支持跨平台播放多种音频格式。
    
    Args:
        sound_path: 音频文件路径。如果为None或空字符串，则返回False。
        
    Returns:
        bool: 播放是否成功
        
    Examples:
        >>> play_task_sound("/path/to/sound.mp3")  # 播放MP3文件
        True
        
        >>> play_task_sound("sounds/notification.wav")  # 播放WAV文件
        True
        
        >>> play_task_sound()  # 不播放，返回False
        False
        
        >>> play_task_sound("nonexistent.mp3")  # 文件不存在，返回False
        False
    """
    if not sound_path:
        return False
    
    return _audio_player.play(sound_path)


# 只接收音频文件路径的装饰器
# 用法：@playAudio("src/sounds/test_beep.wav")
def playAudio(sound_path: str):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                play_task_sound(sound_path)
                return result
            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            play_task_sound(sound_path)
            return result

        return sync_wrapper

    return decorator
        