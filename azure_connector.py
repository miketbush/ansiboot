import os
import sys


class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "AzureConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, azure_command: str):
        c = """az cloud set --name %%AZURE_ENVIRONMENT%%;\
az login --service-principal -u %%AZURE_PRINCIPLE%% -p %%AZURE_SECRET%% --tenant %%AZURE_TENANT%%;\
az account set --subscription %%AZURE_SUBSCRIPTION%%;%%AZURE_COMMAND%%"""
        c = c.replace("%%AZURE_ENVIRONMENT%%", apply_vars(self.parameters["cloud"]))\
            .replace("%%AZURE_SUBSCRIPTION%%", apply_vars(self.parameters["subscription"]))\
            .replace("%%AZURE_PRINCIPLE%%",apply_vars(self.parameters["principle"]))\
            .replace("%%AZURE_SECRET%%", apply_vars(self.parameters["secret"]))\
            .replace("%%AZURE_TENANT%%", apply_vars(self.parameters["tenant"]))\
            .replace("%%AZURE_COMMAND%%", apply_vars(azure_command))

        if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
            print("AZURE STRING:" + c)
        else:
            os.system(c)

        return c

    def play(self, play):
        command = ""
        content = ""
        tag_name = ""
        tag_value = ""

        processor = "RunPowerShellScript"
        if "processor" in play:
            processor = play["processor"]

        if "script" in play:
            # print("\t\tSCRIPT:" + str(play))
            content = "@" + play["script"]
        elif "command" in play:
            # print("\t\tCOMMAND:" + str(play))
            content = "'" + play["command"] + "'"

        command = "az vm run-command invoke --command-id %%COMMAND_PROCESSOR%%" + \
                  "  --name %%INGEST_NAME%% -g %%RESOURCE_GROUP%% --scripts %%COMMAND_TEXT%%"

        if "tag" in play:
            tag_name = play["tag"]
            tag_value = play["value"]
            command = "az vm update --resource-group $RESOURCE_GROUP --name $INGEST_NAME " + \
                      "--set tags.%%AZURE_TAG_NAME%%=%%AZURE_TAG_VALUE%%"

        command_text = command.replace("%%COMMAND_PROCESSOR%%", processor).\
            replace("%%COMMAND_TEXT%%", content). \
            replace("%%AZURE_TAG_NAME%%", tag_name). \
            replace("%%AZURE_TAG_VALUE%%", tag_value). \
            replace("%%INGEST_NAME%%", play["resource_name"]). \
            replace("%%RESOURCE_GROUP%%", play["resource_group"])

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