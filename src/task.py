from datetime import datetime
import os
from enum import Enum
import threading
from threading import Thread, Lock, RLock
from typing import List, Dict

from logger import logger


class TaskStatus(Enum):
    Available = 0
    Taken = 1
    Starting = 2
    Running = 3
    Completing = 4
    Completed = 5
    Failed = -1


class TaskRunMode(Enum):
    Default = 0
    Isolated = 1


class Task:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = TaskStatus.Available
        self.cwd = os.getcwd()
        self.env = os.environ.copy()

    def get_cwd_mode(self) -> TaskRunMode:
        raise NotImplementedError

    def get_display_mode(self) -> TaskRunMode:
        raise NotImplementedError

    def before(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def after(self):
        raise NotImplementedError


class TaskDependency:
    def __init__(self, task: Task):
        self.task = task
        self.children = []

    def has_children(self):
        return bool(self.children)

    def add_child(self, child):
        if TaskDependency.is_task_dependency(child):
            self.children.append(child)

    def is_child(self, child):
        return child in self.children

    def promote_grandchildren_to_children(self, child):
        if self.is_child(child):
            grandchildren = child.children
            self.children.pop(child)
            if grandchildren:
                self.children.extend(grandchildren)

    @staticmethod
    def is_task_dependency(other):
        return TaskDependency is type(other)


class TaskManager:
    dummy_task = Task("dummy")

    class ThreadInfo:
        def __init__(self, thread_id: int, thread: Thread):
            self.thread_id: int = thread_id
            self.thread: Thread = thread

    def __init__(self, max_parallel_tasks, on_task_finish_callback: callable):
        self.max_parallel_tasks = max_parallel_tasks
        self.callback_rlock = RLock()
        self.on_task_finish_callback = on_task_finish_callback
        self.tasks: Dict[str, Task] = {}
        self.dep_tree_lock = Lock()
        self.thread_pool_rlock = RLock()
        self.thread_info_pool: Dict[str, TaskManager.ThreadInfo] = {}
        self.running = False

    def add_task(self, task: Task):
        if task.task_id not in self.tasks or (task.task_id in self.tasks and
                                              self.tasks[task.task_id].status == TaskStatus.Failed and
                                              task.status == TaskStatus.Available):
            self.tasks[task.task_id] = task

    def get_dependency_tree(self, root: TaskDependency, task_list: List[Task]) -> TaskDependency:
        raise NotImplementedError

    def start(self):
        self.running = True

        def run():
            thread_name = threading.current_thread().getName()
            logger.info("TaskManager", "Thread %s starting" % thread_name)
            task = TaskManager.dummy_task
            while task and self.running:
                task = self.get_available_task()
                if task:
                    if task.get_cwd_mode() == TaskRunMode.Isolated:
                        task.cwd = os.path.join("..", "%s-%s" % (thread_name, task.task_id))
                    with self.thread_pool_rlock:
                        if task.get_display_mode() == TaskRunMode.Isolated:
                            task.env["DISPLAY"] = ":%d" % self.thread_info_pool[thread_name].thread_id
                    logger.info("TaskManager", "Thread %s is starting task ID = %s" % (thread_name, task.task_id))
                    date_start = datetime.now()
                    task.start()
                    delta_seconds = (datetime.now() - date_start).total_seconds()
                    print_info = (thread_name, task.task_id, delta_seconds)
                    logger.info("TaskManager", "Thread %s finished task ID = %s in %d seconds" % print_info)
                    with self.callback_rlock:
                        self.on_task_finish_callback()
                    check_thread_pool()
            if not task:
                logger.info("TaskManager", "Thread %s has no task to run" % thread_name)
            logger.info("TaskManager", "Thread %s stopping" % thread_name)
            with self.thread_pool_rlock:
                self.thread_info_pool.pop(thread_name)

        def get_available_thread_id() -> int:
            with self.thread_pool_rlock:
                thread_id = 1
                taken_ids = [self.thread_info_pool[thread_name].thread_id for thread_name in self.thread_info_pool]
                while thread_id in taken_ids:
                    thread_id += 1
                return thread_id

        def spawn_thread():
            with self.thread_pool_rlock:
                if len(self.thread_info_pool) >= self.max_parallel_tasks:
                    return
                thread_id = get_available_thread_id()
                thread_name = "TaskManager%d" % thread_id
                thread_info = TaskManager.ThreadInfo(thread_id, Thread(target=run, name=thread_name))
                self.thread_info_pool[thread_name] = thread_info
                thread_info.thread.start()

        def check_thread_pool():
            with self.thread_pool_rlock:
                threads_left = self.max_parallel_tasks - len(self.thread_info_pool)
                for i in range(threads_left):
                    spawn_thread()

        check_thread_pool()

    def stop(self, wait=False):
        self.running = False
        if wait:
            self.wait_for_all()

    def wait_for_all(self):
        while self.thread_info_pool:
            k = list(self.thread_info_pool)[-1]
            self.thread_info_pool[k].thread.join()

    def status(self):
        count_total = len(self.tasks)
        count_available = 0
        count_taken = 0
        count_starting = 0
        count_running = 0
        count_completing = 0
        count_completed = 0
        count_failed = 0
        which_failed = []

        for _, v in self.tasks.items():
            count_available += 1 if v.status == TaskStatus.Available else 0
            count_taken += 1 if v.status == TaskStatus.Taken else 0
            count_starting += 1 if v.status == TaskStatus.Starting else 0
            count_running += 1 if v.status == TaskStatus.Running else 0
            count_completing += 1 if v.status == TaskStatus.Completing else 0
            count_completed += 1 if v.status == TaskStatus.Completed else 0
            if v.status == TaskStatus.Failed:
                count_failed += 1
                which_failed.append(v.task_id)

        total = "Total: %d" % count_total
        available = "Available: %d" % count_available
        taken = "Taken: %d" % count_taken
        starting = "Starting: %d" % count_starting
        running = "Running: %d" % count_running
        completing = "Completing: %d" % count_completing
        completed = "Completed: %d" % count_completed
        failed = "Failed: %d" % count_failed

        print_info = (available, taken, starting, running, completing, completed, failed, total)
        logger.info("TaskManager", "Task status: %s | %s | %s | %s | %s | %s | %s | %s" % print_info)
        if which_failed:
            logger.info("TaskManager", "Failed task IDs:")
        for t_id in which_failed:
            logger.info("TaskManager", "\tTask ID = %s" % t_id)

        if not self.thread_info_pool:
            self.running = False

    def get_available_task(self) -> Task:

        def find_next_available_task(dep_tree: TaskDependency) -> Task:
            available_task = None
            if dep_tree.task.status == TaskStatus.Available:
                available_task = dep_tree.task
            elif dep_tree.task.status == TaskStatus.Completed:
                for dep_tree_child in dep_tree.children:
                    available_task = find_next_available_task(dep_tree_child)
                    if available_task:
                        break
            return available_task

        with self.dep_tree_lock:
            root = TaskDependency(Task("root"))
            root.task.status = TaskStatus.Completed
            task_list = [self.tasks[t_id] for t_id in self.tasks]
            task_to_run = find_next_available_task(self.get_dependency_tree(root, task_list))
            if task_to_run:
                task_to_run.status = TaskStatus.Taken
            return task_to_run
