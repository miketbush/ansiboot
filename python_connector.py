import os
import platform
import sys
import base64
from io import StringIO
import contextlib


def call_play_internal(name: str, play_caller):
    # print("call_play:" + name)
    play_caller(name)
    sys.stdout.flush()


class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "PythonConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, shell_command: str, variables=None, plays=None):
        result = ""
        c = shell_command
        try:
            if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
                print("LOCAL STRING:" + c)
            else:
                with stdoutIO() as s:
                    try:
                        # call_play=lambda name: call_play_internal(name, plays)
                        exec(c, {"variables": variables, "call_play": lambda name: call_play_internal(name, plays)})
                    except:
                        print("Something wrong with the code")
                print(s.getvalue())
        except Exception as ex:
            exc_tuple = sys.exc_info()
            print("Error:" + exc_tuple[1])
        return result

    def play(self, play, variables=None, plays=None):
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
            command_text = apply_vars(play["script"], variables=variables)

        result = self.connect(command_text, variables=variables, plays=plays)
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

    # print(kv + " = " + str(value))
    return value

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old



