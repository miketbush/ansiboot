import os
import platform
import sys
import base64
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Connector:
    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "GitlabConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, url_command: str, method="get", headers=None, data=None):
        c = url_command
        try:
            if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
                print(url_command)
                result = ""
            else:
                if method == "get":
                    response = requests.get(url_command, headers=headers, data=data)
                else:
                    response = requests.post(url_command, headers=headers, data=data)
                # print(response)
                result = response.json()
        except Exception as ex:
            exc_tuple = sys.exc_info()
            print("Error:" + exc_tuple[1])

        return result

    def play(self, play, variables=None):
        method = "post"
        protocol = "https://"
        vars_suffix = "/api/v4/projects/%%PROJECT_ID%%/variables"
        search_suffix = "/api/v4/search?scope=%%SEARCH_SCOPE%%&search=%%SEARCH_QUERY%%"
        commits_suffix = "/api/v4/projects/%%PROJECT_ID%%/repository/commits?path=%%FILE_NAME%%"
        command_text = None
        headers = None
        each_dict = None

        if "project" in play:
            project_moniker = str(play["project"])
            if not project_moniker.isnumeric():
                vars_suffix = ""
            if isinstance(play["project"], dict):
                if "each" in play["project"]:
                    print(play["project"]["each"])
                    each_dict = variables[play["project"]["each"]]
                    for ek in each_dict:
                        print("each key:" + str(ek))

            if "pipeline-vars" in play:
                vars_suffix = vars_suffix.replace("%%PROJECT_ID%%", project_moniker)
                if play["pipeline-vars"] is None:
                    print("Get All Vars")
                    method = "get"
                    command_text = "https://" + self.parameters["host"] + vars_suffix
                    headers = dict()
                    headers["Authorization"] = self.parameters["auth"]
                    headers["Host"] = self.parameters["host"]
                else:
                    print("GET/SET VARS")
                    vars = play["pipeline-vars"]
                    for v in vars:
                        if isinstance(v, dict):
                            print("SET")
                            for vv in v:
                                print("\t" + vv + " to " + v[vv])
                        else:
                            print("GET " + v)
                            method = "get"
                            command_text = "https://" + self.parameters["host"] + vars_suffix
                            headers = dict()
                            headers["Authorization"] = self.parameters["auth"]
                            headers["Host"] = self.parameters["host"]
            elif "commits" in play:
                print("Get Commits")
                if "file" in play["commits"]:
                    file_name = play["commits"]["file"]
                    print("For file:" + file_name)
                    # commits_suffix = commits_suffix.\
                    #    replace("%%PROJECT_ID%%", project_moniker).\
                    #    replace("%%FILE_NAME%%", file_name)

                    commits_suffix = commits_suffix.replace("%%FILE_NAME%%", file_name)

                    if each_dict is None:
                        commits_suffix = commits_suffix.replace("%%PROJECT_ID%%", project_moniker)

                    method = "get"
                    command_text = "https://" + self.parameters["host"] + commits_suffix
                    headers = dict()
                    headers["Authorization"] = self.parameters["auth"]
                    headers["Host"] = self.parameters["host"]
            else:
                pass
        elif "search" in play:
            if "scope" in play["search"] and "criteria" in play["search"]:
                print(play["search"]["scope"])
                print(play["search"]["criteria"])
                search_suffix = search_suffix. \
                    replace("%%SEARCH_SCOPE%%", play["search"]["scope"]). \
                    replace("%%SEARCH_QUERY%%", play["search"]["criteria"])
                method = "get"
                command_text = "https://" + self.parameters["host"] + search_suffix
                headers = dict()
                headers["Authorization"] = self.parameters["auth"]
                headers["Host"] = self.parameters["host"]
        # if "base64" in play:
        #     base64str = apply_vars(play["base64"])
        #     command_bytes = bytes(base64str, 'utf-8')
        #     command_text = base64.b64decode(command_bytes).decode("utf-8")
        #     if "Windows" in platform.system():
        #         f = open("_t.bat", "w")
        #         if f is not None:
        #             f.write("@echo off\n")
        #             f.write(command_text)
        #             f.flush()
        #             f.close()
        #         command_text = "_t.bat"
        #     else:
        #         command_text = "echo " + base64str + " | base64 -d > _t.sh;chmod +x _t.sh;./_t.sh"
        # else:
        #     command_text = apply_vars(play["command"])

        if each_dict is None:
            result = self.connect(command_text, method,  headers)
        else:
            result = dict()
            for ek in each_dict:
                temp_suffix = command_text.replace("%%PROJECT_ID%%", ek)
                print(temp_suffix)
                result[ek] = self.connect(temp_suffix, method, headers)

        sys.stdout.flush()
        if variables is not None:
            if "as" in play:
                for c in play["as"]:
                    if "pipeline-vars" in play:
                        for gv in result:
                            variables[gv["key"]] = gv["value"]
                    #elif "commits" in play:
                    #    variables[c] = result
                    #    break
                    else:
                        variables[c] = result
        return result

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