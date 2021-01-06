import os
import re
import shutil
import tarfile
import time
from importlib import machinery, util
from types import ModuleType
from typing import List, Tuple, Callable

from globals import Globals
from logger import logger


def format_objective_names(objective1, objective2):
    o = sorted([objective1, objective2])
    return "%s%s%s" % (o[0], Globals.OBJECTIVE_SEPARATOR, o[1])


def format_scenario_name(scenario, objective1, objective2):
    return "%s%s%s" % (scenario, Globals.SCENARIO_SEPARATOR, format_objective_names(objective1, objective2))


def format_solution_name(scenario, objective1, objective2, solution):
    return "%s%s%s" % (format_scenario_name(scenario, objective1, objective2), Globals.SOLUTION_SEPARATOR, solution)


def format_file_name_base(scenario):
    return "%s.base" % scenario


def format_file_name_sim(scenario, objective1, objective2, solution):
    return "%s.sim%d" % (format_scenario_name(scenario, objective1, objective2), solution)


def ensure_dir_exists(path, silent=False):
    if not os.path.exists(path):
        os.makedirs(path)
        if not silent:
            logger.info("Utils", "Created directory %s" % path)


def copy_dir_contents(path_src, path_dst, silent=False):
    if os.path.exists(path_src) and os.path.isdir(path_src):
        ensure_dir_exists(path_dst)
        shutil.copytree(path_src, path_dst, dirs_exist_ok=True)
        if not silent:
            logger.info("Utils", "Copied contents of directory %s to directory %s" % (path_src, path_dst))


def clear_dir(path, silent=False):
    if os.path.exists(path) and os.path.isdir(path):
        removed_something = False
        for name in os.listdir(path):
            child_path = os.path.join(path, name)
            if os.path.isdir(os.path.join(path, name)):
                shutil.rmtree(child_path, ignore_errors=True)
                removed_something = True
            if os.path.isfile(os.path.join(path, name)):
                os.remove(child_path)
                removed_something = True
        if removed_something and not silent:
            logger.info("Utils", "Emptied directory %s" % path)


def clear_and_remove_dir(path, silent=False):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        # if os.path.exists(path):
        #     os.rmdir(path)
        if not silent:
            logger.info("Utils", "Emptied and removed directory %s" % path)


def read_ev_file(file_name):
    f = open(file_name, "r")
    data = {}
    for line in f.readlines():
        items = line.strip().split("\t")
        if len(items) == 2:
            header, value = items[0].strip(), float(items[1].strip())
            data[header] = value
    f.close()
    return data


def read_eval_file(file_name):
    f = open(file_name, "r")
    line = f.readline()
    line = line.replace("#", "").strip()
    headers = [h.strip() for h in line.split(" ")]
    lines = [l for l in f.readlines() if l.strip()]
    f.close()

    eval = {h: [] for h in headers}
    for i in range(len(lines)):
        line = lines[i]
        values = [float(v.strip()) for v in line.split(" ")]
        for j in range(len(values)):
            eval[headers[j]].append(values[j])

    return eval


def write_eval_file(file_name, header: list, data: list):
    f = open(file_name, "w")
    header_str = " ".join(["#"] + header)
    f.write(header_str + "\n")
    items_str = []
    for item in data:
        item_str = " ".join(["{:.18e}".format(item[h]) for h in header])
        items_str.append(item_str)
    f.write("\n".join(items_str))
    f.close()


def read_res_file(file_name):
    f = open(file_name, "r")
    line = f.readline()
    headers = [h.strip() for h in line.split("\t")]
    lines = [l for l in f.readlines() if l.strip()]
    f.close()

    res = {h: [] for h in headers}
    for i in range(len(lines)):
        line = lines[i]
        values = [v.strip() for v in line.split("\t")]
        for j in range(len(values)):
            res[headers[j]].append(float(values[j]) if headers[j] != "link" else values[j])

    return res


def res_to_TEMA_ev(res):
    
    def protect(c: Callable[[int], float], i: int):
        try:
            return c(i)
        except:
            return float(0)

    def for_each(c: Callable[[int], float]):
        return [protect(c, i) for i in range(len(res["link"]))]

    def avg(l: list):
        return sum(l)/len(l)

    ttime = res["ttime"]
    length = res["length"]
    cost_co2 = res["cost_co2"]
    cost_co = res["cost_co"]
    cost_pm10 = res["cost_pm10"]
    cost_pm25 = res["cost_pm25"]
    cost_nox = res["cost_nox"]
    cost_eco_indicator = res["cost_eco_indicator"]
    totalvehicles = res["totalvehicles"]

    return {
        "ttime":                sum(for_each(lambda i: ttime[i] * totalvehicles[i]))/3600,
        "length":               sum(for_each(lambda i: (length[i]/1000) * totalvehicles[i])),
        "cost_co2":             sum(cost_co2)/1_000_000,
        "cost_co2_veh":         avg(for_each(lambda i: cost_co2[i]/((length[i]/1000) * totalvehicles[i]))),
        "cost_co":              sum(cost_co)/1000,
        "cost_PMx":             sum(for_each(lambda i: cost_pm10[i] + cost_pm25[i]))/1000,
        "cost_nox":             sum(cost_nox)/1000,
        "cost_eco_indicator":   sum(for_each(lambda i: cost_eco_indicator[i] * totalvehicles[i]))
    }


