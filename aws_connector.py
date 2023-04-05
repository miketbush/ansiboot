import base64
import os
import sys
import time

class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "AWSConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def connect(self, aws_command: str):
        c = "export AWS_ACCESS_KEY_ID=%%AWS_ACCESS_KEY_ID%%;" + \
            "export AWS_SECRET_ACCESS_KEY=%%AWS_SECRET_ACCESS_KEY%%;" + \
            "export AWS_DEFAULT_REGION=%%AWS_DEFAULT_REGION%%;" + \
            "export AWS_PAGER=\\\"\\\"; %%AWS_COMMAND%%"

        c = c.replace("%%AWS_ACCESS_KEY_ID%%",apply_vars(self.parameters["accessid"]))\
            .replace("%%AWS_SECRET_ACCESS_KEY%%", apply_vars(self.parameters["accesskey"]))\
            .replace("%%AWS_DEFAULT_REGION%%", apply_vars(self.parameters["region"])) \
            .replace("%%AWS_COMMAND%%", aws_command)

        if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
            print("AWS STRING:" + c)
        else:
            os.system(c)
            time.sleep(15)

        return c

    def play(self, play, variables=None):
        command = ""
        content = ""
        tag_name = ""
        tag_value = ""

        processor = "AWS-RunPowerShellScript"
        if "processor" in play:
            processor = play["processor"]

        if "script" in play:
            # print("\t\tSCRIPT:" + str(play))
            encoded_string = ""
            if play["destination"] is not None:
                dest = play["destination"]
            with open(play["script"], "rb") as script_file:
                encoded_string = base64.b64encode(script_file.read())
            #print("encoded_string:" + encoded_string.decode())

            if processor == "AWS-RunPowerShellScript":
                content = "$text=\\\"" + encoded_string.decode() + "\\\";" + \
                          "[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($text)) | " + \
                          "Out-File -Force -Encoding ascii " + dest + ";& " + dest
            else:
                content = "text=\\\"" + encoded_string.decode() + "\\\";" + \
                          "(echo $text | base64 -d) > " + dest + ";chmod +x " + dest + ";" + \
                          "sh " + dest
            command  = "aws ssm send-command --document-name \"%%COMMAND_PROCESSOR%%\"" + \
                       " --parameters 'commands=[\"%%COMMAND_TEXT%%\"]' " + \
                       " --targets \"Key=tag:Name,Values=%%INGEST_NAME%%\""
                       #" --targets \"Key=instanceids,Values=%%INGEST_NAME%%\""

        elif "command" in play:
            # print("\t\tCOMMAND:" + str(play))
            content =  play["command"]
            command  = "aws ssm send-command --document-name \"%%COMMAND_PROCESSOR%%\"" + \
                       " --parameters 'commands=[\"%%COMMAND_TEXT%%\"]' " + \
                       " --targets \"Key=tag:Name,Values=%%INGEST_NAME%%\""
                       #" --targets \"Key=instanceids,Values=%%INGEST_NAME%%\""

        elif "addrole" in play:
            command = "aws ec2 associate-iam-instance-profile --instance-id %%INGEST_NAME%% --iam-instance-profile "
            if play["addrole"].startswith("arn:"):
                command = command + " Arn=" + play["addrole"]
            else:
                command = command + " Name=" + play["addrole"]

        elif "tag" in play:
            tag_name = play["tag"]
            tag_value = play["value"]
            #aws ec2 create-tags --resources i-0fdb4515295e6af61 --tags Key=IngestTest,Value="Automation Added"
            command = "aws ec2 create-tags --resources %%INGEST_NAME%% " + \
                      "--tags Key=%%TAG_NAME%%,Value=%%TAG_VALUE%%".replace("%%TAG_NAME%%", tag_name).\
                      replace("%%TAG_VALUE%%", tag_value)

        command_text = command.replace("%%COMMAND_PROCESSOR%%", processor). \
                               replace("%%COMMAND_TEXT%%", content). \
                               replace("%%INGEST_NAME%%", play["resource_name"])

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