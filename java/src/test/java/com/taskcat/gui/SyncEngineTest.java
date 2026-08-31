package com.taskcat.gui;

import com.taskcat.model.Task;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SyncEngineTest {

    private static Task task(String id, int modifyInt, int priority, String status) {
        Task t = new Task();
        t.setId(id);
        t.setTitle("task-" + id);
        t.setPriority(priority);
        t.setStatus(status);
        t.setModifyInt(modifyInt);
        return t;
    }

    @Test
    void replaceAll_loadsServerTasks() {
        SyncEngine engine = new SyncEngine();
        engine.replaceAll(List.of(task("a", 1, 5, "todo"), task("b", 1, 2, "done")));

        List<Task> view = engine.orderedView();
        assertEquals(2, view.size());
        assertEquals("b", view.get(0).getId()); // priority 2 排前面
    }

    @Test
    void applyUpdates_addsUnknownTask() {
        SyncEngine engine = new SyncEngine();
        engine.replaceAll(List.of(task("a", 1, 5, "todo")));
        engine.applyUpdates(List.of(task("b", 1, 3, "todo")));

        assertEquals(2, engine.orderedView().size());
    }

    @Test
    void applyUpdates_overwritesWhenServerNewer() {
        SyncEngine engine = new SyncEngine();
        Task local = task("a", 1, 5, "todo");
        local.setTitle("旧标题");
        engine.replaceAll(List.of(local));

        Task newer = task("a", 3, 5, "done");
        newer.setTitle("新标题");
        engine.applyUpdates(List.of(newer));

        Task merged = engine.orderedView().get(0);
        assertEquals("新标题", merged.getTitle());
        assertEquals("done", merged.getStatus());
        assertEquals(3, merged.getModifyInt());
    }

    @Test
    void applyUpdates_ignoresEqualOrOlderVersion_noEcho() {
        SyncEngine engine = new SyncEngine();
        Task local = task("a", 5, 5, "todo");
        local.setTitle("本地内容");
        engine.replaceAll(List.of(local));

        // 服务端回显同一版本，不应覆盖本地
        Task echo = task("a", 5, 5, "todo");
        echo.setTitle("回显内容");
        engine.applyUpdates(List.of(echo));

        assertEquals("本地内容", engine.orderedView().get(0).getTitle());
        assertEquals(5, engine.orderedView().get(0).getModifyInt());
    }

    @Test
    void applyUpdates_removesDeletedTasks() {
        SyncEngine engine = new SyncEngine();
        engine.replaceAll(List.of(task("a", 1, 5, "todo"), task("b", 1, 3, "todo")));

        Task deleted = task("b", 4, 3, "deleted");
        engine.applyUpdates(List.of(deleted));

        assertEquals(1, engine.orderedView().size());
        assertEquals("a", engine.orderedView().get(0).getId());
    }

    @Test
    void sequenceOf_usesPriorityOrder() {
        SyncEngine engine = new SyncEngine();
        engine.replaceAll(List.of(task("a", 1, 9, "todo"), task("b", 1, 1, "todo"), task("c", 1, 5, "todo")));

        assertEquals(1, engine.sequenceOf("b"));
        assertEquals(2, engine.sequenceOf("c"));
        assertEquals(3, engine.sequenceOf("a"));
        assertEquals(-1, engine.sequenceOf("nope"));
    }

    @Test
    void upsert_addsOrReplaces() {
        SyncEngine engine = new SyncEngine();
        engine.replaceAll(List.of(task("a", 1, 5, "todo")));

        Task existing = task("a", 2, 4, "doing");
        existing.setTitle("改");
        engine.upsert(existing);
        Task fresh = task("new", 1, 1, "todo");
        engine.upsert(fresh);

        assertEquals(2, engine.orderedView().size());
        assertTrue(engine.orderedView().stream().anyMatch(t -> "new".equals(t.getId())));
    }

    @Test
    void exportForSync_isImmutableCopy() {
        SyncEngine engine = new SyncEngine();
        Task original = task("a", 1, 5, "todo");
        original.setTitle("原始");
        engine.replaceAll(List.of(original));

        List<Task> exported = engine.exportForSync();
        exported.get(0).setTitle("外部篡改");

        assertEquals("原始", engine.orderedView().get(0).getTitle());
    }
}