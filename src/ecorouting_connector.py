import os
from subprocess import STDOUT, PIPE, TimeoutExpired

import utils
from ecorouting.testcases import testcases
from globals import Globals
from spopen import SPopen
from task import Task, RunMode


class EcoRoutingTask(Task):
    def __init__(self, scenario):
        Task.__init__(self)
        self.cwd = Globals.ECOROUTING_DIR
        self.scenario = scenario

    def get_run_mode(self) -> RunMode:
        raise NotImplementedError

    def get_additional_args(self):
        raise NotImplementedError

    def needs_heatmap_config(self):
        raise NotImplementedError

    def needs_video_config(self):
        raise NotImplementedError

    def get_cmd(self):
        cmd = "python main-interactive.py -t %s %s" % (self.scenario, self.get_additional_args())
        if self.needs_heatmap_config():
            pass
        if self.needs_video_config():
            cmd += " --gui"
        return cmd

    def before_simulation(self, heatmap, video):
        if self.cwd != os.getcwd():
            utils.ensure_dir_exists(self.cwd)
            utils.clear_dir(self.cwd)
            utils.copy_dir_contents(Globals.ECOROUTING_DIR, self.cwd)

        if heatmap:
            pass
        if video:
            utils.add_snapshots_to_gui_settings(self.cwd)
            utils.ensure_dir_exists(os.path.join(self.cwd, Globals.SNAPSHOTS_DIR))
            geometry = "%dx%d" % (Globals.VIDEOS_RESOLUTION["width"], Globals.VIDEOS_RESOLUTION["height"])
            display = self.env["DISPLAY"]
            os.system("vncserver %s -noxstartup -geometry %s" % (display, geometry))

    def run(self, process: SPopen):
        raise NotImplementedError

    def start(self):
        cmd = self.get_cmd()
        cmd_array = cmd.split(" ")
        eco_proc = SPopen(cmd_array, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        display = self.env["DISPLAY"]
        print("Started EcoRouting process (display = %s | cwd = %s | cmd = %s)" % (display, self.cwd, cmd))
        self.run(eco_proc)
        print("Terminated EcoRouting process (display = %s | cwd = %s | cmd = %s)" % (display, self.cwd, cmd))

    def after_simulation(self, heatmap, video, file_name=None):
        if heatmap and file_name:
            pass
        if video and file_name:
            path = os.path.join(self.cwd, Globals.SNAPSHOTS_DIR)
            os.system(utils.get_video_cmd(path, file_name))
            utils.clear_and_remove_dir(path)
            display = self.env["DISPLAY"]
            os.system("vncserver -kill %s" % display)

        if self.cwd != os.getcwd():
            utils.clear_and_remove_dir(self.cwd)


class Base(EcoRoutingTask):
    def __init__(self, scenario, heatmap: bool, video: bool):
        EcoRoutingTask.__init__(self, scenario)
        self.heatmap = heatmap
        self.video = video

    def get_run_mode(self) -> RunMode:
        return RunMode.IsolatedParallel

    def get_additional_args(self):
        return "--mode 1"

    def needs_heatmap_config(self):
        return self.heatmap

    def needs_video_config(self):
        return self.video

    def run(self, process: SPopen):
        self.before_simulation(self.heatmap, self.video)
        eco_proc = process.start()
        try:
            out = eco_proc.communicate(timeout=Globals.SUMO_MAX_TIMEOUT)
            print(out[0].decode().rstrip())
            file_name = utils.format_file_name_base(self.scenario)
            self.after_simulation(self.heatmap, self.video, file_name)
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                print("EcoRouting process exceeded %d seconds, and will be terminated" % Globals.SUMO_MAX_TIMEOUT)
            else:
                print("ERROR: ", e)
        finally:
            eco_proc.terminate()


class Pred(EcoRoutingTask):
    def __init__(self, scenario, objective1, objective2):
        EcoRoutingTask.__init__(self, scenario)
        self.objective1 = objective1
        self.objective2 = objective2

    def get_run_mode(self) -> RunMode:
        return RunMode.Parallel

    def get_additional_args(self):
        return "--mode 2 --obj1 %s --obj2 %s" % (self.objective1, self.objective2)

    def needs_heatmap_config(self):
        return False

    def needs_video_config(self):
        return False

    def run(self, process: SPopen):
        eco_proc = process.start()
        try:
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.SUMO_MAX_TIMEOUT)
            print(out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                print("EcoRouting process exceeded %d seconds, and will be terminated" % Globals.SUMO_MAX_TIMEOUT)
            else:
                print("ERROR: ", e)
        finally:
            eco_proc.terminate()


class Sim(Pred):
    def __init__(self, scenario, objective1, objective2, solution: int, heatmap: bool, video: bool):
        Pred.__init__(self, scenario, objective1, objective2)
        self.solution = solution
        self.heatmap = heatmap
        self.video = video

    def get_run_mode(self) -> RunMode:
        return RunMode.IsolatedParallel

    def needs_heatmap_config(self):
        return self.heatmap

    def needs_video_config(self):
        return self.video

    def run(self, process: SPopen):
        self.before_simulation(self.heatmap, self.video)
        eco_proc = process.start()
        try:
            eco_proc.stdin.write(b"%d\n" % self.solution)
            eco_proc.stdin.flush()
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.SUMO_MAX_TIMEOUT)
            print(out[0].decode().rstrip())
            file_name = utils.format_file_name_sim(self.scenario, self.objective1, self.objective2, self.solution)
            self.after_simulation(self.heatmap, self.video, file_name)
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                print("EcoRouting process exceeded %d seconds, and will be terminated" % Globals.SUMO_MAX_TIMEOUT)
            else:
                print("ERROR: ", e)
        finally:
            eco_proc.terminate()


