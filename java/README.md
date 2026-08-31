# TaskCat Java 客户端

TaskCat 的 Java 客户端：**JavaFX GUI**（任务管理 + 双向同步）+ **音频驱动**（下载并播放后端提示音）。

## 结构

```
java/
├── pom.xml                                  # Maven 构建（JavaFX 21 + Jackson）
└── src/
    ├── main/java/com/taskcat/
    │   ├── audio/                           # 音频驱动（纯 JDK，零依赖）
    │   │   ├── AudioDriver.java             # 门面：统一下载+播放
    │   │   ├── SoundDownloader.java         # HttpClient 下载音频
    │   │   ├── AudioPlayer.java             # javax.sound.sampled 播放 WAV
    │   │   └── Main.java                    # 命令行播放演示
    │   ├── model/Task.java                  # 后端 TaskItemModel 的镜像
    │   └── gui/
    │       ├── App.java                     # JavaFX 主窗口（任务列表 + 轮询同步）
    │       ├── TaskApiClient.java           # 后端 REST 客户端（JSON 序列化）
    │       ├── TaskDialog.java              # 新建/编辑弹窗（表单 -> JSON）
    │       └── SyncEngine.java              # 双向增量同步（版本合并）
    └── test/java/com/taskcat/gui/
        ├── SyncEngineTest.java              # 单元测试（8 个用例）
        └── LiveApiIT.java                   # 联调测试（需后端运行）
```

## 运行前提

1. **后端已启动**（在 `../fastapi/` 目录）：`python -m uvicorn src:app --host 127.0.0.1 --port 8000`
2. **JDK 17+ 与 Maven 3.9+**

## 运行 GUI

```bash
cd java
mvn compile
mvn javafx:run
```

指定后端地址：`mvn javafx:run -Djavafx.args=--baseUrl=http://127.0.0.1:8000`

### 功能
- **主窗口**：表格显示任务（名称/内容/状态/优先级/更新时间），底部显示后端与同步状态
- **新建**：弹窗填写名称、内容、优先级，点「确认」后把表单整理成 JSON 发给后端 `POST /task`
- **编辑**：双击行或选中后点「编辑」
- **删除 / 标记完成 / 恢复**：一键操作
- **自动同步**：每 2 秒 `POST /tasks/sync` 双向增量同步，检测到变更自动播放提示音

## 测试

```bash
# 单元测试（无需后端）
mvn test

# 联调测试（需后端运行在 8000 端口）
mvn test -Dtest=LiveApiIT
```

## 音频驱动（命令行演示，可选）

```bash
mvn compile
java -cp target/classes com.taskcat.audio.Main http://127.0.0.1:8000 /sounds/test_beep.wav
```

## 注意

- 后端路由前缀默认 `/TaskCat/api/ver1.0`（与 `fastapi/src/__init__.py` 一致），
  改前缀用 `TaskApiClient(baseUrl, apiPrefix)` / `AudioDriver(baseUrl, apiPrefix)`。
- 后端 `sounds/notification.wav` 目前是**占位文本**，播放会报格式错误；
  请放入真实 WAV（如 `sounds/test_beep.wav`）。GUI 变更提示音默认用 `test_beep.wav`。