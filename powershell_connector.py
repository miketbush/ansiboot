import os
import platform
import subprocess
import sys
import base64
from contextlib import redirect_stdout
from io import StringIO


class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "PowershellConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, shell_command: str):
        result = ""
        c = shell_command
        try:
            if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
                print("LOCAL STRING:" + c)
            else:
                #os.system("powershell -command \"" + c + "\"")
                result = subprocess.getoutput("powershell -command \"" + c + "\"")
                print(result)
        except Exception as ex:
            exc_tuple = sys.exc_info()
            print("Error:" + exc_tuple[1])
        return result

    def play(self, play, variables=None):
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
            command_text = apply_vars(play["command"], variables=variables)

        result = self.connect(command_text)
        sys.stdout.flush()

        if variables is not None:
            if "as" in play:
                for c in play["as"]:
                    variables[c] = result

    def get(self, name):
        if name in self.parameters:
            return self.parameters[name]
        else:
            return None


def apply_vars(var_value, variables=None):
    value = var_value
    if value is None:
        return var_value
    for k, v in os.environ.items():
        rk = "$" + k
        if rk in value:
            value = str(value).replace(rk, v)

    if variables is not None:
        for k in variables:
            rk = "$var:" + k
            v = variables[k]
            if rk in value:
                value = str(value).replace(rk, str(v))

    #print(kv + " = " + str(value))
    return value