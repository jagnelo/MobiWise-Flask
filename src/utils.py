import os
from enum import Enum

from globals import Globals


def format_objective_names(objective1, objective2):
    o = sorted([objective1, objective2])
    return "%s%s%s" % (o[0], Globals.objective_separator, o[1])


def format_db_entry_key(scenario, objective1, objective2):
    return "%s%s%s" % (scenario, Globals.scenario_separator, format_objective_names(objective1, objective2))


def format_file_name_base(scenario):
    return "%s.base" % scenario


def format_file_name_sim(scenario, objective1, objective2, solution):
    return "%s.sim%d" % (format_db_entry_key(scenario, objective1, objective2), solution)


def get_file_path_or_default(path, name, extension):
    file_path = os.path.join(path, "%s.%s" % (name, extension))
    if not os.path.exists(file_path):
        file_path = os.path.join(path, "default.%s" % extension)
    return file_path


def get_video_cmd(video_name):
    snapshots_dir = os.path.join(Globals.SNAPSHOTS_DIR, "snapshot%d.png")
    videos_dir = os.path.join(Globals.VIDEOS_DIR, video_name)
    return Globals.FFMPEG_CMD % (snapshots_dir, videos_dir)


def setup_snapshots_dir():
    if not os.path.exists(Globals.SNAPSHOTS_DIR):
        os.mkdir(Globals.SNAPSHOTS_DIR)


def clear_snapshots():
    for file in os.listdir(Globals.SNAPSHOTS_DIR):
        os.remove(os.path.join(Globals.SNAPSHOTS_DIR, file))


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
        "gui-settings": open("gui-settings.xml", "rb"),
        "additional-files": open("moreOutputInfo.xml", "rb"),
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
    split = name.split(Globals.objective_separator)
    return len(split) == 2 and split[0] in Globals.METRICS and split[1] in Globals.METRICS


def reverse_format_objective_names(name):
    if not is_objective_pair(name):
        return None
    split = name.split(Globals.objective_separator)
    return split[0], split[1]

