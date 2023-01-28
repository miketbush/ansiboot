# This is a sample Python script.
import os
import shutil
import sys
import uuid
import zipfile
from zipfile import ZipFile

import yaml

import azure_connector
from azure_connector import Connector

BANNER_WIDTH = 156


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

    connectors["local_connector"] = load_module("local_connector").Connector()
    connectors["local_connector"] .load(dict())

    for c in config:
        # print(c)
        try:
            if "connector" in c and c["connector"] is not None:
                try:
                    # cname = c["connector"]["name"]
                    cc, cname = load_connector(c)
                    connectors[cname] = cc
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


def load_connector(c):

    if "type" not in c["connector"]:
        print("Connector invalid:" + str(c))
        return

    if "name" not in c["connector"]:
        cname = c["connector"]["type"]
    else:
        cname = c["connector"]["name"]

    tname = c["connector"]["type"]

    # print("connector name:" + cname)
    conn = load_module(tname)
    # connectors[cname] = conn
    # print(conn)
    cc = conn.Connector()
    cc.load(c["connector"])
    return cc, cname


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


def get_xfix_size(text: str):
    if len(text) > 40:
        text = text[0:39]
    pname_len = len(text)
    if pname_len % 2 > 0:
        pname_len = pname_len + 1
        text += " "

    prefix_size = int((BANNER_WIDTH - pname_len - 2) / 2)
    return prefix_size, text


def print_banner(pname: str):
    prefix_size, pname = get_xfix_size(pname)
    header = ("=" * prefix_size) + " " + pname + " " + ("=" * prefix_size)
    print(header)
    sys.stdout.flush()
    return header


def process_plays(pb):
    for p in pb["plays"]:
        # print(pb["plays"][p]["name"])
        # print("\t" + pb["plays"][p]["connection"])
        if "connection" in pb["plays"][p]:
            cname = pb["plays"][p]["connection"]
        else:
            cname = "local_connector"

        try:
            cc = pb["connectors"][cname]
        except:
            cc = None

        pname = pb["plays"][p]["name"]

        header = print_banner(pname)

        if cc is not None:
            print_banner(cname)
            cc.play(pb["plays"][p])
        else:
            print("Error: Connector Not Found")
            sys.stdout.flush()

        footer = "=" * len(header) + "\n"
        print(footer)
        sys.stdout.flush()


def create_abs(create_file, source_dir):
    zipdir(source_dir, create_file)


def zipdir(path, create_file):
    # ziph is zipfile handle
    ziph = zipfile.ZipFile(create_file, "w")
    for root, dirs, files in os.walk(path):
        for file in files:
            #ziph.write(os.path.join(root, file),
            #           os.path.relpath(os.path.join(root, file),
            #                           os.path.join(path, '..')))
            ziph.write(os.path.join(root, file), file)


def run_plays(play_file: str):
    current_dir = os.getcwd()
    if play_file.endswith(".abs"):
        base_name = os.path.basename(play_file)
        print("Processing Compressed Bootstrap " + base_name + " in " + current_dir)
        new_dir = current_dir + os.path.sep + base_name.replace(".abs", ".run")
        # print(new_dir)
        try:
            shutil.rmtree(new_dir)
        except:
            pass
        os.mkdir(new_dir)
        with ZipFile(play_file, 'r') as compressed_plays:
            for f in compressed_plays.filelist:
                print("\t" + f.filename)
            compressed_plays.extractall(new_dir)
        compressed_plays.close()
        os.chdir(new_dir)
        print(os.getcwd())

        pb = load_plays("bootstrap.yml")
        process_plays(pb)

        os.chdir(current_dir)
        print(os.getcwd())
    else:
        pb = load_plays(play_file)
        process_plays(pb)

    # for p in pb["plays"]:
    #     # print(pb["plays"][p]["name"])
    #     # print("\t" + pb["plays"][p]["connection"])
    #     cname = pb["plays"][p]["connection"]
    #     cc = pb["connectors"][cname]
    #     cc.play(pb["plays"][p])



def main():

    if len(sys.argv) == 1:
        print("ansiboot-playbook v1.0.0")
        return

    if len(sys.argv) == 2:
        run_plays(sys.argv[1])
    elif len(sys.argv) == 5:
        create = ""
        dir = ""
        if "-d" in sys.argv and "-f" in sys.argv:
            for index, arg in enumerate(sys.argv):
                if arg.startswith("-f"):
                    create = sys.argv[index+1]
                elif arg.startswith("-d"):
                    dir = sys.argv[index+1]
            print("create " + create + " from dir: " + dir)
            create_abs(create, dir)


if __name__ == '__main__':
    main()



