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
        remaining_secs = (1/24) - (datetime.datetime.now() - start_time).total_seconds()
        if remaining_secs > 0:
            time.sleep(remaining_secs)
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


@app.route("/api/simulation/replay", methods=["GET"])
def replay():
    if simulation.g_sim_running:
        return utils.error_response("Cannot replay a running simulation"), 400
    return Response(replay_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/simulation/replay/<start>", methods=["GET"])
def replay_start(start):
    if simulation.g_sim_running:
        return utils.error_response("Cannot replay a running simulation"), 400
    if not str(start).isdigit() or (str(start).isdigit() and int(start) < 0):
        return utils.error_response("Parameter <start> must be a positive integer"), 404
    return Response(replay_frames(int(start)), mimetype="multipart/x-mixed-replace; boundary=frame")


def replay_frames(start: int = None):
    frames = available_frames()
    if start is not None and 0 < start < len(frames):
        frames = frames[start:]
    for frame in frames:
        start_time = datetime.datetime.now()
        remaining_secs = (1/24) - (datetime.datetime.now() - start_time).total_seconds()
        if remaining_secs > 0:
            time.sleep(remaining_secs)
        yield b"--frame\r\n"b"Content-Type: image/jpeg\r\n\r\n" + load_frame_by_name(frame) + b"\r\n"


if __name__ == "__main__":
    app.run(port=5000)
