import os
import shutil
import subprocess

import utils
from ecorouting.testcases import testcases
from globals import Globals


def get_test_cases():
    return testcases


def check_content():
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
        image_name = utils.format_file_name_base(scenario)
        heatmap_base_exists = exists(join(Globals.HEATMAPS_DIR, image_name, Globals.HEATMAPS_FILE_TYPE))
        heatmaps_total += 1
        if heatmap_base_exists:
            heatmaps_done += 1
        video_name = utils.format_file_name_base(scenario)
        video_base_exists = exists(join(Globals.VIDEOS_DIR, video_name, Globals.VIDEOS_FILE_TYPE))
        videos_total += 1
        if video_base_exists:
            videos_done += 1
        print_info = (verbose(res_dir_exists), verbose(res_base_roufile_exists), verbose(heatmap_base_exists),
                      verbose(video_base_exists), count_combs_done, count_combs_total)
        print("\tResults directory: %s | Base route file: %s | Heatmap file: %s | Video file: %s | "
              "Objective combinations: %d/%d" % print_info)

        task_name = utils.format_file_name_base(scenario)
        tasks[task_name] = Base(scenario, not heatmap_base_exists, not video_base_exists)

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

            # sol_task_name = utils.format_scenario_name(scenario, objective1, objective2)
            # tasks[sol_task_name] = Sim(scenario, objective1, objective2,, not he

            for solution in solutions_total:
                sol_dir = join(comb_dir, solution)
                sol_sim_roufile_exists = exists(join(sol_dir, tc["bname"]) + ".rou.xml")
                simulations_total += 1
                if sol_sim_roufile_exists:
                    simulations_done += 1
                solution_number = int(solution.replace("solution", ""))
                solution_pretty = "Solution %d" % solution_number
                sol_image_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_heatmap_sim_exists = exists(join(Globals.HEATMAPS_DIR, sol_image_name, Globals.HEATMAPS_FILE_TYPE))
                heatmaps_total += 1
                if sol_heatmap_sim_exists:
                    heatmaps_done += 1
                sol_video_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_video_sim_exists = exists(join(Globals.VIDEOS_DIR, sol_video_name, Globals.VIDEOS_FILE_TYPE))
                videos_total += 1
                if sol_video_sim_exists:
                    videos_done += 1
                print_info = (solution_pretty, verbose(sol_sim_roufile_exists),
                              verbose(sol_heatmap_sim_exists), verbose(sol_video_sim_exists))
                print("\t\t\t%s: Sim route file: %s | Heatmap file: %s | Video file: %s" % print_info)

        print()
    print_info = (simulations_done, simulations_total, heatmaps_done, heatmaps_total, videos_done, videos_total)
    print("Finished checking content: Simulations done: %d/%d | Heatmaps done: %d/%d | Videos done: %d/%d" % print_info)


class EcoRoutingTask:
    gui_settings_original = os.path.join(Globals.ECOROUTING_DIR, "gui-settings.xml")
    gui_settings_backup = os.path.join(Globals.ECOROUTING_DIR, "gui-settings.xml.BAK")

    def __init__(self, scenario, heatmap, video):
        self.scenario = scenario
        self.heatmap = heatmap
        self.video = video

    def get_args(self):
        raise NotImplementedError

    # code to run before calling the EcoRouting process
    def setup(self):
        if self.heatmap:
            pass
        if self.video:
            os.system("vncserver :1 -noxstartup -geometry 400x300")     # 1280x960")
            if os.path.exists(EcoRoutingTask.gui_settings_backup):
                if os.path.exists(EcoRoutingTask.gui_settings_original):
                    os.remove(EcoRoutingTask.gui_settings_original)
                os.rename(EcoRoutingTask.gui_settings_backup, EcoRoutingTask.gui_settings_original)

            shutil.copyfile(EcoRoutingTask.gui_settings_original, EcoRoutingTask.gui_settings_backup)
            utils.ensure_dir_exists(Globals.SNAPSHOTS_DIR)
            utils.clear_dir(Globals.SNAPSHOTS_DIR)
            snapshots_dir_abs = os.path.abspath(Globals.SNAPSHOTS_DIR)
            snapshot_name = os.path.join(snapshots_dir_abs, Globals.SNAPSHOTS_NAME)
            snapshot_xml = '\t<snapshot file="%s" time="%d"/>'
            snapshot_str = "\n".join([snapshot_xml % (snapshot_name % i, i) for i in range(Globals.SNAPSHOTS_COUNT)])

            with open(EcoRoutingTask.gui_settings_original, "r") as f:
                content = f.read()

            content = content.replace("</viewsettings>", "%s\n</viewsettings>" % snapshot_str)

            with open(EcoRoutingTask.gui_settings_original, "w") as f:
                f.write(content)

            del content

    def run(self):
        cmd = "python main-interactive.py -t %s %s" % (self.scenario, self.get_args())
        env = os.environ.copy()
        if self.heatmap:
            pass
        if self.video:
            cmd += " --gui"
            env["DISPLAY"] = ":1"
        eco_proc = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, cwd=Globals.ECOROUTING_DIR, env=env)
        try:
            print("Starting EcoRouting process (cmd = %s)" % cmd)
            self._run(eco_proc)
            # eco_proc.communicate(timeout=30)  # Globals.SUMO_MAX_TIMEOUT)
        except BaseException as e:
            if isinstance(e, subprocess.TimeoutExpired):
                print_info = (Globals.SUMO_MAX_TIMEOUT, cmd)
                print("Current EcoRouting process exceeded %d seconds, and will be terminated (cmd = %s)" % print_info)
            else:
                print("ERROR: ", e)
        finally:
            eco_proc.terminate()
            print("EcoRouting process terminated")

    def _run(self, eco_proc: subprocess.Popen):
        raise NotImplementedError

    # code to run before a simulation starts
    def before_simulation(self):
        if self.heatmap:
            pass
        if self.video:
            utils.ensure_dir_exists(Globals.SNAPSHOTS_DIR)
            utils.clear_dir(Globals.SNAPSHOTS_DIR)

    # code to run after a simulation finishes
    def after_simulation(self, file_name=None):
        if self.heatmap and file_name:
            pass
        if self.video and file_name:
            os.system(utils.get_video_cmd(file_name))

    # code to run after the EcoRouting process terminates
    def teardown(self):
        if self.heatmap:
            pass
        if self.video:
            os.system("vncserver -kill :1")
            utils.clear_and_remove_dir(Globals.SNAPSHOTS_DIR)
            os.remove(EcoRoutingTask.gui_settings_original)
            os.rename(EcoRoutingTask.gui_settings_backup, EcoRoutingTask.gui_settings_original)


