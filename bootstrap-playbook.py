# This is a sample Python script.
import inspect
import os
import shutil
import sys
import time
import uuid
import zipfile
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
import urllib3
import yaml

import azure_connector
from azure_connector import Connector
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    vars       = dict()

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
                    print(sys.exc_info())
                    print("Cannot load:" + str(c))
            elif "variables" in c and c["variables"] is not None:
                try:
                    for v in c["variables"]:
                        vars[v] = c["variables"][v]
                except:
                    pass
            else:
                try:
                    play = dict()
                    for kv in c:
                        play[kv] = apply_vars(c[kv])
                        # print(kv + " = " + str(play[kv]))
                    uid = str(uuid.uuid1())
                    plays[uid] = play
                except:
                    pass
        except:
            print("Cannot load plays")

    playbook["connectors"] = connectors
    playbook["plays"] = plays
    playbook["variables"] = vars
    return playbook


def download(url: str, file_path='', progress: str = None,  attempts=2):
    """Downloads a URL content into a file (with large file support by streaming)

    :param url: URL to download
    :param file_path: Local file name to contain the data downloaded
    :param attempts: Number of attempts
    :return: New file path. Empty string if the download failed
    """
    if not file_path:
        file_path = os.path.realpath(os.path.basename(url))
    url_sections = urlparse(url)
    if not url_sections.scheme:
        # logger.debug('The given url is missing a scheme. Adding http scheme')
        url = f'http://{url}'
        # logger.debug(f'New url: {url}')
    for attempt in range(1, attempts + 1):
        ckc = 0
        try:
            if attempt > 1:
                time.sleep(10)  # 10 seconds wait time between downloads
            with requests.get(url, stream=True, verify=False) as response:
                h = response.headers
                total_size = 0
                if "Content-Length" in h:
                    total_size = int(h["Content-Length"])
                response.raise_for_status()
                with open(file_path, 'wb') as out_file:
                    for chunk in response.iter_content(chunk_size=8192):  # 1MB chunks
                        out_file.write(chunk)
                        if progress is not None:
                            progress(ckc, 8192, total_size)
                            ckc += 1

                # logger.info('Download finished successfully')
                return file_path
        except Exception as ex:
            # logger.error(f'Attempt #{attempt} failed with error: {ex}')
            pass
    return ''


def load_connector(c):
    connector = c["connector"]
    # if "type" not in c["connector"]:
    #     print("Connector invalid:" + str(c))
    #     return
    for cv in connector:
        # print("before:" + connector[cv])
        if connector[cv] is not None:
            if not isinstance(connector[cv], dict):
                connector[cv] = apply_vars(connector[cv])
            else:
                print(connector[cv])

    if "url" in connector:
        uid = uuid.uuid1()
        cls = "connector_" + str(uid).replace("-", "")
        download_type = (cls + ".py")
        connector["download_file"] = download(file_path=download_type, url=connector["url"])
        connector["type"] = cls
        connector["downloaded"] = True
    else:
        if "type" not in connector:
            print("Connector invalid:" + str(c))
            return

    if "name" not in connector:
        cname = connector["type"]
    else:
        cname = connector["name"]

    t_name = connector["type"]

    conn = load_module(t_name)

    cc = conn.Connector()
    cc.load(connector)
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

        run_a_play(pb, p)

        # if "connection" in pb["plays"][p]:
        #     cname = pb["plays"][p]["connection"]
        # else:
        #     cname = "local_connector"
        #
        # try:
        #     cc = pb["connectors"][cname]
        # except:
        #     cc = None
        #
        # pname = pb["plays"][p]["name"]
        #
        # header = print_banner(pname)
        #
        # if cc is not None:
        #     print_banner(cname)
        #     current_play = pb["plays"][p]
        #     if "plays" in inspect.signature(cc.play).parameters:
        #         cc.play(play=current_play, variables=pb["variables"], plays=pb["plays"])
        #     else:
        #         cc.play(play=current_play, variables=pb["variables"])
        # else:
        #     print("Error: Connector Not Found")
        #     sys.stdout.flush()
        #
        # footer = "=" * len(header) + "\n"
        # print(footer)
        # sys.stdout.flush()


def run_a_play_by_name(pb, name):
    for p in pb["plays"]:
        play = pb["plays"][p]
        if name == play["name"]:
            # print("FOUND THAT PLAY!!")
            run_a_play(pb, p, called=True)


def run_a_play(pb, p, called=False):

    if "connection" in pb["plays"][p]:
        cname = pb["plays"][p]["connection"]
    else:
        cname = "local_connector"

    try:
        cc = pb["connectors"][cname]
    except:
        cc = None

    ignore = False

    try:
        if not called:
            ignore = bool(pb["plays"][p]["ignore"])
    except:
        ignore = False

    pname = pb["plays"][p]["name"]

    if not called and not ignore:
        header = print_banner(pname)

    if cc is not None:

        if not called and not ignore:
            print_banner(cname)

        current_play = pb["plays"][p]

        if not ignore:
            if "plays" in inspect.signature(cc.play).parameters:
                #cc.play(play=current_play, variables=pb["variables"], plays=pb["plays"])
                cc.play(play=current_play, variables=pb["variables"], plays=lambda name: run_a_play_by_name(pb, name))
            else:
                cc.play(play=current_play, variables=pb["variables"])

    else:
        print("Error: Connector Not Found")
        sys.stdout.flush()

    if not called and not ignore:
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
        for c in pb["connectors"]:
            cc = pb["connectors"][c]
            if cc.get("downloaded") is not None:
                if cc.get("downloaded") is True:
                    os.remove(cc.get("download_file"))


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



