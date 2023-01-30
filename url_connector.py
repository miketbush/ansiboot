import os
import sys
import urllib.request

class Reporter:

    def __init__(self, debug):
        self.transferred = 0
        self.debug = debug
        self.percent = 0

    def progress(self, chunk_number, chunk_size, total_size):
        if self.debug is not None:
            if self.debug == "verbose":
                self.transferred += chunk_size
                # print(str(transferred) + " of " + str(total_size))
                if total_size - self.transferred > 0:
                    print(str(total_size - self.transferred) + " remaining")
            elif self.debug == "dot":
                self.transferred += chunk_size
                new_percent = int(self.transferred/total_size*100)
                if new_percent > self.percent:
                    self.percent = new_percent
                    print(".", end='')
            elif self.debug == "percent":
                self.transferred += chunk_size
                new_percent = int(self.transferred/total_size*100)
                if new_percent > self.percent:
                    self.percent = new_percent
                    print(str(self.percent) + "%")
            sys.stdout.flush()


class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "URLConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, command: str, file: str, debug: str):

        if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
            print("URL STRING:" + command)
        else:
            r = Reporter(debug)
            urllib.request.urlretrieve(command, filename=file, reporthook=r.progress)

        return command

    def play(self, play):
        url = None
        debug = None
        if "url" in play:
            url = play["url"]
        if "dest" in play:
            file = play["dest"]
        if "progress" in play:
            debug = play["progress"]

        if url is not None:
            transferred = 0
            command_text = url
            c = self.connect(command_text, file=file, debug=debug)
            print("Transfer Complete.")
            sys.stdout.flush()

    def get(self, name):
        if name in self.parameters:
            return self.parameters[name]
        else:
            return None


def apply_vars(var_value):
    value = var_value
    if value is None:
        return var_value
    for k, v in os.environ.items():
        rk = "$" + k
        if rk in value:
            value = str(value).replace(rk, v)
    #print(kv + " = " + str(value))
    return value