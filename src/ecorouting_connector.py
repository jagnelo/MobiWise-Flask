import os
from subprocess import STDOUT, PIPE, TimeoutExpired
from typing import Dict, Union

import utils
from globals import Globals

if not utils.is_module_available("ecorouting"):
    module = utils.import_module(os.path.join(Globals.ECOROUTING_DIR, "testcases.py"), "testcases")
    testcases = getattr(module, "testcases")
else:
    from ecorouting.testcases import testcases
from spopen import SPopen
from task import Task, TaskStatus, TaskManager, TaskDependency, TaskRunMode


class EcoRoutingMode:
    def get_additional_args(self):
        raise NotImplementedError

    def run(self, process: SPopen):
        raise NotImplementedError


class EcoRoutingTask(Task):
    def __init__(self, task_id, scenario, mode: EcoRoutingMode):
        Task.__init__(self, task_id)
        self.scenario = scenario
        self.mode = mode

    def get_cwd_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def get_display_mode(self) -> TaskRunMode:
        return TaskRunMode.Default

    def get_cmd(self):
        return ["python", "main-interactive.py", "-t", self.scenario, *self.mode.get_additional_args()]

    def before(self):
        if self.cwd != os.getcwd():
            utils.ensure_dir_exists(self.cwd)
            utils.clear_dir(self.cwd)
            utils.copy_dir_contents(Globals.ECOROUTING_DIR, self.cwd)

    def start(self):
        if self.cwd == os.getcwd() or self.cwd == Globals.ECOROUTING_DIR:
            print("WARNING: EcoRoutingTask task ID = %s is set for cwd %s" % (self.task_id, self.cwd))
        cmd = self.get_cmd()
        eco_proc = SPopen(cmd, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        print("Started EcoRouting process (task ID = %s | cwd = %s | cmd = %s)" % (self.task_id, self.cwd, cmd))
        self.status = TaskStatus.Starting
        self.before()
        self.status = TaskStatus.Running
        try:
            self.mode.run(eco_proc)
        except BaseException as e:
            print("[task ID = %s] ERROR: " % self.task_id, e)
            self.status = TaskStatus.Failed
        self.status = TaskStatus.Completing
        self.after()
        self.status = TaskStatus.Completed
        print("Terminated EcoRouting process (task ID = %s | cwd = %s | cmd = %s)" % (self.task_id, self.cwd, cmd))

    def after(self):
        if self.cwd != os.getcwd():
            utils.clear_and_remove_dir(self.cwd)


class EcoRoutingVideoTask(EcoRoutingTask):
    def __init__(self, task_id, scenario, mode: EcoRoutingMode, video_name: str):
        EcoRoutingTask.__init__(self, task_id, scenario, mode)
        self.video_name = video_name

    def get_display_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def get_cmd(self):
        return EcoRoutingTask.get_cmd(self).append("--gui")

    def before(self):
        EcoRoutingTask.before(self)
        utils.add_snapshots_to_gui_settings(self.cwd)
        utils.ensure_dir_exists(os.path.join(self.cwd, Globals.SNAPSHOTS_DIR))
        geometry = "%dx%d" % (Globals.VIDEOS_RESOLUTION["width"], Globals.VIDEOS_RESOLUTION["height"])
        display = self.env["DISPLAY"]
        os.system("vncserver %s -noxstartup -geometry %s" % (display, geometry))

    def start(self):
        if self.env["DISPLAY"] == ":0":
            print("WARNING: EcoRoutingVideoTask task ID = %s is set for DISPLAY :0" % self.task_id)
        display = self.env["DISPLAY"]
        print("Running EcoRouting process on DISPLAY %s through a VNC server" % display)
        EcoRoutingTask.start(self)

    def after(self):
        path = os.path.join(self.cwd, Globals.SNAPSHOTS_DIR)
        os.system(utils.get_video_cmd(path, self.video_name))
        utils.clear_and_remove_dir(path)
        display = self.env["DISPLAY"]
        os.system("vncserver -kill %s" % display)
        EcoRoutingTask.after(self)


# video_name = utils.format_file_name_base(self.scenario)
class Base(EcoRoutingMode):
    def get_additional_args(self):
        return ["--mode", "1"]

    def run(self, process: SPopen):
        eco_proc = process.start()
        try:
            out = eco_proc.communicate(timeout=Globals.SUMO_MAX_TIMEOUT)
            print(out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                print("EcoRouting Base process exceeded %d seconds, and will be terminated" % Globals.SUMO_MAX_TIMEOUT)
            raise
        finally:
            eco_proc.terminate()


class Pred(EcoRoutingMode):
    def __init__(self, objective1, objective2):
        self.objective1 = objective1
        self.objective2 = objective2

    def get_additional_args(self):
        return ["--mode", "2", "--obj1", self.objective1, "--obj2", self.objective2]

    def run(self, process: SPopen):
        eco_proc = process.start()
        try:
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.SUMO_MAX_TIMEOUT)
            print(out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                print("EcoRouting Pred process exceeded %d seconds, and will be terminated" % Globals.SUMO_MAX_TIMEOUT)
            raise
        finally:
            eco_proc.terminate()


# video_name = utils.format_file_name_sim(self.scenario, self.objective1, self.objective2, self.solution)
class Sim(Pred):
    def __init__(self, objective1, objective2, solution: int):
        Pred.__init__(self, objective1, objective2)
        self.solution = solution

    def run(self, process: SPopen):
        eco_proc = process.start()
        try:
            eco_proc.stdin.write(b"%d\n" % self.solution)
            eco_proc.stdin.flush()
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.SUMO_MAX_TIMEOUT)
            print(out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                print("EcoRouting Sim process exceeded %d seconds, and will be terminated" % Globals.SUMO_MAX_TIMEOUT)
            raise
        finally:
            eco_proc.terminate()


class EcoRoutingTaskManager(TaskManager):
    def get_dependency_tree(self, root: TaskDependency, task_list: list) -> TaskDependency:
        eco_tasks = []
        for task in task_list:
            if isinstance(task, EcoRoutingTask):
                if type(task.mode) in [Base, Pred, Sim]:
                    eco_tasks.append(task)
                else:
                    print_info = (task.mode.__class__.__name__, task.task_id)
                    print("WARNING: Unknown EcoRoutingMode %s for EcoRoutingTask task ID = %s " % print_info)
            else:
                print("WARNING: Task task ID = %s is not a subclass of EcoRoutingTask" % task.task_id)

        while eco_tasks:
            task = eco_tasks.pop(0)
            if type(task) is Base:
                pass
            elif type(task) is Pred:
                pass
            elif type(task) is Sim:
                pass
            else:
                eco_tasks.append(task)

        return root


def get_test_cases():
    return testcases


def check_content() -> Dict[str, EcoRoutingTask]:
    tcs = get_test_cases()
    total_objective_combinations = utils.get_objective_combinations()
    count_combs_total = len(total_objective_combinations)
    simulations_total = 0
    simulations_done = 0
    heatmaps_total = 0
    heatmaps_done = 0
    videos_total = 0
    videos_done = 0
    tasks = {}

    def verbose(value: bool) -> str:
        return "FOUND" if value else "MISSING"

    def exists(path: str) -> bool:
        return os.path.exists(path)

    def join(*paths: str) -> str:
        return os.path.join(*paths)

    print("Checking content...")
    for scenario in tcs:
        tc = tcs[scenario]
        print("Test case: %s (%s)" % (tc["prettyName"], scenario))

        data_dir = tc["ifolder"]
        data_dir_exists = exists(data_dir)
        data_netfile_exists = exists(join(data_dir, tc["netfile"]))
        data_roufile_exists = exists(join(data_dir, tc["roufile"]))
        print_info = (verbose(data_dir_exists), verbose(data_netfile_exists), verbose(data_roufile_exists))
        print("\tDataset directory: %s | Net file: %s | Route file: %s" % print_info)

        res_dir = tc["ofolder"]
        res_dir_exists = exists(res_dir)
        done_objective_combinations = []
        if res_dir_exists:
            for name in os.listdir(res_dir):
                if utils.is_objective_pair(name):
                    done_objective_combinations.append(name)
        res_base_roufile_exists = exists(join(res_dir, "inputdata", tc["bname"]) + "-base.rou.xml")
        simulations_total += 1
        if res_base_roufile_exists:
            simulations_done += 1
        count_combs_done = len(done_objective_combinations)
        count_combs_left = count_combs_total - count_combs_done
        simulations_total += count_combs_left
        heatmaps_total += count_combs_left
        videos_total += count_combs_left
        image_name = "%s.%s" % (utils.format_file_name_base(scenario), Globals.HEATMAPS_FILE_TYPE)
        heatmap_base_exists = exists(join(Globals.HEATMAPS_DIR, image_name))
        heatmaps_total += 1
        if heatmap_base_exists:
            heatmaps_done += 1
        video_name = "%s.%s" % (utils.format_file_name_base(scenario), Globals.VIDEOS_FILE_TYPE)
        video_base_exists = exists(join(Globals.VIDEOS_DIR, video_name))
        videos_total += 1
        if video_base_exists:
            videos_done += 1
        print_info = (verbose(res_dir_exists), verbose(res_base_roufile_exists), verbose(heatmap_base_exists),
                      verbose(video_base_exists), count_combs_done, count_combs_total)
        print("\tResults directory: %s | Base route file: %s | Heatmap file: %s | Video file: %s | "
              "Objective combinations: %d/%d" % print_info)

        # if not res_base_roufile_exists or not heatmap_base_exists or not video_base_exists:
        base_task_name = scenario
        task = EcoRoutingVideoTask(base_task_name, scenario, Base(), video_name)
        if res_base_roufile_exists and video_base_exists:
            # FIXME -> the Completed status should NOT be attributed here; works for now
            task.status = TaskStatus.Completed
        tasks[base_task_name] = task
        # TODO -> heatmap task for the Base case

        for combination in total_objective_combinations:
            # if combination not in done_objective_combinations:
            objective1, objective2 = utils.reverse_format_objective_names(combination)
            pred_task_name = utils.format_scenario_name(scenario, objective1, objective2)
            task = EcoRoutingTask(pred_task_name, scenario, Pred(objective1, objective2))
            if combination in done_objective_combinations:
                # FIXME -> the Completed status should NOT be attributed here; works for now
                task.status = TaskStatus.Completed
            tasks[pred_task_name] = task

        for combination in done_objective_combinations:
            comb_dir = join(res_dir, combination)
            comb_base_eval_exists = exists(join(comb_dir, "base.eval"))
            comb_pred_eval_exists = exists(join(comb_dir, "pred.eval"))
            comb_sim_eval_exists = exists(join(comb_dir, "sim.eval"))
            solutions_total = []
            solutions_done = []
            for name in os.listdir(comb_dir):
                if os.path.isdir(join(comb_dir, name)) and name.startswith("solution"):
                    solutions_total.append(name)
                    if any([file.endswith(".rou.xml") for file in os.listdir(join(comb_dir, name))]):
                        solutions_done.append(name)
            objective1, objective2 = utils.reverse_format_objective_names(combination)
            objective1_pretty = Globals.METRICS[objective1]["pretty"]
            objective2_pretty = Globals.METRICS[objective2]["pretty"]
            combination_pretty = utils.format_objective_names(objective1_pretty, objective2_pretty)
            count_sols_total = len(solutions_total)
            count_sols_done = len(solutions_done)
            print_info = (combination_pretty, combination, verbose(comb_base_eval_exists),
                          verbose(comb_pred_eval_exists), verbose(comb_sim_eval_exists),
                          count_sols_done, count_sols_total)
            print("\t\t%s (%s): Base results file: %s | Pred results file: %s | Sim results file: %s | "
                  "Solutions: %d/%d" % print_info)

            for solution in solutions_total:
                sol_dir = join(comb_dir, solution)
                sol_sim_roufile_exists = exists(join(sol_dir, tc["bname"]) + ".rou.xml")
                simulations_total += 1
                if sol_sim_roufile_exists:
                    simulations_done += 1
                solution_number = int(solution.replace("solution", ""))
                solution_pretty = "Solution %d" % solution_number
                sol_image_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_image_name = "%s.%s" % (sol_image_name, Globals.HEATMAPS_FILE_TYPE)
                sol_heatmap_sim_exists = exists(join(Globals.HEATMAPS_DIR, sol_image_name))
                heatmaps_total += 1
                if sol_heatmap_sim_exists:
                    heatmaps_done += 1
                sol_video_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_video_name = "%s.%s" % (sol_video_name, Globals.VIDEOS_FILE_TYPE)
                sol_video_sim_exists = exists(join(Globals.VIDEOS_DIR, sol_video_name))
                videos_total += 1
                if sol_video_sim_exists:
                    videos_done += 1
                print_info = (solution_pretty, verbose(sol_sim_roufile_exists),
                              verbose(sol_heatmap_sim_exists), verbose(sol_video_sim_exists))
                print("\t\t\t%s: Sim route file: %s | Heatmap file: %s | Video file: %s" % print_info)

                sol_task_name = utils.format_solution_name(scenario, objective1, objective2, solution_number)
                sol_task_mode = Sim(objective1, objective2, solution_number)
                task = EcoRoutingVideoTask(sol_task_name, scenario, sol_task_mode, sol_video_name)
                if sol_sim_roufile_exists and sol_video_sim_exists:
                    # FIXME -> the Completed status should NOT be attributed here; works for now
                    task.status = TaskStatus.Completed
                tasks[sol_task_name] = task
                # TODO -> heatmap task for the Sim case
        print()

    # FIXME: mismatch between simulations_total, heatmaps_total, videos_total and len(tasks) [len(tasks) is larger]
    print_info = (simulations_done, simulations_total, heatmaps_done, heatmaps_total, videos_done, videos_total)
    print("Finished checking content: Simulations done: %d/%d | Heatmaps done: %d/%d | Videos done: %d/%d" % print_info)
    return tasks
