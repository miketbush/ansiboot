# This is a sample Python script.
import os
import sys
import uuid

import yaml

import azure_connector
from azure_connector import Connector


def load_module(module):
    # module_path = "mypackage.%s" % module
    module_path = module

    if module_path in sys.modules:
        return sys.modules[module_path]

    return __import__(module_path, fromlist=[module])


def load_plays(play_file: str) -> dict:

    with open(play_file, 'r') as file:
        config = yaml.safe_load(file)

    playbook   = dict()
    connectors = dict()
    plays      = dict()

    for c in config:
        # print(c)
        try:
            if "connector" in c and c["connector"] is not None:
                try:
                    cname = c["connector"]["name"]
                    # print("connector name:" + cname)
                    conn = load_module(cname)
                    #connectors[cname] = conn
                    # print(conn)
                    cc = conn.Connector()
                    cc.load(c["connector"])
                    connectors[cname] = cc
                    # print(cc)
                    #cc.connect()
                except:
                    print("Cannot load:" + str(c))
            else:
                play = dict()
                for kv in c:
                    play[kv] = apply_vars(c[kv])
                    # print(kv + " = " + str(play[kv]))
                uid = str(uuid.uuid1())
                plays[uid] = play
        except:
            print("Cannot load plays")

    playbook["connectors"] = connectors
    playbook["plays"] = plays
    return playbook


def apply_vars(var_value):
    value = var_value
    if value is None:
        return var_value
    for k, v in os.environ.items():
        try:
            rk = "$" + k
            if rk in value:
                value = str(value).replace(rk, v)
        except:
            pass
    return value


def run_plays(play_file: str):
    pb = load_plays(play_file)
    # print()
    for p in pb["plays"]:
        # print(pb["plays"][p]["name"])
        # print("\t" + pb["plays"][p]["connection"])
        cname = pb["plays"][p]["connection"]
        cc = pb["connectors"][cname]
        cc.play(pb["plays"][p])


def main():

    if len(sys.argv) == 1:
        print("ansiboot-playbook v1.0.0")
        return

    if len(sys.argv) == 2:
        run_plays(sys.argv[1])

    else:
        for arg in sys.argv:
            if arg.startswith("-p"):
                pass


if __name__ == '__main__':
    main()