class Base(EcoRoutingTask):
    def __init__(self, scenario, heatmap, video):
        EcoRoutingTask.__init__(self, scenario, heatmap, video)

    def get_args(self):
        return "--mode 1"

    def _run(self, eco_proc: subprocess.Popen):
        # because here the process has already been started, it might not be safe to call
        # this function as it clears the contents of SNAPSHOTS_DIR
        # (this is only useful for the Sim mode, because multiple simulations are run
        # whereas only one is run in the Base mode, and SNAPSHOTS_DIR is already created
        # and cleared by the setup() function)
        # self.before_simulation()
        line = " "
        while line:
            line = eco_proc.stdout.readline().decode().rstrip()
            print(line)
        try:
            eco_proc.communicate()
        except:
            pass
        self.after_simulation(utils.format_file_name_base(self.scenario))


# IMPORTANT NOTE
# This is quite a weak solution, but it is the only way to fully integrate the EcoRouting module with the
# rest of the MobiWise system, and it is entirely dependent on line 106 of main-interactive.py
#
#   106     sel = int(input("Enter solution number or -1 to exit\n"))
#
# If the parameter of the input() function is changed, this solution is no longer valid, and the thread
# calling eco_proc.stdout.readline() WILL BLOCK indefinitely (i.e., deadlock)
class Sim(EcoRoutingTask):
    ecorouting_input_str = "Enter solution number or -1 to exit"

    def __init__(self, scenario, objective1, objective2, solutions, heatmap, video):
        EcoRoutingTask.__init__(self, scenario, heatmap, video)
        self.objective1 = objective1
        self.objective2 = objective2
        self.solutions = solutions

    def get_args(self):
        return "--mode 2 --obj1 %s --obj2 %s" % (self.objective1, self.objective2)

    def _run(self, eco_proc: subprocess.Popen):
        self.read_until_line(eco_proc.stdout, Sim.ecorouting_input_str)
        for sol in self.solutions:
            self.before_simulation()
            self.write_to_fd(eco_proc.stdin, "%d" % sol)
            self.read_until_line(eco_proc.stdout, Sim.ecorouting_input_str)
            self.after_simulation(utils.format_file_name_sim(self.scenario, self.objective1, self.objective2, sol))
        # self.read_until_line(eco_proc.stdout, Sim.ecorouting_input_str)
        self.write_to_fd(eco_proc.stdin, "-1")

    # reads the STDOUT of a given file descriptor until a given line is found
    # returns a list with each of the lines read
    @staticmethod
    def read_until_line(fd, line):
        out = ""
        lines = []
        while line not in out:
            out = fd.readline().decode().rstrip()
            lines.append(out)
            print(out)
        return lines

    # writes a line to a given STDIN file descriptor, in either byte or string modes
    @staticmethod
    def write_to_fd(fd, line, byte=True):
        s = "%s\n" % line
        fd.write(s.encode() if byte else s)
        fd.flush()


def call_ecorouting(ecorouting_task: EcoRoutingTask):
    ecorouting_task.setup()
    ecorouting_task.run()
    ecorouting_task.teardown()
