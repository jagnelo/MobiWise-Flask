from flask import Flask, Response
import os
import simulation
import datetime
import time
import utils

app = Flask(__name__)


@app.route("/")
def index():
    pass


@app.route("/api/simulation/run", methods=["POST"])
def simulate():
    simulation.run_default()
    return utils.success_response("Simulation finished"), 200


@app.route("/api/simulation/stream", methods=["GET"])
def stream():
    if not simulation.g_sim_running:
        return utils.error_response("Cannot stream a non-running simulation"), 400
    return Response(stream_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


def stream_frames():
    while simulation.g_sim_running:
        start_time = datetime.datetime.now()
        last = last_frame()
        remaining_secs = (1/30) - (datetime.datetime.now() - start_time).total_seconds()
        if remaining_secs > 0:
            time.sleep(remaining_secs)
        # print("[curr %s] remaining_secs %f" % (last, remaining_secs))
        yield b"--frame\r\n"b"Content-Type: image/jpeg\r\n\r\n" + load_frame_by_name(last) + b"\r\n"


def is_frame_available(name: str):
    return os.path.exists(os.path.join("output", name))


def available_frames():
    return sorted([f for f in os.listdir("output") if f.endswith(".jpg")])


def last_frame():
    return available_frames()[-1]


def step_from_name(name: str):
    return int("".join(filter(str.isdigit, name)))


def load_frame_by_name(name: str):
    with open(os.path.join("output", name), "rb") as fd:
        return fd.read()


def load_frame_by_step(step: int):
    return load_frame_by_name(simulation.g_img_name % step)


def get_frames():
    i = 1
    last_frame = None
    while simulation.g_sim_running or i <= simulation.g_sim_step:   # simulation.g_sim_step resets to 0 and this ends
        file_name = simulation.g_img_name % i
        file_path = os.path.join("output", file_name)
        sleep_secs = simulation.g_sim_delta_secs if simulation.g_sim_running else 1 / 30
        while not os.path.exists(file_path):
            print("Waiting for file %s to be created..." % file_name)
            if last_frame is not None:
                yield b"--frame\r\n"b"Content-Type: image/jpeg\r\n\r\n" + last_frame + b"\r\n"
            time.sleep(sleep_secs)
        start_time = datetime.datetime.now()
        with open(file_path, "rb") as fd:
            frame = fd.read()
            last_frame = bytes(frame)
            delta_secs = (datetime.datetime.now() - start_time).total_seconds()
            remaining_secs = sleep_secs - delta_secs
            if remaining_secs > 0:
                time.sleep(remaining_secs)
            print("[step %d, file %s] remaining_secs %f" % (i, file_name, remaining_secs))
            yield b"--frame\r\n"b"Content-Type: image/jpeg\r\n\r\n" + last_frame + b"\r\n"
        i += 1


if __name__ == "__main__":
    app.run(port=8000)
