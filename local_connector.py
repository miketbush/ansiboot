import os
import platform
import sys
import base64

class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "LocalConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]


    def connect(self, shell_command: str):
        c = shell_command
        #print("LOCAL STRING:" + c)
        # if "desc" in self.parameters:
        #    print(self.parameters["desc"] + ":")
        #    sys.stdout.flush()
        try:
            if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
                print("LOCAL STRING:" + c)
            else:
                os.system(c)
        except:
            exc_tuple = sys.exc_info()
            print("Error:" + exc_tuple[1])
        return c

    def play(self, play):
        if "base64" in play:
            base64str = apply_vars(play["base64"])
            command_bytes = bytes(base64str, 'utf-8')
            command_text = base64.b64decode(command_bytes).decode("utf-8")
            if "Windows" in platform.system():
                f = open("_t.bat", "w")
                if f is not None:
                    f.write("@echo off\n")
                    f.write(command_text)
                    f.flush()
                    f.close()
                command_text = "_t.bat"
            else:
                command_text = "echo " + base64str + " | base64 -d > _t.sh;chmod +x _t.sh;./_t.sh"
        else:
            command_text = apply_vars(play["command"])

        c = self.connect(command_text)
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