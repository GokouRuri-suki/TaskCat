package com.taskcat.gui;

import com.taskcat.model.Task;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 双向增量同步引擎（客户端侧），移植自后端 {@code service.sync_tasks} 的版本合并规则。
 *
 * <p>规则：
 * <ul>
 *   <li>本地编辑自增 {@code modify_int}，通过 sync 发送，服务端会吸收更高版本</li>
 *   <li>sync 响应中返回的是服务端比客户端更新的任务（{@code modify_int} 更大）</li>
 *   <li>只接受版本号更大的项，防止把客户端刚发上去的改动再回写覆盖（防回环）</li>
 *   <li>状态为 {@code deleted} 的任务从本地视图移除</li>
 * </ul>
 *
 * <p>线程安全：所有方法同步，GUI 轮询线程与 UI 线程共用同一实例。
 */
public class SyncEngine {

    private final List<Task> tasks = new ArrayList<>();

    /** 首次加载：用 GET /task 的全量结果替换本地。 */
    public synchronized void replaceAll(List<Task> serverTasks) {
        tasks.clear();
        if (serverTasks != null) {
            for (Task t : serverTasks) {
                if (!t.isDeleted()) {
                    tasks.add(t.copy());
                }
            }
        }
    }

    /** 把 sync 响应中的更新合并进本地（版本号更大的才覆盖）。 */
    public synchronized void applyUpdates(List<Task> serverItems) {
        if (serverItems == null) {
            return;
        }
        for (Task server : serverItems) {
            Task local = findById(server.getId());
            if (local == null) {
                if (!server.isDeleted()) {
                    tasks.add(server.copy());
                }
            } else if (server.getModifyInt() > local.getModifyInt()) {
                replace(local, server);
            }
            // 服务端版本 <= 本地版本：忽略，避免回环覆盖
        }
        tasks.removeIf(Task::isDeleted);
    }

    /** 新建/更新后的任务落库（服务端返回的权威版本）。 */
    public synchronized void upsert(Task serverTask) {
        if (serverTask == null) {
            return;
        }
        Task local = findById(serverTask.getId());
        if (local == null) {
            tasks.add(serverTask.copy());
        } else {
            replace(local, serverTask);
        }
    }

    /** 本地删除：把任务标记为 deleted 并移除（软删除，便于 sync 上报）。 */
    public synchronized void removeLocal(String id) {
        tasks.removeIf(t -> id.equals(t.getId()));
    }

    /** 按优先级升序的显示视图（数字越小优先级越高）。 */
    public synchronized List<Task> orderedView() {
        List<Task> view = new ArrayList<>(tasks);
        view.sort(Comparator.comparingInt(Task::getPriority));
        return view;
    }

    /** 当前任务在优先级排序视图中的序号（1 开始），用于 PATCH/DELETE；找不到返回 -1。 */
    public synchronized int sequenceOf(String id) {
        List<Task> view = orderedView();
        for (int i = 0; i < view.size(); i++) {
            if (id.equals(view.get(i).getId())) {
                return i + 1;
            }
        }
        return -1;
    }

    /** 导出用于 sync 上报的副本（带本地版本号）。 */
    public synchronized List<Task> exportForSync() {
        List<Task> copy = new ArrayList<>(tasks.size());
        for (Task t : tasks) {
            copy.add(t.copy());
        }
        return copy;
    }

    public synchronized boolean isEmpty() {
        return tasks.isEmpty();
    }

    private Task findById(String id) {
        for (Task t : tasks) {
            if (id.equals(t.getId())) {
                return t;
            }
        }
        return null;
    }

    private void replace(Task local, Task fresh) {
        Task copy = fresh.copy();
        int index = tasks.indexOf(local);
        if (index >= 0) {
            tasks.set(index, copy);
        } else {
            tasks.add(copy);
        }
    }
}