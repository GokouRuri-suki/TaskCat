package com.taskcat.gui;

import com.taskcat.model.Task;
import javafx.geometry.Insets;
import javafx.scene.control.ButtonBar;
import javafx.scene.control.ButtonType;
import javafx.scene.control.Dialog;
import javafx.scene.control.Label;
import javafx.scene.control.Spinner;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.GridPane;
import javafx.stage.Window;

/**
 * 新建/编辑任务弹窗。表单字段（名称、内容、优先级）在点「确认」后
 * 由调用方整理成 JSON 发送给后端。
 */
public class TaskDialog {

    /** 表单数据。 */
    public record TaskForm(String title, String content, int priority) {
    }

    private TaskDialog() {
    }

    /**
     * 弹出任务表单。
     *
     * @param owner 父窗口
     * @param existing 编辑已有任务时传入；新建传 null
     * @return 确认后的表单数据；取消返回 null
     */
    public static TaskForm show(Window owner, Task existing) {
        Dialog<TaskForm> dialog = new Dialog<>();
        dialog.initOwner(owner);
        dialog.setTitle(existing == null ? "新建任务" : "编辑任务");

        ButtonType okButton = new ButtonType("确认", ButtonBar.ButtonData.OK_DONE);
        ButtonType cancelButton = new ButtonType("取消", ButtonBar.ButtonData.CANCEL_CLOSE);
        dialog.getDialogPane().getButtonTypes().addAll(okButton, cancelButton);

        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(10);
        grid.setPadding(new Insets(16));

        TextField titleField = new TextField();
        titleField.setPromptText("任务名称");
        titleField.setPrefWidth(320);

        TextArea contentArea = new TextArea();
        contentArea.setPromptText("要做什么（可选）");
        contentArea.setPrefRowCount(6);
        contentArea.setPrefColumnCount(30);

        Spinner<Integer> prioritySpinner = new Spinner<>(Task.PRIORITY_MIN, Task.PRIORITY_MAX,
                existing != null ? existing.getPriority() : Task.PRIORITY_DEFAULT);
        prioritySpinner.setEditable(true);

        if (existing != null) {
            titleField.setText(existing.getTitle());
            contentArea.setText(existing.getContent());
        }

        grid.add(new Label("名称 *"), 0, 0);
        grid.add(titleField, 1, 0);
        grid.add(new Label("内容"), 0, 1);
        grid.add(contentArea, 1, 1);
        grid.add(new Label("优先级 (1-10)"), 0, 2);
        grid.add(prioritySpinner, 1, 2);

        dialog.getDialogPane().setContent(grid);

        dialog.setResultConverter(button -> {
            if (button == okButton) {
                String title = titleField.getText() == null ? "" : titleField.getText().trim();
                if (title.isEmpty()) {
                    return null;
                }
                int priority = prioritySpinner.getValue() == null ? Task.PRIORITY_DEFAULT : prioritySpinner.getValue();
                return new TaskForm(title, contentArea.getText(), priority);
            }
            return null;
        });

        // 校验：名称为空时点确认不关闭弹窗
        javafx.scene.Node okNode = dialog.getDialogPane().lookupButton(okButton);
        okNode.addEventFilter(javafx.scene.input.MouseEvent.MOUSE_CLICKED, event -> {
            String title = titleField.getText() == null ? "" : titleField.getText().trim();
            if (title.isEmpty()) {
                event.consume();
            }
        });

        return dialog.showAndWait().orElse(null);
    }
}