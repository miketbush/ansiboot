import os
import sys


class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "AnsibleConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, ansible_command: str):
        c = ansible_command

        if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
            print("ANSIBLE STRING:" + c)
        else:
            os.system(c)


        return c

    def play(self, play):
        command = ""
        processor = "powershell"
        host = os.environ.get("IP_ADDRESS")

        if "processor" in play:
            processor = apply_vars(play["processor"])

        if "host" in play:
            host = apply_vars(play["host"])

        ansible_playbook = "user-provision.yml"
        if "playbook" in play:
            ansible_playbook = apply_vars(play["playbook"])


        c = """ansible-playbook %%ANSIBLE_PLAYBOOK%% -e variable_host=%%HOST%% -e ansible_user=%%ANSIBLE_USER%% -e ansible_password="%%ANSIBLE_PASSWORD%%" -e ansible_become_method=runas -e ansible_become_user=%%ANSIBLE_USER%% -e ansible_winrm_server_cert_validation=ignore -e ansible_connection=winrm -e ansible_shell_type=%%ANSIBLE_PROCESSOR%% -e ansible_shell_executable=None -i %%HOST%%,"""
        c = c.replace("%%ANSIBLE_USER%%", apply_vars(self.parameters["user"]))\
            .replace("%%ANSIBLE_PASSWORD%%", apply_vars(self.parameters["password"]))\
            .replace("%%HOST%%", host) \
            .replace("%%ANSIBLE_PROCESSOR%%", processor) \
            .replace("%%ANSIBLE_PLAYBOOK%%", ansible_playbook)

        command_text = c

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