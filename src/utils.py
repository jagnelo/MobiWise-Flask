import os
import re
import shutil
from enum import Enum

from globals import Globals


def format_objective_names(objective1, objective2):
    o = sorted([objective1, objective2])
    return "%s%s%s" % (o[0], Globals.OBJECTIVE_SEPARATOR, o[1])


def format_scenario_name(scenario, objective1, objective2):
    return "%s%s%s" % (scenario, Globals.SCENARIO_SEPARATOR, format_objective_names(objective1, objective2))


def format_file_name_base(scenario):
    return "%s.base" % scenario


def format_file_name_sim(scenario, objective1, objective2, solution):
    return "%s.sim%d" % (format_scenario_name(scenario, objective1, objective2), solution)


def get_file_path_or_default(path, name, extension):
    file_path = os.path.join(path, "%s.%s" % (name, extension))
    if not os.path.exists(file_path):
        file_path = os.path.join(path, "default.%s" % extension)
    return file_path


def get_video_cmd(snapshots_dir, video_name):
    path = os.path.join(snapshots_dir, Globals.SNAPSHOTS_FILE_NAME)
    videos_dir = os.path.join(Globals.VIDEOS_DIR, video_name)
    return Globals.FFMPEG_CMD % (path, videos_dir)


def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print("Created directory %s" % path)


def copy_dir_contents(path_src, path_dst):
    if os.path.exists(path_src) and os.path.isdir(path_src):
        ensure_dir_exists(path_dst)
        shutil.copytree(path_src, path_dst, dirs_exist_ok=True)
        print("Copied contents of directory %s to directory %s" % (path_src, path_dst))


def clear_dir(path):
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
        if removed_something:
            print("Emptied directory %s" % path)


def clear_and_remove_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        print("Emptied and removed directory %s" % path)


def read_eval_file(file_name):
    f = open(file_name, "r")
    line = f.readline()
    line = line.replace("#", "").strip()
    headers = [h.strip() for h in line.split(" ")]
    lines = [l for l in f.readlines() if l.strip()]
    f.close()

    ev = {h: [] for h in headers}
    for i in range(len(lines)):
        line = lines[i]
        values = [float(v.strip()) for v in line.split(" ")]
        for j in range(len(values)):
            ev[headers[j]].append(values[j])

    return ev


def get_simulation_files(netfile, roufile):
    return {
        "gui-settings": open(Globals.SUMO_GUI_SETTINGS_FILE_NAME, "rb"),
        "additional-files": open(moreOutputInfo.xml, "rb"),
        "net-file": open(netfile, "rb"),
        "route-files": open(roufile, "rb"),
        "edge-data-out": open("edge-data-out.xml", "rb"),
        "basecars-emission-by-edges-out": open("basecars-emission-by-edges-out.xml", "rb")
    }


class TextFormat(Enum):
    Red = "\033[1;31m"
    Blue = "\033[1;34m"
    Cyan = "\033[1;36m"
    Green = "\033[0;32m"
    Reverse = "\033[;7m"


def format_text(text:str, format:TextFormat, bold=False):
    Reset = "\033[0;0m"
    Bold = "\033[;1m"
    return (Bold if bold else "") + format.value + text + Reset


def get_objective_combinations():
    combinations = set()
    for objective1 in Globals.METRICS:
        for objective2 in Globals.METRICS:
            if objective1 != objective2:
                objectives = format_objective_names(objective1, objective2)
                combinations.add(objectives)
    return list(combinations)


def is_objective_pair(name):
    split = name.split(Globals.OBJECTIVE_SEPARATOR)
    return len(split) == 2 and split[0] in Globals.METRICS and split[1] in Globals.METRICS


def reverse_format_objective_names(name):
    if not is_objective_pair(name):
        return None
    split = name.split(Globals.OBJECTIVE_SEPARATOR)
    return split[0], split[1]


def add_snapshots_to_gui_settings(path_to_gui_settings):
    remove_snapshots_from_gui_settings(path_to_gui_settings)
    snapshot_file_name = os.path.join(Globals.SNAPSHOTS_DIR, Globals.SNAPSHOTS_FILE_NAME)
    snapshot_str = "\n".join([Globals.SNAPSHOTS_XML_ELEMENT % (snapshot_file_name % i, i) for i in
                              range(Globals.SNAPSHOTS_COUNT)])
    gui_settings = os.path.join(path_to_gui_settings, Globals.SUMO_GUI_SETTINGS_FILE_NAME)
    with open(gui_settings, "r") as f:
        content = f.read()

    content = content.replace("</viewsettings>", "%s\n</viewsettings>" % snapshot_str)

    with open(gui_settings, "w") as f:
        f.write(content)

    del content


def remove_snapshots_from_gui_settings(path_to_gui_settings):
    xml_line = Globals.SNAPSHOTS_XML_ELEMENT
    regex = re.compile(xml_line.replace("%s", ".+").replace("%d", "[0-9]+").strip())
    gui_settings = os.path.join(path_to_gui_settings, Globals.SUMO_GUI_SETTINGS_FILE_NAME)
    with open(gui_settings, "r") as f:
        content = f.readlines()

    content = [line for line in content if not regex.match(line.strip())]

    with open(gui_settings, "w") as f:
        f.writelines(content)

    del content
