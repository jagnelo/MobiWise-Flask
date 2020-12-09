import os
import re
import subprocess
from subprocess import PIPE, STDOUT

import magic

import utils
from globals import Globals
from logger import logger


def find_video_targz_files():
    files = []
    for file in os.listdir(Globals.VIDEOS_TARGZ_DIR):
        if file.endswith(Globals.VIDEOS_TARGZ_FILE_TYPE) and not file.endswith("." + Globals.VIDEOS_TARGZ_FILE_TYPE):
            fixed_file = file.replace(Globals.VIDEOS_TARGZ_FILE_TYPE, "." + Globals.VIDEOS_TARGZ_FILE_TYPE)
            os.rename(os.path.join(Globals.VIDEOS_TARGZ_DIR, file), os.path.join(Globals.VIDEOS_TARGZ_DIR, fixed_file))
            files.append(fixed_file)
        else:
            files.append(file)
    return files


def generate_video_from_targz(targz_file_name):
    file_name = targz_file_name.replace("." + Globals.VIDEOS_TARGZ_FILE_TYPE, "")
    src_dir = os.path.join(Globals.VIDEOS_TARGZ_DIR, targz_file_name)
    dst_dir = os.path.join(Globals.VIDEOS_DIR, file_name)
    utils.unzip_targz(src_dir, dst_dir)
    if os.path.exists(os.path.join(dst_dir, Globals.SNAPSHOTS_DIR)):
        dst_dir = os.path.join(dst_dir, Globals.SNAPSHOTS_DIR)
    snapshots_path = os.path.join(dst_dir, Globals.SNAPSHOTS_DIR)
    for snapshot_name in os.listdir(snapshots_path):
        snapshot = os.path.join(snapshots_path, snapshot_name)
        f = magic.from_file(snapshot)
        w, h = re.search('(\d+) x (\d+)', f).groups()
        if int(w) == 1 and int(h) == 1:
            logger.warn("VideoGenerator", "Snapshot %s has dimensions 1x1 and will be removed" % snapshot_name)
            os.remove(snapshot)
    video_path = os.path.join(Globals.VIDEOS_DIR, file_name)
    cmd = Globals.FFMPEG_CMD % (snapshots_path, video_path)
    try:
        proc = subprocess.Popen(cmd.split(" "), stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        stdout, stderr = proc.communicate()
        logger.info("VideoGenerator", stdout.decode().rstrip())
        if stderr:
            logger.error("VideoGenerator", stderr.decode().rstrip())
        mp4_file_name = "%s.%s" % (video_path, Globals.VIDEOS_FILE_TYPE)
        if proc.returncode == 0 and os.path.exists(mp4_file_name):
            logger.info("VideoGenerator", "Video %s generated successfully" % mp4_file_name)
            os.remove(src_dir)
        else:
            logger.error("VideoGenerator", "Failed to generate video %s" % mp4_file_name)
    except BaseException as e:
        logger.error("VideoGenerator", str(e))
    utils.clear_and_remove_dir(dst_dir)


def run():
    for file in find_video_targz_files():
        logger.info("VideoGenerator", "Generating video from %s" % file)
        generate_video_from_targz(file)
        if __name__ == '__main__':
            logger.flush()


if __name__ == '__main__':
    run()
