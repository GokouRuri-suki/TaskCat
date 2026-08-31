package com.taskcat.gui;

import com.taskcat.model.Task;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 联调测试：连接真实后端（默认 http://127.0.0.1:8000）验证
 * GET → create(表单JSON) → sync → update → delete 全流程。
 *
 * <p>由 surefire 的 IT 命名规则排除，仅在显式执行时运行：
 * {@code mvn test -Dtest=LiveApiIT}
 */
class LiveApiIT {

    private static final String BASE_URL =
            System.getProperty("taskcat.baseUrl", "http://127.0.0.1:8000");

    @Test
    void fullApiFlow() throws Exception {
        TaskApiClient client = new TaskApiClient(BASE_URL);
        SyncEngine engine = new SyncEngine();

        // 1. 首次加载
        TaskApiClient.TaskListResult list = client.getTasks();
        engine.replaceAll(list.tasks());
        assertNotNull(list.tasks());
        System.out.println("[1] GET /task -> " + engine.orderedView().size() + " tasks");

        // 2. 新建（表单字段 -> JSON -> POST /task）
        String title = "IT-" + System.currentTimeMillis() % 100000;
        TaskApiClient.CreateResult created = client.create(title, "form from Java GUI", "todo", 3);
        engine.upsert(created.task());
        assertNotNull(created.task().getId());
        assertEquals(1, created.task().getModifyInt());
        assertEquals(3, created.task().getPriority());
        System.out.println("[2] POST /task -> id=" + created.task().getId() + " modify_int=" + created.task().getModifyInt());

        // 3. sync 应有更新
        TaskApiClient.SyncResult sync = client.sync(engine.exportForSync());
        engine.applyUpdates(sync.items());
        System.out.println("[3] sync -> changed=" + sync.changed() + " items=" + sync.items().size());

        // 4. 按序号修改
        int seq = engine.sequenceOf(created.task().getId());
        assertTrue(seq >= 1);
        Task updated = client.update(seq, null, "edited", "doing", 1);
        engine.upsert(updated);
        assertEquals("doing", updated.getStatus());
        assertEquals(1, updated.getPriority());
        assertEquals(2, updated.getModifyInt());
        System.out.println("[4] PATCH /task/" + seq + " -> status=" + updated.getStatus() + " modify_int=" + updated.getModifyInt());

        // 5. 删除
        boolean ok = client.delete(seq);
        engine.removeLocal(created.task().getId());
        assertTrue(ok);
        System.out.println("[5] DELETE /task/" + seq + " -> ok=" + ok);

        System.out.println("LIVE OK");
    }
}