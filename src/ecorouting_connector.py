import os
import shutil
from subprocess import STDOUT, PIPE, TimeoutExpired
from typing import Dict, Callable, List, Tuple

import utils
from globals import Globals
from logger import logger

if not utils.is_module_available("ecorouting"):
    module = utils.import_module(os.path.join(Globals.ECOROUTING_DIR, "testcases.py"), "testcases")
    testcases = getattr(module, "testcases")
else:
    from ecorouting.testcases import testcases
from spopen import SPopen
from task import Task, TaskStatus, TaskManager, TaskDependency, TaskRunMode


class EcoRoutingMode:
    def can_generate_TEMA_data(self):
        raise NotImplementedError

    def get_TEMA_files(self, scenario) -> List[Tuple[str, str]]:
        raise NotImplementedError

    def get_additional_args(self):
        raise NotImplementedError

    def get_output_dir(self, scenario):
        raise NotImplementedError

    def get_net_file(self, scenario) -> Tuple[str, str]:
        tc = get_test_cases()[scenario]
        return (tc["ifolder"], tc["netfile"])

    def get_route_file(self, scenario) -> Tuple[str, str]:
        raise NotImplementedError

    def get_TEMA_route_file(self, scenario):
        raise NotImplementedError

    def run_ecorouting(self, process: SPopen):
        raise NotImplementedError

    def run_eco_indicator(self, process: SPopen):
        eco_ind_proc = process.start()
        try:
            out = eco_ind_proc.communicate(timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.info("TEMA", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("TEMA", "TEMA Eco-Indicator process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            eco_ind_proc.terminate()

    def run_heatmaps(self, process: SPopen):
        eco_ind_proc = process.start()
        try:
            out = eco_ind_proc.communicate(timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.info("TEMA", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("TEMA", "TEMA Heatmaps process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            eco_ind_proc.terminate()


class Base(EcoRoutingMode):
    def can_generate_TEMA_data(self):
        return True

    def get_TEMA_files(self, scenario) -> List[Tuple[str, str]]:
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        file_rou = self.get_route_file(scenario)[1]
        file_route_veh = Globals.TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME
        file_all_veh = Globals.TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME
        file_noise = Globals.TEMA_NOISE_EDGE_DATA_FILE_NAME
        return [
            (file_rou, self.get_TEMA_route_file(scenario)),
            (file_route_veh, utils.convert_base_file_name_to_TEMA_spec(file_route_veh, period, location)),
            (file_all_veh, utils.convert_base_file_name_to_TEMA_spec(file_all_veh, period, location)),
            (file_noise, utils.convert_base_file_name_to_TEMA_spec(file_noise, period, location))
        ]

    def get_additional_args(self):
        return ["--mode", "1"]

    def get_output_dir(self, scenario):
        tc = get_test_cases()[scenario]
        return os.path.join(tc["ofolder"], "inputdata")

    def get_route_file(self, scenario) -> Tuple[str, str]:
        tc = get_test_cases()[scenario]
        return self.get_output_dir(scenario), "%s-base.rou.xml" % tc["bname"]

    def get_TEMA_route_file(self, scenario):
        tc = get_test_cases()[scenario]
        return "Trips%s_baseline.rou.xml" % tc["period"]

    def run_ecorouting(self, process: SPopen):
        eco_proc = process.start()
        try:
            out = eco_proc.communicate(timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.info("EcoRouting", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("EcoRouting", "EcoRouting Base process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            eco_proc.terminate()


class Pred(EcoRoutingMode):
    def __init__(self, objective1, objective2):
        self.objective1 = objective1
        self.objective2 = objective2

    def can_generate_TEMA_data(self):
        return False

    def get_additional_args(self):
        return ["--mode", "2", "--obj1", self.objective1, "--obj2", self.objective2]

    def run_ecorouting(self, process: SPopen):
        eco_proc = process.start()
        try:
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.info("EcoRouting", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("EcoRouting", "EcoRouting Pred process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            eco_proc.terminate()


class Sim(Pred):
    def __init__(self, objective1, objective2, solution: int):
        Pred.__init__(self, objective1, objective2)
        self.solution = solution

    def can_generate_TEMA_data(self):
        return True

    def get_TEMA_files(self, scenario) -> List[Tuple[str, str]]:
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        file_rou = self.get_route_file(scenario)[1]
        file_route_veh = Globals.TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME
        file_all_veh = Globals.TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME
        file_noise = Globals.TEMA_NOISE_EDGE_DATA_FILE_NAME
        return [
            (file_rou, self.get_TEMA_route_file(scenario)),
            (file_route_veh, utils.convert_sim_file_name_to_TEMA_spec(file_route_veh, period, location, self.solution)),
            (file_all_veh, utils.convert_sim_file_name_to_TEMA_spec(file_all_veh, period, location, self.solution)),
            (file_noise, utils.convert_sim_file_name_to_TEMA_spec(file_noise, period, location, self.solution))
        ]

    def get_output_dir(self, scenario):
        tc = get_test_cases()[scenario]
        objectives = utils.format_objective_names(self.objective1, self.objective2)
        return os.path.join(tc["ofolder"], objectives, "solution%d" % self.solution)

    def get_route_file(self, scenario) -> Tuple[str, str]:
        tc = get_test_cases()[scenario]
        return self.get_output_dir(scenario), "%s.rou.xml" % tc["bname"]

    def get_TEMA_route_file(self, scenario):
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        return "%s_%s_%s_solution%d.rou.xml" % (tc["bname"], period, location, self.solution)

    def run_ecorouting(self, process: SPopen):
        eco_proc = process.start()
        try:
            eco_proc.stdin.write(b"%d\n" % self.solution)
            eco_proc.stdin.flush()
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.info("EcoRouting", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("EcoRouting", "EcoRouting Sim process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            eco_proc.terminate()


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
            if self.mode.can_generate_TEMA_data():
                src = os.path.join(get_test_cases()[self.scenario]["ifolder"], Globals.TEMA_ADDITIONAL_FILES_FILE_NAME)
                dst = os.path.join(self.cwd, Globals.ECOROUTING_ADDITIONAL_FILES_FILE_NAME)
                utils.merge_additional_files_content(src, dst, [Globals.SUMO_EDGE_DATA_XML_TAG])

    def start(self):
        if self.cwd == os.getcwd() or self.cwd == Globals.ECOROUTING_DIR:
            logger.warn("EcoRouting", "EcoRoutingTask task ID = %s is set for cwd %s" % (self.task_id, self.cwd))
        cmd = self.get_cmd()
        eco_proc = SPopen(cmd, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        print_info = (self.task_id, self.cwd, cmd)
        logger.info("EcoRouting", "Started EcoRouting process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
        self.status = TaskStatus.Starting
        self.before()
        self.status = TaskStatus.Running
        try:
            self.mode.run_ecorouting(eco_proc)
        except BaseException as e:
            logger.error("EcoRouting", "Error in task ID = %s: %s" % (self.task_id, e))
            self.status = TaskStatus.Failed
        if self.status != TaskStatus.Failed:
            self.status = TaskStatus.Completing
        self.after()
        if self.status != TaskStatus.Failed:
            self.status = TaskStatus.Completed
        print_info = (self.task_id, self.status.value, self.cwd, cmd)
        logger.info("EcoRouting", "Terminated EcoRouting process (task ID = %s | stats = %s | cwd = %s | cmd = %s)" % print_info)

    def after(self):
        if self.cwd != os.getcwd():
            if self.mode.can_generate_TEMA_data():
                out_dir = self.mode.get_output_dir(self.scenario)
                all_veh_edge_data = os.path.join(self.cwd, Globals.TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME)
                if os.path.exists(all_veh_edge_data) and os.path.isfile(all_veh_edge_data):
                    dst = os.path.join(out_dir, Globals.TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME)
                    shutil.copyfile(all_veh_edge_data, dst)
                routing_veh_edge_data = os.path.join(self.cwd, Globals.TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME)
                if os.path.exists(routing_veh_edge_data) and os.path.isfile(routing_veh_edge_data):
                    dst = os.path.join(out_dir, Globals.TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME)
                    shutil.copyfile(routing_veh_edge_data, dst)
                noise_edge_data = os.path.join(self.cwd, Globals.TEMA_NOISE_EDGE_DATA_FILE_NAME)
                if os.path.exists(noise_edge_data) and os.path.isfile(noise_edge_data):
                    dst = os.path.join(out_dir, Globals.TEMA_NOISE_EDGE_DATA_FILE_NAME)
                    shutil.copyfile(noise_edge_data, dst)
            utils.clear_and_remove_dir(self.cwd)


class EcoRoutingVideoTask(EcoRoutingTask):
    def __init__(self, task_id, scenario, mode: EcoRoutingMode, video_name: str):
        EcoRoutingTask.__init__(self, task_id, scenario, mode)
        self.video_name = video_name

    def get_display_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def get_cmd(self):
        return EcoRoutingTask.get_cmd(self) + ["--gui"]

    def before(self):
        EcoRoutingTask.before(self)
        utils.add_snapshots_to_gui_settings(self.cwd)
        utils.ensure_dir_exists(os.path.join(self.cwd, Globals.SNAPSHOTS_DIR))
        geometry = "%dx%d" % (Globals.VIDEOS_RESOLUTION["width"], Globals.VIDEOS_RESOLUTION["height"])
        display = self.env["DISPLAY"]
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        os.system("vncserver %s -noxstartup -geometry %s" % (display, geometry))

    def start(self):
        if self.env["DISPLAY"] == ":0":
            logger.warn("EcoRouting", "EcoRoutingVideoTask task ID = %s is set for DISPLAY :0" % self.task_id)
        display = self.env["DISPLAY"]
        logger.info("EcoRouting", "Running EcoRouting process on DISPLAY %s through a VNC server" % display)
        EcoRoutingTask.start(self)

    def after(self):
        src_path = os.path.join(self.cwd, Globals.SNAPSHOTS_DIR)
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        # os.system(utils.get_video_cmd(src_path, self.video_name))
        dst_path = os.path.join(self.cwd, self.video_name)
        path_to_gztar = shutil.make_archive(dst_path, 'gztar', src_path)
        gztar = path_to_gztar.split(os.sep)[-1]
        shutil.move(path_to_gztar, os.path.join(Globals.VIDEOS_TARGZ_DIR, gztar))
        utils.clear_and_remove_dir(src_path)
        display = self.env["DISPLAY"]
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        os.system("vncserver -kill %s" % display)
        EcoRoutingTask.after(self)


class TEMATask(Task):
    def __init__(self, task_id, scenario, mode: EcoRoutingMode, image_name):
        Task.__init__(self, task_id)
        self.scenario = scenario
        self.mode = mode
        self.image_name = image_name

    def get_cwd_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def get_display_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def before(self):
        if self.cwd != os.getcwd():
            utils.ensure_dir_exists(self.cwd)
            utils.clear_dir(self.cwd)
            utils.copy_dir_contents(Globals.TEMA_DIR, self.cwd)
            net_file_path, net_file = self.mode.get_net_file(self.scenario)
            shutil.copyfile(os.path.join(net_file_path, net_file), os.path.join(self.cwd, net_file))
            for file_src, file_dst in self.mode.get_TEMA_files(self.scenario):
                src_path = os.path.join(self.mode.get_output_dir(self.scenario), file_src)
                dst_path = os.path.join(self.cwd, file_dst)
                shutil.copyfile(src_path, dst_path)

        geometry = "%dx%d" % (Globals.HEATMAPS_RESOLUTION["width"], Globals.HEATMAPS_RESOLUTION["height"])
        display = self.env["DISPLAY"]
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        os.system("vncserver %s -noxstartup -geometry %s" % (display, geometry))

    def start(self):
        if self.env["DISPLAY"] == ":0":
            logger.warn("TEMA", "TEMATask task ID = %s is set for DISPLAY :0" % self.task_id)
        display = self.env["DISPLAY"]
        logger.info("TEMA", "Running TEMA process on DISPLAY %s through a VNC server" % display)
        if self.cwd == os.getcwd() or self.cwd == Globals.ECOROUTING_DIR:
            logger.warn("TEMA", "TEMATask task ID = %s is set for cwd %s" % (self.task_id, self.cwd))
        eco_ind_cmd = ["bash", "run_eco_indicator.sh", Globals.MATLAB_RUNTIME_DIR]
        net_file = self.mode.get_net_file(self.scenario)[1]
        rou_file = self.mode.get_TEMA_route_file(self.scenario)
        traci_port = str(Globals.TEMA_TRACI_BASE_PORT + int(display.replace(":", "")))
        heatmap_cmd = ["bash", "run_heatmaps.sh", Globals.MATLAB_RUNTIME_DIR, net_file, rou_file, traci_port]
        eco_ind_proc = SPopen(eco_ind_cmd, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        heatmap_proc = SPopen(heatmap_cmd, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        logger.info("TEMA", "Started TEMA process (task ID = %s | cwd = %s)" % (self.task_id, self.cwd))
        self.status = TaskStatus.Starting
        self.before()
        self.status = TaskStatus.Running
        try:
            print_info = (self.task_id, self.cwd, eco_ind_cmd)
            logger.info("TEMA", "Started TEMA Eco-Indicator process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
            self.mode.run_eco_indicator(eco_ind_proc)
            logger.info("TEMA", "Terminated TEMA Eco-Indicator process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
            print_info = (self.task_id, self.cwd, heatmap_cmd)
            logger.info("TEMA", "Started TEMA Heatmaps process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
            self.mode.run_heatmaps(heatmap_proc)
            logger.info("TEMA", "Terminated TEMA Heatmaps process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
        except BaseException as e:
            logger.error("TEMA", "Error in task ID = %s: %s" % (self.task_id, e))
            self.status = TaskStatus.Failed
        if self.status != TaskStatus.Failed:
            self.status = TaskStatus.Completing
        self.after()
        if self.status != TaskStatus.Failed:
            self.status = TaskStatus.Completed
        print_info = (self.task_id, self.status.value, self.cwd)
        logger.info("TEMA", "Terminated TEMA process (task ID = %s | status = %s | cwd = %s)" % print_info)

    def after(self):
        display = self.env["DISPLAY"]
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        os.system("vncserver -kill %s" % display)
        if self.cwd != os.getcwd():
            path_dst = os.path.join(Globals.HEATMAPS_DIR, self.image_name)
            utils.ensure_dir_exists(path_dst)
            for file in os.listdir(self.cwd):
                if file.endswith(Globals.HEATMAPS_FILE_TYPE):
                    shutil.move(os.path.join(self.cwd, file), os.path.join(path_dst, file))
            utils.clear_and_remove_dir(self.cwd)


class EcoRoutingTaskManager(TaskManager):
    def get_dependency_tree(self, root: TaskDependency, task_list: List[Task]) -> TaskDependency:
        base_tasks = []
        base_heatmap_tasks = []
        pred_tasks = []
        sim_tasks = []
        sim_heatmap_tasks = []
        for task in task_list:
            if isinstance(task, EcoRoutingTask):
                if type(task.mode) is Base:
                    base_tasks.append(task)
                elif type(task.mode) is Pred:
                    pred_tasks.append(task)
                elif type(task.mode) is Sim:
                    sim_tasks.append(task)
                else:
                    print_info = (task.mode.__class__.__name__, task.task_id)
                    logger.warn("TaskManager", "Unknown EcoRoutingMode %s for EcoRoutingTask task ID = %s " % print_info)
            elif isinstance(task, TEMATask):
                if type(task.mode) is Base:
                    base_heatmap_tasks.append(task)
                elif type(task.mode) is Sim:
                    sim_heatmap_tasks.append(task)
                else:
                    print_info = (task.mode.__class__.__name__, task.task_id)
                    logger.warn("TaskManager", "Unknown EcoRoutingMode %s for TEMATask task ID = %s " % print_info)
            else:
                print_info = (task.__class__.__name__, task.task_id)
                logger.warn("TaskManager", "Task %s task ID = %s is not an acceptable subclass of Task" % print_info)

        def find_matching_task_dep(dep_tree: TaskDependency, condition: Callable[[TaskDependency], bool]):
            res = None
            if condition(dep_tree):
                res = dep_tree
            else:
                for child in dep_tree.children:
                    res = find_matching_task_dep(child, condition)
                    if res:
                        break
            return res

        def find_all_matching_task_deps(dep_tree: TaskDependency, condition: Callable[[TaskDependency], bool]):
            res = []
            if condition(dep_tree):
                res.append(dep_tree)
            for child in dep_tree.children:
                res.extend(find_all_matching_task_deps(child, condition))
            return res

        for base_task in base_tasks:
            base_task_dep = TaskDependency(base_task)
            root.add_child(base_task_dep)

        for base_heatmap_task in base_heatmap_tasks:
            base_heatmap_task_dep = TaskDependency(base_heatmap_task)

            def f_base_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask) and isinstance(dep.task.mode, Base):
                    return dep.task.scenario == base_heatmap_task.scenario
                return False

            parent_base_task_dep = find_matching_task_dep(root, f_base_parent)
            if parent_base_task_dep:
                parent_base_task_dep.add_child(base_heatmap_task_dep)
            else:
                root.add_child(base_heatmap_task_dep)

        for pred_task in pred_tasks:
            pred_task_dep = TaskDependency(pred_task)

            def f_base_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask) and isinstance(dep.task.mode, Base):
                    return dep.task.scenario == pred_task.scenario
                return False

            parent_base_task_dep = find_matching_task_dep(root, f_base_parent)
            if parent_base_task_dep:
                parent_base_task_dep.add_child(pred_task_dep)
            else:
                root.add_child(pred_task_dep)

        for sim_task in sim_tasks:
            sim_task_dep = TaskDependency(sim_task)

            def f_sim_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask):
                    if isinstance(dep.task.mode, Sim) and isinstance(sim_task.mode, Sim):
                        return dep.task.scenario == sim_task.scenario and \
                               dep.task.mode.objective1 == sim_task.mode.objective1 and \
                               dep.task.mode.objective2 == sim_task.mode.objective2 and \
                               dep.task.mode.solution != sim_task.mode.solution
                return False

            def f_pred_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask):
                    if isinstance(dep.task.mode, Pred) and isinstance(sim_task.mode, Sim):
                        return dep.task.scenario == sim_task.scenario and \
                               dep.task.mode.objective1 == sim_task.mode.objective1 and \
                               dep.task.mode.objective2 == sim_task.mode.objective2
                return False

            parent_sim_task_deps = find_all_matching_task_deps(root, f_sim_parent)
            parent_pred_task_dep = find_matching_task_dep(root, f_pred_parent)
            if parent_sim_task_deps:
                parent_sim_task_deps[-1].add_child(sim_task_dep)
            elif parent_pred_task_dep:
                parent_pred_task_dep.add_child(sim_task_dep)
            else:
                root.add_child(sim_task_dep)

        for sim_heatmap_task in sim_heatmap_tasks:
            sim_heatmap_task_dep = TaskDependency(sim_heatmap_task)

            def f_sim_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask):
                    if isinstance(dep.task.mode, Sim) and isinstance(sim_heatmap_task.mode, Sim):
                        return dep.task.scenario == sim_heatmap_task.scenario and \
                               dep.task.mode.objective1 == sim_heatmap_task.mode.objective1 and \
                               dep.task.mode.objective2 == sim_heatmap_task.mode.objective2 and \
                               dep.task.mode.solution == sim_heatmap_task.mode.solution
                return False

            parent_sim_task_dep = find_matching_task_dep(root, f_sim_parent)
            if parent_sim_task_dep:
                parent_sim_task_dep.add_child(sim_heatmap_task_dep)
            else:
                root.add_child(sim_heatmap_task_dep)

        return root


def get_test_cases():
    excluded = ["ang-est", "portoSB_8AM9AM_fewerv", "portoA3_6PM7PM"]
    return {k: v for k, v in testcases.items() if k not in excluded}


def check_content(silent=True) -> Dict[str, Task]:
    tcs = get_test_cases()
    total_objective_combinations = utils.get_objective_combinations()
    count_combs_total = len(total_objective_combinations)
    tasks: Dict[str, Task] = {}

    def verbose(value: bool) -> str:
        return "FOUND" if value else "MISSING"

    def exists(path: str) -> bool:
        return os.path.exists(path)

    def join(*paths: str) -> str:
        return os.path.join(*paths)

    if not silent:
        logger.info("ContentChecker", "Checking content...")
    for scenario in tcs:
        tc = tcs[scenario]
        if not silent:
            logger.info("ContentChecker", "Test case: %s (%s)" % (tc["prettyName"], scenario))

        data_dir = tc["ifolder"]
        data_dir_exists = exists(data_dir)
        data_netfile_exists = exists(join(data_dir, tc["netfile"]))
        data_roufile_exists = exists(join(data_dir, tc["roufile"]))
        print_info = (verbose(data_dir_exists), verbose(data_netfile_exists), verbose(data_roufile_exists))
        if not silent:
            logger.info("ContentChecker", "\tDataset directory: %s | Net file: %s | Route file: %s" % print_info)

        res_dir = tc["ofolder"]
        res_dir_exists = exists(res_dir)
        done_objective_combinations = []
        if res_dir_exists:
            for name in os.listdir(res_dir):
                if utils.is_objective_pair(name):
                    done_objective_combinations.append(name)
        res_base_roufile_exists = exists(join(res_dir, "inputdata", tc["bname"]) + "-base.rou.xml")
        count_combs_done = len(done_objective_combinations)
        image_name = "%s.%s" % (utils.format_file_name_base(scenario), Globals.HEATMAPS_FILE_TYPE)
        heatmap_base_exists = exists(join(Globals.HEATMAPS_DIR, image_name))
        video_name = utils.format_file_name_base(scenario)
        video_extension = ".%s" % Globals.VIDEOS_FILE_TYPE
        video_targz_extension = ".%s" % Globals.VIDEOS_TARGZ_FILE_TYPE
        video_base_exists = exists(join(Globals.VIDEOS_DIR, video_name + video_extension)) or \
                            exists(join(Globals.VIDEOS_TARGZ_DIR, video_name + video_targz_extension))
        print_info = (verbose(res_dir_exists), verbose(res_base_roufile_exists), verbose(heatmap_base_exists),
                      verbose(video_base_exists), count_combs_done, count_combs_total)
        if not silent:
            logger.info("ContentChecker", "\tResults directory: %s | Base route file: %s | Heatmap file: %s | "
                                          "Video file: %s | Objective combinations: %d/%d" % print_info)

        base_task_name = scenario
        base_task_mode = Base()
        base_task = EcoRoutingVideoTask(base_task_name, scenario, base_task_mode, video_name)
        if res_base_roufile_exists and video_base_exists:
            # FIXME -> the Completed status should NOT be attributed here; works for now
            base_task.status = TaskStatus.Completed
        tasks[base_task_name] = base_task
        base_heatmap_task_name = "%s_heatmap" % base_task_name
        base_task_heatmap = TEMATask(base_heatmap_task_name, scenario, base_task_mode, "")
        if heatmap_base_exists:
            # FIXME -> the Completed status should NOT be attributed here; works for now
            base_task_heatmap.status = TaskStatus.Completed
        # tasks[base_heatmap_task_name] = base_task_heatmap

        for combination in total_objective_combinations:
            objective1, objective2 = utils.reverse_format_objective_names(combination)
            pred_task_name = utils.format_scenario_name(scenario, objective1, objective2)
            pred_task = EcoRoutingTask(pred_task_name, scenario, Pred(objective1, objective2))
            if combination in done_objective_combinations:
                # FIXME -> the Completed status should NOT be attributed here; works for now
                pred_task.status = TaskStatus.Completed
            tasks[pred_task_name] = pred_task

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
            if not silent:
                logger.info("ContentChecker", "\t\t%s (%s): Base results file: %s | Pred results file: %s | "
                                              "Sim results file: %s | Solutions: %d/%d" % print_info)

            for solution in solutions_total:
                sol_dir = join(comb_dir, solution)
                sol_sim_roufile_exists = exists(join(sol_dir, tc["bname"]) + ".rou.xml")
                solution_number = int(solution.replace("solution", ""))
                solution_pretty = "Solution %d" % solution_number
                sol_image_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_image_name = "%s.%s" % (sol_image_name, Globals.HEATMAPS_FILE_TYPE)
                sol_heatmap_sim_exists = exists(join(Globals.HEATMAPS_DIR, sol_image_name))
                sol_video_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                video_extension = ".%s" % Globals.VIDEOS_FILE_TYPE
                video_targz_extension = ".%s" % Globals.VIDEOS_TARGZ_FILE_TYPE
                sol_video_sim_exists = exists(join(Globals.VIDEOS_DIR, sol_video_name + video_extension)) or \
                                       exists(join(Globals.VIDEOS_TARGZ_DIR, sol_video_name + video_targz_extension))
                print_info = (solution_pretty, verbose(sol_sim_roufile_exists),
                              verbose(sol_heatmap_sim_exists), verbose(sol_video_sim_exists))
                if not silent:
                    logger.info("ContentChecker", "\t\t\t%s: Sim route file: %s | Heatmap file: %s | "
                                                  "Video file: %s" % print_info)

                sol_task_name = utils.format_solution_name(scenario, objective1, objective2, solution_number)
                sol_task_mode = Sim(objective1, objective2, solution_number)
                sol_task = EcoRoutingVideoTask(sol_task_name, scenario, sol_task_mode, sol_video_name)
                if sol_sim_roufile_exists and sol_video_sim_exists:
                    # FIXME -> the Completed status should NOT be attributed here; works for now
                    sol_task.status = TaskStatus.Completed
                tasks[sol_task_name] = sol_task
                sol_heatmap_task_name = "%s_heatmap" % sol_task_name
                sol_task_heatmap = TEMATask(sol_heatmap_task_name, scenario, sol_task_mode, "")
                if sol_heatmap_sim_exists:
                    # FIXME -> the Completed status should NOT be attributed here; works for now
                    sol_task_heatmap.status = TaskStatus.Completed
                # tasks[sol_heatmap_task_name] = sol_task_heatmap

    completed_tasks = sum([v.status == TaskStatus.Completed for k, v in tasks.items()])
    if not silent:
        logger.info("ContentChecker", "Finished checking content: "
                                      "Completed tasks: %d/%d" % (completed_tasks, len(tasks)))
    return tasks
