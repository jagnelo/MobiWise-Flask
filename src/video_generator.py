import os
import subprocess
from subprocess import STDOUT, PIPE

import utils
from globals import Globals


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
    dst_dir = os.path.join(Globals.VIDEOS_TARGZ_DIR, file_name)
    utils.unzip_targz(src_dir, dst_dir)
    if os.path.exists(os.path.join(dst_dir, Globals.SNAPSHOTS_DIR)):
        dst_dir = os.path.join(dst_dir, Globals.SNAPSHOTS_DIR)
    snapshots_path = os.path.join(dst_dir, Globals.SNAPSHOTS_FILE_NAME)
    video_path = os.path.join(Globals.VIDEOS_DIR, file_name)
    cmd = Globals.FFMPEG_CMD % (snapshots_path, video_path)
    print("CMD", cmd.split(" "))
    proc = subprocess.Popen(cmd.split(" "), stdout=PIPE, stdin=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    print(stdout.decode().rstrip())
    if stderr:
        print(stderr.decode().rstrip())
    if proc.returncode == 0 and os.path.exists("%s.%s" % (video_path, Globals.VIDEOS_FILE_TYPE)):
        print("FFMPEG TERMINATED OK")
    else:
        print("FFMPEG TERMINATED BADLY")
    utils.clear_and_remove_dir(dst_dir)
