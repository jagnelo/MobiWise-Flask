import os
import subprocess

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
    p = None
    try:
        p = subprocess.run(cmd.split(" "), check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(p.stdout.decode().rstrip())
    except subprocess.CalledProcessError as e:
        print("ERROR: ", e)
        if p:
            print(print(p.stderr.decode().rstrip()))
