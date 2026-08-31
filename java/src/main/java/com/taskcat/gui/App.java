package com.taskcat.gui;

import com.taskcat.audio.AudioDriver;
import com.taskcat.model.Task;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ButtonType;
import javafx.scene.control.ContextMenu;
import javafx.scene.control.Label;
import javafx.scene.control.ListCell;
import javafx.scene.control.ListView;
import javafx.scene.control.MenuItem;
import javafx.scene.control.SelectionMode;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.shape.Circle;
import javafx.stage.Stage;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Objects;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * TaskCat 主窗口（Google Play 风格）：
 * 卡片式任务列表 + 状态灯（红/黄/绿）+ 右下角悬浮「新建」+
 * 双击编辑 + 右键更多操作 + 2 秒轮询同步 + 变更提示音。
 */
public class App extends Application {

    private static final String DEFAULT_BASE_URL = "http://127.0.0.1:8000";
    private static final String DEFAULT_SOUND = "/sounds/test_beep.wav";
    private static final long SYNC_INTERVAL_SECONDS = 2;
    private static final DateTimeFormatter TIME_FORMAT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm").withZone(ZoneId.systemDefault());

    private final TaskApiClient client;
    private final SyncEngine engine = new SyncEngine();
    private final AudioDriver audioDriver;
    private final ScheduledExecutorService pool;

    private ListView<Task> listView;
    private Label statusLabel;

    public App() {
        this(DEFAULT_BASE_URL);
    }

