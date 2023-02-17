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
        return "UtilConnector"

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

    def walk_keys(self, var, keys, variables, result):

        for vk1 in var:
            item = var[vk1]
            if isinstance(item, dict):
                for key in keys:
                    if key["key"] in item:
                        print("Found Keys")
                        return var
                return self.walk_keys(var[vk1], keys, variables, result)
            else:
                break
        return var
        # for vk in var:
        #     buf = StringIO(str(var[vk]))
        #     for line in buf.readlines():
        #         line = line.strip()
        #         for k in keys:
        #             if line.startswith(k["key"]):
        #                 if vk not in result:
        #                     result[vk] = dict()
        #                 ci = line.index("=")
        #                 ck = line[0:ci].strip()
        #                 cv = line[ci+1:].strip()
        #                 print("ck:" + ck + " cv:" + cv)
        #                 result[vk][ck] = cv
        return result

    def play(self, play, variables=None):
        command_text = ""
        if "config" in play:
            if "var" in play["config"]:
                if "keys" in play["config"]:
                    keys = play["config"]["keys"]
                    var = variables[play["config"]["var"]]
                    if isinstance(var, dict):
                        # print("var is dict")
                        result = dict()
                        # test walk
                        # var = self.walk_keys(var, keys, variables, result)
                        for vk in var:
                            buf = StringIO(str(var[vk]))
                            for line in buf.readlines():
                                line = line.strip()
                                for k in keys:
                                    if line.startswith(k["key"]):
                                        if vk not in result:
                                            result[vk] = dict()
                                        ci = line.index("=")
                                        ck = line[0:ci].strip()
                                        cv = line[ci+1:].strip()
                                        print("ck:" + ck + " cv:" + cv)
                                        result[vk][ck] = cv
                    else:
                        pass
            elif "var" in play["config"]:
                pass
        else:
            pass

        # result = self.connect(command_text)
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