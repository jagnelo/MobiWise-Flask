import os
# https://sumo.dlr.de/
import traci
import utils


KEY_SUMO_GUI_EXE = "sumo-gui-exe"
KEY_SUMO_PORT = "sumo-port"
KEY_SUMO_NET_FILE = "sumo-net-file"


def sumo_init(args):
    return utils.success_response()


def sumo_load(args):
    return utils.success_response()


def sumo_simulate(args):
    return utils.success_response()


def sumo_close(args):
    return utils.success_response()


KEY_ACTION = "action"
ACTION_INIT = "init"
ACTION_LOAD = "load"
ACTION_SIMULATE = "simulate"
ACTION_CLOSE = "close"


def main(args):
    if KEY_ACTION not in args:
        return utils.error_response("Required argument '" + KEY_ACTION + "' is missing")

    if args[KEY_ACTION] is ACTION_INIT:
        return sumo_init(args)
    if args[KEY_ACTION] is ACTION_LOAD:
        return sumo_load(args)
    if args[KEY_ACTION] is ACTION_SIMULATE:
        return sumo_simulate(args)
    if args[KEY_ACTION] is ACTION_CLOSE:
        return sumo_close(args)

    return utils.error_response("Request action '" + args[KEY_ACTION] + "' is unknown")


if __name__ == '__main__':
    main({})
