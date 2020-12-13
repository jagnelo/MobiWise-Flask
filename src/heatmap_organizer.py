import os

from globals import Globals
from logger import logger


def find_heatmaps_dirs():
    dirs = []
    for dir in os.listdir(Globals.HEATMAPS_DIR):
        if dir.endswith("." + Globals.HEATMAPS_FILE_TYPE):
            fixed_dir = dir.replace("." + Globals.HEATMAPS_FILE_TYPE, "")
            os.rename(os.path.join(Globals.HEATMAPS_DIR, dir), os.path.join(Globals.HEATMAPS_DIR, fixed_dir))
            dirs.append(fixed_dir)
        else:
            dirs.append(dir)
    return dirs


def organize_heatmap(dir):
    path = os.path.join(Globals.HEATMAPS_DIR, dir)
    for file in os.listdir(path):
        file_name = file.lower()
        if "draft" not in file_name:
            for metric in Globals.TEMA_HEATMAPS_METRICS:
                if metric in file_name:
                    if "routes" in file_name:
                        new_file = "%s_%s.%s" % (metric, "routes", Globals.HEATMAPS_FILE_TYPE)
                    else:
                        new_file = "%s.%s" % (metric, Globals.HEATMAPS_FILE_TYPE)
                    if file != new_file:
                        os.rename(os.path.join(path, file), os.path.join(path, new_file))
                        logger.info("HeatmapOrganizer", "Renamed %s to %s in %s" % (file, new_file, path))
        else:
            os.remove(os.path.join(path, file))


def run():
    for dir in find_heatmaps_dirs():
        logger.info("HeatmapOrganizer", "Organizing image files at %s" % dir)
        organize_heatmap(dir)
        if __name__ == '__main__':
            logger.flush()


if __name__ == '__main__':
    run()