class EcoRoutingTaskManager:
    class TaskObj:
        def __init__(self, name, task: Task):
            self.name = name
            self.task = task

    def __init__(self):
        self.tasks = {}

    def add_task(self, name, task: Task, sequence_name=""):
        if sequence_name not in self.tasks:
            self.tasks[sequence_name] = []
        self.tasks[sequence_name].append(EcoRoutingTaskManager.TaskObj(name, task))

    def run_tasks(self):
        pass


def get_test_cases():
    return testcases


def check_content() -> EcoRoutingTaskManager:
    tcs = get_test_cases()
    total_objective_combinations = utils.get_objective_combinations()
    count_combs_total = len(total_objective_combinations)
    simulations_total = 0
    simulations_done = 0
    heatmaps_total = 0
    heatmaps_done = 0
    videos_total = 0
    videos_done = 0
    task_manager = EcoRoutingTaskManager()

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

        if not res_base_roufile_exists or not heatmap_base_exists or not video_base_exists:
            base_task_name = utils.format_file_name_base(scenario)
            task = Base(scenario, not heatmap_base_exists, not video_base_exists)
            task_manager.add_task(base_task_name, task)
            continue

        for combination in total_objective_combinations:
            if combination not in done_objective_combinations:
                objective1, objective2 = utils.reverse_format_objective_names(combination)
                pred_task_name = utils.format_scenario_name(scenario, objective1, objective2)
                task = Pred(scenario, objective1, objective2)
                task_manager.add_task(pred_task_name, task)

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

            sol_status = {}
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

                sol_status[solution_number] = {"roufile_exists": sol_sim_roufile_exists,
                                               "heatmap_exists": sol_heatmap_sim_exists,
                                               "video_exists": sol_video_sim_exists}

            if sol_status:
                solutions = []
                heatmaps = []
                videos = []
                for sol in sol_status:
                    roufile_exists = sol_status[sol]["roufile_exists"]
                    heatmap_exists = sol_status[sol]["heatmap_exists"]
                    video_exists = sol_status[sol]["video_exists"]
                    if not roufile_exists or not heatmap_exists or not video_exists:
                        solutions.append(sol)
                        heatmaps.append(not heatmap_exists)
                        videos.append(not video_exists)
                if solutions and heatmaps and videos:
                    sol_task_name = utils.format_scenario_name(scenario, objective1, objective2)
                    task = Sim(scenario, objective1, objective2, solutions, heatmaps, videos)
                    task_manager.add_task(sol_task_name, task)

        print()
    print_info = (simulations_done, simulations_total, heatmaps_done, heatmaps_total, videos_done, videos_total)
    print("Finished checking content: Simulations done: %d/%d | Heatmaps done: %d/%d | Videos done: %d/%d" % print_info)
    return task_manager