    public App(String baseUrl) {
        this.client = new TaskApiClient(baseUrl);
        this.audioDriver = new AudioDriver(baseUrl);
        this.pool = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "taskcat-worker");
            t.setDaemon(true);
            return t;
        });
    }

    @Override
    public void start(Stage stage) {
        String baseUrl = getParameters().getNamed().getOrDefault("baseUrl", DEFAULT_BASE_URL);
        Scene scene = new Scene(buildUi(baseUrl), 720, 560);
        scene.getStylesheets().add(Objects.requireNonNull(
                getClass().getResource("/gui/style.css")).toExternalForm());
        stage.setTitle("TaskCat - 任务同步");
        stage.setScene(scene);
        stage.show();
        System.out.println("GUI_STARTED");

        loadInitial();
        startPolling();

        String smoke = System.getProperty("taskcat.smokeExitSeconds");
        if (smoke != null) {
            new Thread(() -> {
                try {
                    Thread.sleep(Long.parseLong(smoke) * 1000L);
                } catch (InterruptedException ignored) {
                }
                Platform.runLater(stage::close);
            }).start();
        }
    }

    private BorderPane buildUi(String baseUrl) {
        Label appTitle = new Label("TaskCat");
        appTitle.getStyleClass().add("app-title");

        statusLabel = new Label("后端: " + baseUrl);
        statusLabel.getStyleClass().add("status-text");

        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);

        HBox header = new HBox(12, appTitle, spacer, statusLabel);
        header.getStyleClass().add("header");
        header.setAlignment(Pos.CENTER_LEFT);

        listView = new ListView<>();
        listView.getSelectionModel().setSelectionMode(SelectionMode.SINGLE);
        listView.setCellFactory(lv -> new TaskCardCell());

        // 双击行 = 编辑
        listView.setOnMouseClicked(e -> {
            if (e.getClickCount() == 2) {
                Task t = listView.getSelectionModel().getSelectedItem();
                if (t != null) {
                    onEdit(t);
                }
            }
        });

        // 右下角悬浮「新建」
        Button fab = new Button("＋");
        fab.getStyleClass().add("fab");
        fab.setOnAction(e -> onCreate());

        StackPane center = new StackPane(listView, fab);
        StackPane.setAlignment(fab, Pos.BOTTOM_RIGHT);
        StackPane.setMargin(fab, new Insets(0, 24, 24, 0));

        BorderPane root = new BorderPane();
        root.setTop(header);
        root.setCenter(center);
        return root;
    }

    /** 卡片单元格：状态灯 + 标题/内容 + 优先级。 */
    private final class TaskCardCell extends ListCell<Task> {
        @Override
        protected void updateItem(Task task, boolean empty) {
            super.updateItem(task, empty);
            if (empty || task == null) {
                setGraphic(null);
                setContextMenu(null);
                return;
            }

            Circle light = new Circle(7);
            light.setFill(statusColor(task.getStatus()));

            Label title = new Label(task.getTitle());
            title.getStyleClass().add("task-title");

            VBox texts = new VBox(3);
            texts.getChildren().add(title);
            String content = task.getContent() == null ? "" : task.getContent().trim();
            if (!content.isEmpty()) {
                Label contentLabel = new Label(content);
                contentLabel.getStyleClass().add("task-content");
                texts.getChildren().add(contentLabel);
            }

            Label priority = new Label(String.valueOf(task.getPriority()));
            priority.getStyleClass().add("task-priority");

            Region spacer = new Region();
            HBox.setHgrow(spacer, Priority.ALWAYS);

            HBox card = new HBox(12, light, texts, spacer, priority);
            card.getStyleClass().add("task-card");
            card.setAlignment(Pos.CENTER_LEFT);
            setGraphic(card);

            ContextMenu menu = new ContextMenu();
            MenuItem edit = new MenuItem("编辑");
            edit.setOnAction(e -> onEdit(task));
            MenuItem toggle = new MenuItem(
                    Task.STATUS_DONE.equals(task.getStatus()) ? "标记为待办" : "标记为完成");
            toggle.setOnAction(e -> onToggleDone(task));
            MenuItem delete = new MenuItem("删除");
            delete.setOnAction(e -> onDelete(task));
            menu.getItems().addAll(edit, toggle, delete);
            setContextMenu(menu);
        }
    }

    private void loadInitial() {
        pool.execute(() -> {
            try {
                TaskApiClient.TaskListResult result = client.getTasks();
                Platform.runLater(() -> {
                    engine.replaceAll(result.tasks());
                    refreshList();
                    setStatus("已连接 · " + engine.orderedView().size() + " 个任务");
                    System.out.println("INIT_OK tasks=" + engine.orderedView().size());
                });
            } catch (Exception e) {
                Platform.runLater(() -> setStatus("连接后端失败: " + e.getMessage()));
            }
        });
    }

    private void startPolling() {
        pool.scheduleWithFixedDelay(() -> {
            try {
                TaskApiClient.SyncResult result = client.sync(engine.exportForSync());
                Platform.runLater(() -> {
                    engine.applyUpdates(result.items());
                    refreshList();
                    setStatus("已同步 · " + engine.orderedView().size() + " 个任务 · " + TIME_FORMAT.format(Instant.now()));
                    if (result.changed()) {
                        playSound(result.sound());
                    }
                });
            } catch (Exception ignored) {
                Platform.runLater(() -> setStatus("同步失败，稍后重试"));
            }
        }, SYNC_INTERVAL_SECONDS, SYNC_INTERVAL_SECONDS, TimeUnit.SECONDS);
    }

    private void onCreate() {
        TaskDialog.TaskForm form = TaskDialog.show(listView.getScene().getWindow(), null);
        if (form == null) {
            return;
        }
        pool.execute(() -> {
            try {
                TaskApiClient.CreateResult result =
                        client.create(form.title(), form.content(), Task.STATUS_TODO, form.priority());
                Platform.runLater(() -> {
                    engine.upsert(result.task());
                    refreshList();
                    setStatus("已创建任务");
                    playSound(result.sound());
                });
            } catch (Exception e) {
                showError("创建失败", e);
            }
        });
    }

    private void onEdit(Task task) {
        TaskDialog.TaskForm form = TaskDialog.show(listView.getScene().getWindow(), task);
        if (form == null) {
            return;
        }
        pool.execute(() -> {
            try {
                int seq = engine.sequenceOf(task.getId());
                if (seq < 0) {
                    return;
                }
                Task updated = client.update(seq, form.title(), form.content(), task.getStatus(), form.priority());
                Platform.runLater(() -> {
                    engine.upsert(updated);
                    refreshList();
                    setStatus("已保存修改");
                    playSound(null);
                });
            } catch (Exception e) {
                showError("保存失败", e);
            }
        });
    }

    private void onToggleDone(Task task) {
        String nextStatus = Task.STATUS_DONE.equals(task.getStatus())
                ? Task.STATUS_TODO : Task.STATUS_DONE;
        pool.execute(() -> {
            try {
                int seq = engine.sequenceOf(task.getId());
                if (seq < 0) {
                    return;
                }
                Task updated = client.update(seq, null, null, nextStatus, null);
                Platform.runLater(() -> {
                    engine.upsert(updated);
                    refreshList();
                    setStatus("状态已更新");
                    playSound(null);
                });
            } catch (Exception e) {
                showError("更新失败", e);
            }
        });
    }

    private void onDelete(Task task) {
        Alert confirm = new Alert(Alert.AlertType.CONFIRMATION,
                "确定删除任务「" + task.getTitle() + "」？", ButtonType.OK, ButtonType.CANCEL);
        confirm.initOwner(listView.getScene().getWindow());
        confirm.setHeaderText(null);
        confirm.showAndWait().ifPresent(button -> {
            if (button == ButtonType.OK) {
                pool.execute(() -> {
                    try {
                        int seq = engine.sequenceOf(task.getId());
                        if (seq < 0) {
                            return;
                        }
                        client.delete(seq);
                        Platform.runLater(() -> {
                            engine.removeLocal(task.getId());
                            refreshList();
                            setStatus("已删除任务");
                            playSound(null);
                        });
                    } catch (Exception e) {
                        showError("删除失败", e);
                    }
                });
            }
        });
    }

    private void playSound(String sound) {
        String url = sound == null || sound.isEmpty() ? DEFAULT_SOUND : sound;
        pool.execute(() -> {
            try {
                audioDriver.play(url);
            } catch (Exception ignored) {
                // 音频文件缺失或格式不支持时静默跳过，不影响主流程
            }
        });
    }

    private void refreshList() {
        ObservableList<Task> items = FXCollections.observableArrayList(engine.orderedView());
        listView.setItems(items);
    }

    private void setStatus(String text) {
        statusLabel.setText(text);
    }

    private void showError(String title, Exception e) {
        Platform.runLater(() -> {
            Alert alert = new Alert(Alert.AlertType.ERROR, e.getMessage(), ButtonType.OK);
            alert.setHeaderText(title);
            alert.initOwner(listView.getScene().getWindow());
            alert.showAndWait();
        });
    }

    /** 状态灯颜色：待办红、进行中黄、已完成绿。 */
    private static javafx.scene.paint.Color statusColor(String status) {
        if (status == null) {
            return javafx.scene.paint.Color.GRAY;
        }
        return switch (status) {
            case Task.STATUS_DONE -> javafx.scene.paint.Color.web("#30a46c");
            case Task.STATUS_DOING -> javafx.scene.paint.Color.web("#f5a623");
            case Task.STATUS_TODO -> javafx.scene.paint.Color.web("#e5484d");
            default -> javafx.scene.paint.Color.GRAY;
        };
    }

    @Override
    public void stop() {
        pool.shutdownNow();
        Platform.exit();
    }

    public static void main(String[] args) {
        launch(args);
    }
}