def get_simulation_files(netfile, roufile):
    return {
        "gui-settings": open(os.path.join(Globals.ECOROUTING_DIR, Globals.ECOROUTING_GUI_SETTINGS_FILE_NAME), "rb"),
        "net-file": open(netfile, "rb"),
        "route-files": open(roufile, "rb")
    }


def get_objective_combinations():
    combinations = set()
    for objective1 in Globals.ECOROUTING_METRICS:
        for objective2 in Globals.ECOROUTING_METRICS:
            if objective1 != objective2:
                objectives = format_objective_names(objective1, objective2)
                combinations.add(objectives)
    return list(combinations)


def is_objective_pair(name):
    split = name.split(Globals.OBJECTIVE_SEPARATOR)
    return len(split) == 2 and split[0] in Globals.ECOROUTING_METRICS and split[1] in Globals.ECOROUTING_METRICS


def reverse_format_objective_names(name):
    if not is_objective_pair(name):
        return None
    split = name.split(Globals.OBJECTIVE_SEPARATOR)
    return split[0], split[1]


def add_snapshots_to_gui_settings(path_to_gui_settings):
    # remove_snapshots_from_gui_settings(path_to_gui_settings)
    snapshot_file_name = os.path.join(Globals.SNAPSHOTS_DIR, Globals.SNAPSHOTS_FILE_NAME)
    snapshot_str = "\n".join([Globals.SNAPSHOTS_XML_ELEMENT % (snapshot_file_name % i, i) for i in
                              range(Globals.SNAPSHOTS_COUNT)])
    gui_settings = os.path.join(path_to_gui_settings, Globals.ECOROUTING_GUI_SETTINGS_FILE_NAME)
    with open(gui_settings, "r") as f:
        content = f.read()

    content = content.replace("</viewsettings>", "%s\n</viewsettings>" % snapshot_str)

    with open(gui_settings, "w") as f:
        f.write(content)

    del content


def remove_snapshots_from_gui_settings(path_to_gui_settings):
    xml_line = Globals.SNAPSHOTS_XML_ELEMENT
    regex = re.compile(xml_line.replace("%s", ".+").replace("%d", "[0-9]+").strip())
    gui_settings = os.path.join(path_to_gui_settings, Globals.ECOROUTING_GUI_SETTINGS_FILE_NAME)
    with open(gui_settings, "r") as f:
        content = f.readlines()

    content = [line for line in content if not regex.match(line.strip())]

    with open(gui_settings, "w") as f:
        f.writelines(content)

    del content


def merge_additional_files_content(file_src, file_dest, xml_tags: list):
    content_to_add = []
    with open(file_src, "r") as f:
        for line in f.readlines():
            for xml_tag in xml_tags:
                if line.replace("<", "").replace(">", "").strip().startswith(xml_tag):
                    content_to_add.append(line.strip())
                    break
    content_to_add_str = "\n".join(content_to_add)

    with open(file_dest, "r") as f:
        content = f.read()

    content = content.replace("</additional>", "%s\n</additional>" % content_to_add_str)

    with open(file_dest, "w") as f:
        f.write(content)

    del content


def remove_tags_from_xml(file, tags: List[Tuple[str, str]]):
    with open(file, "r") as f:
        content = f.read()

    for tag in tags:
        start = tag[0]
        end = tag[1]
        content = re.sub("(%s.*?%s)" % (start, end), "", content, flags=re.DOTALL)

    content = re.sub("\n(\n)+", "", content)

    with open(file, "w") as f:
        f.write(content)

    del content


def is_module_available(module_name):
    return util.find_spec(module_name)


def import_module(path_to_py_file, module_name) -> ModuleType:
    loader = machinery.SourceFileLoader(module_name, path_to_py_file)
    return loader.load_module(module_name)


def convert_base_file_name_to_TEMA_spec(file_name, period, location):
    name = file_name.replace(".xml", "")
    suffix = Globals.TEMA_FILE_NAME_BASE_SUFFIX
    return "%s_%s_Routing_%s_%s" % (name, period, location, suffix)


def convert_sim_file_name_to_TEMA_spec(file_name, period, location, solution):
    name = file_name.replace(".xml", "")
    suffix = Globals.TEMA_FILE_NAME_SIM_SUFFIX_FORMAT % int(solution)
    return "%s_%s_Routing_%s_%s" % (name, period, location, suffix)


def get_base_route_file_name_per_TEMA_spec(period):
    return "Trips%s_baseline.rou.xml" % period


def get_sim_route_file_name_per_TEMA_spec(bname, period, location, solution):
    return "%s_%s_%s_solution%d.rou.xml" % (bname, period, location, solution)


def get_base_res_file_name_per_TEMA_spec(period, location):
    return "%s_baseline_Routing_%s_results.txt" % (period, location)


def get_sim_res_file_name_per_TEMA_spec(period, location, solution):
    return "%s_optimized_solution%d_Routing_%s_results.txt" % (period, solution, location)


def zip_targz(path_to_targz_file, dir_to_zip, targz_root_dir):
    with tarfile.open(path_to_targz_file, "w:gz") as tar:
        tar.add(dir_to_zip, arcname=targz_root_dir)


def unzip_targz(path_to_targz_file, unzip_to_dir):
    with tarfile.open(path_to_targz_file, "r:gz") as tar:
        tar.extractall(path=unzip_to_dir)


def wait(millis=0):
    time.sleep(millis/1000)


def wait_until(condition: Callable[[], bool], millis=0):
    while not condition():
        wait(millis)
