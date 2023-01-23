# This is a sample Python script.
import os

import yaml

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    #for k, v in os.environ.items():
    #    print("%s=%s" % (k, v))
    #    # Use a breakpoint in the code line below to debug your script.
    with open('c:\\devprojects\\bootstrap.yml', 'r') as file:
        config = yaml.safe_load(file)

    for c in config:
        print(c)
        for kv in c:
            value = c[kv]
            if value is None:
                break
            # print(kv + " = " + value)
            for k, v in os.environ.items():
                rk = "$" + k
                if rk in value:
                    value = str(c[kv]).replace(rk, v)
            print(kv + " = " + value)
            if kv == "command":
                os.system(value)

        print()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')


