import os
import shutil
import threading
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


file_copy_lock = threading.RLock()


class EcoRoutingMode:
    TEMA_lock = threading.RLock()

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

    def get_TEMA_route_file(self, scenario):
        raise NotImplementedError

    def get_TEMA_res_file(self, scenario):
        raise NotImplementedError

    def run_ecorouting(self, process: SPopen):
        # TODO: Detect return code from Popen process, and if it is not 0 the task MUST be considered as status = Failed
        #       If the task has failed, additionally, the EcoRouting output directory MUST be removed
        raise NotImplementedError

    def run_eco_indicator(self, process: SPopen):
        logger.debug("TEMA", "[Eco-Indicator] starting Popen process")
        with EcoRoutingMode.TEMA_lock:
            eco_ind_proc = process.start()
        logger.debug("TEMA", "[Eco-Indicator] started Popen process")
        try:
            logger.debug("TEMA", "[Eco-Indicator] waiting for eco_ind_proc.communicate()")
            out = eco_ind_proc.communicate(timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.debug("TEMA", "[Eco-Indicator] eco_ind_proc.communicate() finished")
            logger.info("TEMA", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("TEMA", "TEMA Eco-Indicator process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            logger.debug("TEMA", "[Eco-Indicator] terminating Popen process")
            eco_ind_proc.terminate()
            logger.debug("TEMA", "[Eco-Indicator] terminated Popen process")

    def run_heatmaps(self, process: SPopen):
        logger.debug("TEMA", "[Heatmaps] starting Popen process")
        with EcoRoutingMode.TEMA_lock:
            heatmaps_proc = process.start()
        logger.debug("TEMA", "[Heatmaps] started Popen process")
        try:
            logger.debug("TEMA", "[Heatmaps] waiting for heatmaps_proc.communicate()")
            out = heatmaps_proc.communicate(timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.debug("TEMA", "[Heatmaps] heatmaps_proc.communicate() finished")
            logger.info("TEMA", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("TEMA", "TEMA Heatmaps process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            logger.debug("TEMA", "[Heatmaps] terminating Popen process")
            heatmaps_proc.terminate()
            logger.debug("TEMA", "[Heatmaps] terminated Popen process")


class Base(EcoRoutingMode):
    def can_generate_TEMA_data(self):
        return True

    def get_TEMA_files(self, scenario) -> List[Tuple[str, str]]:
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        file_rou = "%s-base.rou.xml" % tc["bname"]
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

    def get_TEMA_route_file(self, scenario):
        tc = get_test_cases()[scenario]
        return utils.get_base_route_file_name_per_TEMA_spec(tc["period"])

    def get_TEMA_res_file(self, scenario):
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        return utils.get_base_res_file_name_per_TEMA_spec(period, location)

    def run_ecorouting(self, process: SPopen):
        logger.debug("EcoRouting", "[Base] starting Popen process")
        eco_proc = process.start()
        logger.debug("EcoRouting", "[Base] started Popen process")
        try:
            logger.debug("EcoRouting", "[Base] waiting for eco_proc.communicate()")
            out = eco_proc.communicate(timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.debug("EcoRouting", "[Base] eco_proc.communicate() finished")
            logger.info("EcoRouting", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("EcoRouting", "EcoRouting Base process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            logger.debug("EcoRouting", "[Base] terminating Popen process")
            eco_proc.terminate()
            logger.debug("EcoRouting", "[Base] terminated Popen process")


class Pred(EcoRoutingMode):
    def __init__(self, objective1, objective2):
        self.objective1 = objective1
        self.objective2 = objective2

    def can_generate_TEMA_data(self):
        return False

    def get_additional_args(self):
        return ["--mode", "2", "--obj1", self.objective1, "--obj2", self.objective2]

    def run_ecorouting(self, process: SPopen):
        logger.debug("EcoRouting", "[Pred] starting Popen process")
        eco_proc = process.start()
        logger.debug("EcoRouting", "[Pred] started Popen process")
        try:
            logger.debug("EcoRouting", "[Pred] waiting for eco_proc.communicate(-1)")
            out = eco_proc.communicate(input=b"-1\n", timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.debug("EcoRouting", "[Pred] eco_proc.communicate(-1) finished")
            logger.info("EcoRouting", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("EcoRouting", "EcoRouting Pred process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            logger.debug("EcoRouting", "[Pred] terminating Popen process")
            eco_proc.terminate()
            logger.debug("EcoRouting", "[Pred] terminated Popen process")


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
        file_rou = "%s.rou.xml" % tc["bname"]
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

    def get_TEMA_route_file(self, scenario):
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        return utils.get_sim_route_file_name_per_TEMA_spec(tc["bname"], period, location, self.solution)

    def get_TEMA_res_file(self, scenario):
        tc = get_test_cases()[scenario]
        period = tc["period"]
        location = tc["location"]
        return utils.get_sim_res_file_name_per_TEMA_spec(period, location, self.solution)

    def run_ecorouting(self, process: SPopen):
        logger.debug("EcoRouting", "[Sim] starting Popen process")
        eco_proc = process.start()
        logger.debug("EcoRouting", "[Sim] started Popen process")
        try:
            logger.debug("EcoRouting", "[Sim] waiting for eco_proc.communicate(%d\\n-1\\n)" % self.solution)
            out = eco_proc.communicate(input=b"%d\n-1\n" % self.solution, timeout=Globals.TASK_MANAGER_MAX_TIMEOUT)
            logger.debug("EcoRouting", "[Sim] eco_proc.communicate(%d\\n-1\\n) finished" % self.solution)
            logger.info("EcoRouting", out[0].decode().rstrip())
        except BaseException as e:
            if isinstance(e, TimeoutExpired):
                timeout = Globals.TASK_MANAGER_MAX_TIMEOUT
                logger.info("EcoRouting", "EcoRouting Sim process exceeded %d seconds, and will be terminated" % timeout)
            raise
        finally:
            logger.debug("EcoRouting", "[Sim] terminating Popen process")
            eco_proc.terminate()
            logger.debug("EcoRouting", "[Sim] terminated Popen process")


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
            with file_copy_lock:
                utils.copy_dir_contents(Globals.ECOROUTING_DIR, self.cwd)
            if self.mode.can_generate_TEMA_data():
                src = os.path.join(get_test_cases()[self.scenario]["ifolder"], Globals.TEMA_ADDITIONAL_FILES_FILE_NAME)
                dst = os.path.join(self.cwd, Globals.ECOROUTING_ADDITIONAL_FILES_FILE_NAME)
                utils.merge_additional_files_content(src, dst, [Globals.SUMO_EDGE_DATA_XML_TAG])

    def start(self):
        if self.cwd == os.getcwd() or self.cwd == Globals.ECOROUTING_DIR:
            logger.error("EcoRouting", "EcoRoutingTask task ID = %s is set for cwd %s" % (self.task_id, self.cwd))
            self.status = TaskStatus.Failed
            return
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
        print_info = (self.task_id, self.status.name, self.cwd, cmd)
        logger.info("EcoRouting", "Terminated EcoRouting process (task ID = %s | status = %s | cwd = %s | cmd = %s)" % print_info)

    def after(self):
        if self.cwd != os.getcwd():
            if self.mode.can_generate_TEMA_data():
                out_dir = self.mode.get_output_dir(self.scenario)
                all_veh_edge_data = os.path.join(self.cwd, Globals.TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME)
                with file_copy_lock:
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
            logger.error("EcoRouting", "EcoRoutingVideoTask task ID = %s is set for DISPLAY :0" % self.task_id)
            self.status = TaskStatus.Failed
            return
        display = self.env["DISPLAY"]
        logger.info("EcoRouting", "Running EcoRouting process on DISPLAY %s through a VNC server" % display)
        EcoRoutingTask.start(self)

    def after(self):
        snapshots_path = os.path.join(self.cwd, Globals.SNAPSHOTS_DIR)
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        # os.system(utils.get_video_cmd(src_path, self.video_name))
        gztar_file = "%s.%s" % (self.video_name, Globals.VIDEOS_TARGZ_FILE_TYPE)
        path_to_gztar_file = os.path.join(self.cwd, gztar_file)
        logger.debug("EcoRouting", "[EcoRoutingVideo] compressing %s to %s" % (snapshots_path, gztar_file))
        utils.zip_targz(path_to_gztar_file, snapshots_path, Globals.SNAPSHOTS_DIR)
        logger.debug("EcoRouting", "[EcoRoutingVideo] %s created at %s" % (gztar_file, path_to_gztar_file))
        dst_path = os.path.join(Globals.VIDEOS_TARGZ_DIR, gztar_file)
        shutil.move(path_to_gztar_file, dst_path)
        logger.debug("EcoRouting", "[EcoRoutingVideo] %s moved to %s" % (path_to_gztar_file, dst_path))
        utils.clear_and_remove_dir(snapshots_path)
        display = self.env["DISPLAY"]
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        os.system("vncserver -kill %s" % display)
        EcoRoutingTask.after(self)


class TEMAEcoIndicatorTask(Task):
    def __init__(self, task_id, scenario, mode: EcoRoutingMode):
        Task.__init__(self, task_id)
        self.scenario = scenario
        self.mode = mode

    def get_cwd_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def get_display_mode(self) -> TaskRunMode:
        return TaskRunMode.Default

    def before(self):
        if self.cwd != os.getcwd():
            utils.ensure_dir_exists(self.cwd)
            utils.clear_dir(self.cwd)
            with file_copy_lock:
                utils.copy_dir_contents(Globals.TEMA_DIR, self.cwd)
                for file_src, file_dst in self.mode.get_TEMA_files(self.scenario):
                    src_path = os.path.join(self.mode.get_output_dir(self.scenario), file_src)
                    dst_path = os.path.join(self.cwd, file_dst)
                    shutil.copyfile(src_path, dst_path)

    def start(self):
        if self.cwd == os.getcwd() or self.cwd == Globals.ECOROUTING_DIR:
            logger.error("TEMA", "TEMATask task ID = %s is set for cwd %s" % (self.task_id, self.cwd))
            self.status = TaskStatus.Failed
            return
        eco_ind_cmd = ["./eco_indicator"]
        eco_ind_proc = SPopen(eco_ind_cmd, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        logger.info("TEMA", "Started TEMA process (task ID = %s | cwd = %s)" % (self.task_id, self.cwd))
        self.status = TaskStatus.Starting
        self.before()
        self.status = TaskStatus.Running
        try:
            print_info = (self.task_id, self.cwd, eco_ind_cmd)
            logger.info("TEMA", "Started TEMA Eco-Indicator process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
            self.mode.run_eco_indicator(eco_ind_proc)
            logger.info("TEMA", "Terminated TEMA Eco-Indicator process (task ID = %s | cwd = %s | cmd = %s)" % print_info)
        except BaseException as e:
            logger.error("TEMA", "Error in task ID = %s: %s" % (self.task_id, e))
            self.status = TaskStatus.Failed
        if self.status != TaskStatus.Failed:
            self.status = TaskStatus.Completing
        self.after()
        if self.status != TaskStatus.Failed:
            self.status = TaskStatus.Completed
        print_info = (self.task_id, self.status.name, self.cwd)
        logger.info("TEMA", "Terminated TEMA process (task ID = %s | status = %s | cwd = %s)" % print_info)

    def after(self):
        if self.cwd != os.getcwd():
            res_file = self.mode.get_TEMA_res_file(self.scenario)
            if res_file in os.listdir(self.cwd):
                out_dir = self.mode.get_output_dir(self.scenario)
                shutil.move(os.path.join(self.cwd, res_file), os.path.join(out_dir, Globals.TEMA_RESULTS_FILE_NAME))
            else:
                logger.error("TEMA", "Results file %s not found in %s" % (res_file, self.cwd))
                self.status = TaskStatus.Failed
            utils.clear_and_remove_dir(self.cwd)


class TEMAHeatmapsTask(Task):
    def __init__(self, task_id, scenario, mode: EcoRoutingMode, image_dir_name):
        Task.__init__(self, task_id)
        self.scenario = scenario
        self.mode = mode
        self.image_dir_name = image_dir_name

    def get_cwd_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def get_display_mode(self) -> TaskRunMode:
        return TaskRunMode.Isolated

    def before(self):
        if self.cwd != os.getcwd():
            utils.ensure_dir_exists(self.cwd)
            utils.clear_dir(self.cwd)
            with file_copy_lock:
                utils.copy_dir_contents(Globals.TEMA_DIR, self.cwd)
                utils.copy_dir_contents(Globals.MATLAB_LIB_DIR, self.cwd)
                net_file_path, net_file = self.mode.get_net_file(self.scenario)
                shutil.copyfile(os.path.join(net_file_path, net_file), os.path.join(self.cwd, net_file))
                res_file_src = os.path.join(self.mode.get_output_dir(self.scenario), Globals.TEMA_RESULTS_FILE_NAME)
                res_file_dst = os.path.join(self.cwd, self.mode.get_TEMA_res_file(self.scenario))
                shutil.copyfile(res_file_src, res_file_dst)
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
            logger.error("TEMA", "TEMATask task ID = %s is set for DISPLAY :0" % self.task_id)
            self.status = TaskStatus.Failed
            return
        display = self.env["DISPLAY"]
        logger.info("TEMA", "Running TEMA process on DISPLAY %s through a VNC server" % display)
        if self.cwd == os.getcwd() or self.cwd == Globals.ECOROUTING_DIR:
            logger.error("TEMA", "TEMATask task ID = %s is set for cwd %s" % (self.task_id, self.cwd))
            self.status = TaskStatus.Failed
            return
        net_file = self.mode.get_net_file(self.scenario)[1]
        rou_file = self.mode.get_TEMA_route_file(self.scenario)
        traci_port = str(Globals.TEMA_TRACI_BASE_PORT + int(display.replace(":", "")))
        heatmap_cmd = ["./heatmaps", net_file, rou_file, traci_port]
        heatmap_proc = SPopen(heatmap_cmd, cwd=self.cwd, env=self.env, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        logger.info("TEMA", "Started TEMA process (task ID = %s | cwd = %s)" % (self.task_id, self.cwd))
        self.status = TaskStatus.Starting
        self.before()
        self.status = TaskStatus.Running
        try:
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
        print_info = (self.task_id, self.status.name, self.cwd)
        logger.info("TEMA", "Terminated TEMA process (task ID = %s | status = %s | cwd = %s)" % print_info)

    def after(self):
        display = self.env["DISPLAY"]
        # FIXME: replace os.system by subprocess in order to redirect output to logger's STDOUT
        os.system("vncserver -kill %s" % display)
        if self.cwd != os.getcwd():
            path_dst = os.path.join(Globals.HEATMAPS_DIR, self.image_dir_name)
            utils.ensure_dir_exists(path_dst)
            heatmaps_count = 0
            for file in os.listdir(self.cwd):
                if file.endswith(Globals.HEATMAPS_FILE_TYPE) and "draft" not in file:
                    shutil.move(os.path.join(self.cwd, file), os.path.join(path_dst, file))
                    heatmaps_count += 1
            if heatmaps_count != Globals.HEATMAP_EXPECTED_COUNT:
                print_info = (heatmaps_count, self.cwd, Globals.HEATMAP_EXPECTED_COUNT)
                logger.error("TEMA", "Only %d heatmap files were found in %s out of an expected %d" % print_info)
                utils.clear_and_remove_dir(path_dst)
                self.status = TaskStatus.Failed
            utils.clear_and_remove_dir(self.cwd)


class EcoRoutingTaskManager(TaskManager):
    def get_dependency_tree(self, root: TaskDependency, task_list: List[Task]) -> TaskDependency:
        base_tasks = []
        base_eco_indicator_tasks = []
        base_heatmap_tasks = []
        pred_tasks = []
        sim_tasks = []
        sim_eco_indicator_tasks = []
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
            elif isinstance(task, TEMAEcoIndicatorTask):
                if type(task.mode) is Base:
                    base_eco_indicator_tasks.append(task)
                elif type(task.mode) is Sim:
                    sim_eco_indicator_tasks.append(task)
                else:
                    print_info = (task.mode.__class__.__name__, task.task_id)
                    logger.warn("TaskManager", "Unknown EcoRoutingMode %s for TEMAEcoIndicatorTask task ID = %s " % print_info)
            elif isinstance(task, TEMAHeatmapsTask):
                if type(task.mode) is Base:
                    base_heatmap_tasks.append(task)
                elif type(task.mode) is Sim:
                    sim_heatmap_tasks.append(task)
                else:
                    print_info = (task.mode.__class__.__name__, task.task_id)
                    logger.warn("TaskManager", "Unknown EcoRoutingMode %s for TEMAHeatmapsTask task ID = %s " % print_info)
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

        for base_eco_indicator_task in base_eco_indicator_tasks:
            base_eco_indicator_task_dep = TaskDependency(base_eco_indicator_task)

            def f_base_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask) and isinstance(dep.task.mode, Base):
                    return dep.task.scenario == base_eco_indicator_task.scenario
                return False

            parent_base_task_dep = find_matching_task_dep(root, f_base_parent)
            if parent_base_task_dep:
                parent_base_task_dep.add_child(base_eco_indicator_task_dep)
            else:
                root.add_child(base_eco_indicator_task_dep)

        for base_heatmap_task in base_heatmap_tasks:
            base_heatmap_task_dep = TaskDependency(base_heatmap_task)

            def f_base_eco_indicator_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, TEMAEcoIndicatorTask) and isinstance(dep.task.mode, Base):
                    return dep.task.scenario == base_heatmap_task.scenario
                return False

            parent_base_eco_indicator_task_dep = find_matching_task_dep(root, f_base_eco_indicator_parent)
            if parent_base_eco_indicator_task_dep:
                parent_base_eco_indicator_task_dep.add_child(base_heatmap_task_dep)
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

        for sim_eco_indicator_task in sim_eco_indicator_tasks:
            sim_eco_indicator_task_dep = TaskDependency(sim_eco_indicator_task)

            def f_sim_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, EcoRoutingTask):
                    if isinstance(dep.task.mode, Sim) and isinstance(sim_eco_indicator_task.mode, Sim):
                        return dep.task.scenario == sim_eco_indicator_task.scenario and \
                               dep.task.mode.objective1 == sim_eco_indicator_task.mode.objective1 and \
                               dep.task.mode.objective2 == sim_eco_indicator_task.mode.objective2 and \
                               dep.task.mode.solution == sim_eco_indicator_task.mode.solution
                return False

            parent_sim_task_dep = find_matching_task_dep(root, f_sim_parent)
            if parent_sim_task_dep:
                parent_sim_task_dep.add_child(sim_eco_indicator_task_dep)
            else:
                root.add_child(sim_eco_indicator_task_dep)

        for sim_heatmap_task in sim_heatmap_tasks:
            sim_heatmap_task_dep = TaskDependency(sim_heatmap_task)

            def f_sim_eco_indicator_parent(dep: TaskDependency) -> bool:
                if isinstance(dep.task, TEMAEcoIndicatorTask):
                    if isinstance(dep.task.mode, Sim) and isinstance(sim_heatmap_task.mode, Sim):
                        return dep.task.scenario == sim_heatmap_task.scenario and \
                               dep.task.mode.objective1 == sim_heatmap_task.mode.objective1 and \
                               dep.task.mode.objective2 == sim_heatmap_task.mode.objective2 and \
                               dep.task.mode.solution == sim_heatmap_task.mode.solution
                return False

            parent_sim_eco_indicator_task_dep = find_matching_task_dep(root, f_sim_eco_indicator_parent)
            if parent_sim_eco_indicator_task_dep:
                parent_sim_eco_indicator_task_dep.add_child(sim_heatmap_task_dep)
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
    log = []
    tasks: Dict[str, Task] = {}

    def verbose(value: bool) -> str:
        return "FOUND" if value else "MISSING"

    def exists(path: str) -> bool:
        return os.path.exists(path)

    def join(*paths: str) -> str:
        return os.path.join(*paths)

    def check_TEMA_simulation_data(path) -> bool:
        files = os.listdir(path)
        return Globals.TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME in files and \
               Globals.TEMA_NOISE_EDGE_DATA_FILE_NAME in files and \
               Globals.TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME in files

    def check_video(video_name) -> bool:
        path_mp4 = join(Globals.VIDEOS_DIR, video_name + "." + Globals.VIDEOS_FILE_TYPE)
        path_targz = join(Globals.VIDEOS_TARGZ_DIR, video_name + "." + Globals.VIDEOS_TARGZ_FILE_TYPE)
        return (exists(path_mp4) and os.path.isfile(path_mp4)) or (exists(path_targz) and os.path.isfile(path_targz))

    def check_heatmap(heatmap_dir_name) -> bool:
        path = join(Globals.HEATMAPS_DIR, heatmap_dir_name)
        if exists(path) and os.path.isdir(path):
            heatmaps = [f for f in os.listdir(path) if f.endswith(Globals.HEATMAPS_FILE_TYPE) and "draft" not in f]
            return len(heatmaps) == Globals.HEATMAP_EXPECTED_COUNT
        return False

    def check_task_completeness(task: Task, *conditions: bool):
        if all(list(conditions)):
            # FIXME -> the Completed status should NOT be attributed here; works for now
            task.status = TaskStatus.Completed

    log.append("Checking content...")

    for scenario in tcs:
        tc = tcs[scenario]

        log.append("Scenario %s (%s)" % (tc["prettyName"], scenario))

        data_dir = tc["ifolder"]
        data_net = join(data_dir, tc["netfile"])
        data_rou = join(data_dir, tc["roufile"])
        data_dir_exists = exists(data_dir)
        data_net_exists = exists(data_net)
        data_rou_exists = exists(data_rou)

        log.append("\tDataset: Net file: %s | Route file: %s " % (verbose(data_net_exists), verbose(data_rou_exists)))

        if data_dir_exists and data_net_exists and data_rou_exists:
            res_dir = tc["ofolder"]
            base_dir = join(res_dir, "inputdata")

            base_TEMA_res = join(base_dir, Globals.TEMA_RESULTS_FILE_NAME)
            base_rou = join(base_dir, tc["bname"]) + "-base.rou.xml"
            base_TEMA_res_exists = exists(base_TEMA_res)
            base_rou_exists = exists(base_rou)
            base_TEMA_data_exists = check_TEMA_simulation_data(base_dir)

            base_tasks = {}
            base_ecorouting_task_name = scenario
            base_eco_indicator_task_name = base_ecorouting_task_name + "_eco_indicator"
            base_heatmap_task_name = base_ecorouting_task_name + "_heatmap"
            base_task_mode = Base()

            task = EcoRoutingTask(base_ecorouting_task_name, scenario, base_task_mode)
            base_tasks[base_ecorouting_task_name] = task
            check_task_completeness(task, base_TEMA_data_exists, base_rou_exists)

            task = TEMAEcoIndicatorTask(base_eco_indicator_task_name, scenario, base_task_mode)
            base_tasks[base_eco_indicator_task_name] = task
            check_task_completeness(task, base_TEMA_res_exists)

            base_media_name = utils.format_file_name_base(scenario)

            base_video_exists = check_video(base_media_name)
            task = EcoRoutingVideoTask(base_ecorouting_task_name, scenario, base_task_mode, base_media_name)
            base_tasks[base_ecorouting_task_name] = task
            check_task_completeness(task, base_video_exists)

            base_heatmap_exists = check_heatmap(base_media_name)
            task = TEMAHeatmapsTask(base_heatmap_task_name, scenario, base_task_mode, base_media_name)
            # base_tasks[base_heatmap_task_name] = task
            check_task_completeness(task, base_heatmap_exists)
            
            for task_id, base_task in base_tasks.items():
                tasks[task_id] = base_task

            log.append("\tBase: Route file: %s | TEMA data: %s | TEMA results file: %s | Video file: %s | "
                       "Heatmaps: %s" % (verbose(base_rou_exists), verbose(base_TEMA_data_exists),
                                         verbose(base_TEMA_res_exists), verbose(base_video_exists),
                                         verbose(base_heatmap_exists)))

            for objective_combination in total_objective_combinations:
                obj1, obj2 = utils.reverse_format_objective_names(objective_combination)

                pred_dir = join(res_dir, objective_combination)
                base_eval = join(pred_dir, "base.eval")
                pred_eval = join(pred_dir, "pred.eval")

                pred_dir_exists = exists(pred_dir)
                base_eval_exists = exists(base_eval)
                pred_eval_exists = exists(pred_eval)

                pred_ecorouting_task_name = scenario
                pred_task_mode = Pred(obj1, obj2)

                task = EcoRoutingTask(pred_ecorouting_task_name, scenario, pred_task_mode)
                check_task_completeness(task, pred_dir_exists, base_eval_exists, pred_eval_exists)
                tasks[pred_ecorouting_task_name] = task
                
                if pred_dir_exists:

                    obj1_pretty = Globals.ECOROUTING_METRICS[obj1]["pretty"]
                    obj2_pretty = Globals.ECOROUTING_METRICS[obj2]["pretty"]
                    log.append("\t\t%s - %s" % (obj1_pretty, obj2_pretty))

                    for file in os.listdir(pred_dir):
                        if os.path.isdir(join(pred_dir, file)) and file.startswith("solution"):
                            sim_dir = join(pred_dir, file)
                            sol_number = int(file.replace("solution", "").strip())

                            sim_TEMA_res = join(sim_dir, Globals.TEMA_RESULTS_FILE_NAME)
                            sim_rou = join(sim_dir, tc["bname"]) + ".rou.xml"
                            sim_TEMA_res_exists = exists(sim_TEMA_res)
                            sim_rou_exists = exists(sim_rou)
                            sim_TEMA_data_exists = check_TEMA_simulation_data(sim_dir)

                            sim_tasks = {}
                            sim_ecorouting_task_name = utils.format_solution_name(scenario, obj1, obj2, sol_number)
                            sim_eco_indicator_task_name = sim_ecorouting_task_name + "_eco_indicator"
                            sim_heatmap_task_name = sim_ecorouting_task_name + "_heatmap"
                            sim_task_mode = Sim(obj1, obj2, sol_number)

                            task = EcoRoutingTask(sim_ecorouting_task_name, scenario, sim_task_mode)
                            sim_tasks[sim_ecorouting_task_name] = task
                            check_task_completeness(task, sim_TEMA_data_exists, sim_rou_exists)

                            task = TEMAEcoIndicatorTask(sim_eco_indicator_task_name, scenario, sim_task_mode)
                            sim_tasks[sim_eco_indicator_task_name] = task
                            check_task_completeness(task, sim_TEMA_res_exists)

                            sim_media_name = utils.format_file_name_sim(scenario, obj1, obj2, sol_number)

                            sim_video_exists = check_video(sim_media_name)
                            task = EcoRoutingVideoTask(sim_ecorouting_task_name, scenario, sim_task_mode, sim_media_name)
                            # FIXME: only generate video for each 1st solution -> should be removed!!!
                            if sol_number == 1:
                                sim_tasks[sim_ecorouting_task_name] = task
                            check_task_completeness(task, sim_video_exists)

                            sim_heatmap_exists = check_heatmap(sim_media_name)
                            task = TEMAHeatmapsTask(sim_heatmap_task_name, scenario, sim_task_mode, sim_media_name)
                            # sim_tasks[sim_heatmap_task_name] = task
                            check_task_completeness(task, sim_heatmap_exists)

                            for task_id, sim_task in sim_tasks.items():
                                tasks[task_id] = sim_task

                            log.append("\t\t\tSolution %d: Route file: %s | TEMA data: %s | TEMA results file: %s | "
                                       "Video file: %s | Heatmaps: %s" % (sol_number, verbose(sim_rou_exists),
                                                                          verbose(sim_TEMA_data_exists),
                                                                          verbose(sim_TEMA_res_exists),
                                                                          verbose(sim_video_exists),
                                                                          verbose(sim_heatmap_exists)))

    completed_tasks = sum([t.status == TaskStatus.Completed for _, t in tasks.items()])
    log.append("Finished checking content: Completed tasks: %d/%d" % (completed_tasks, len(tasks)))

    if not silent:
        logger.info("ContentChecker", "\n".join(log))

    return tasks
