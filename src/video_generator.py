import os

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
    files_in_dst = os.listdir(dst_dir)
    if len(files_in_dst) == 1 and os.path.isdir(os.path.join(dst_dir, files_in_dst[0])):
        snapshots_dir = os.path.join(dst_dir, files_in_dst[0])
        video_name = "%s.%s" % (file_name, Globals.VIDEOS_FILE_TYPE)
        path = os.path.join(snapshots_dir, Globals.SNAPSHOTS_FILE_NAME)
        videos_dir = os.path.join(Globals.VIDEOS_DIR, video_name)
        return Globals.FFMPEG_CMD % (path, videos_dir)

