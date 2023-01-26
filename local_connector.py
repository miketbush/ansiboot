import os
import sys


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
        command_text = apply_vars(play["command"])
        print("==== " + play["name"] + " ====")
        sys.stdout.flush()
        c = self.connect(command_text)
        print("============================\n")
        sys.stdout.flush()

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