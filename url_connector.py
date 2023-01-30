import os
import ssl
import sys
import time
import urllib.request
from urllib.parse import urlparse
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Reporter:

    def __init__(self, debug):
        self.transferred = 0
        self.debug = debug
        self.percent = 0

    def progress(self, chunk_number, chunk_size, total_size):
        if self.debug is not None:
            if self.debug == "verbose":
                self.transferred += chunk_size
                # print(str(transferred) + " of " + str(total_size))
                if total_size - self.transferred > 0:
                    print(str(total_size - self.transferred) + " remaining")
            elif self.debug == "dot":
                self.transferred += chunk_size
                new_percent = int(self.transferred/total_size*100)
                if new_percent > self.percent:
                    self.percent = new_percent
                    print(".", end='')
            elif self.debug == "percent":
                self.transferred += chunk_size
                new_percent = int(self.transferred/total_size*100)
                if new_percent > self.percent:
                    self.percent = new_percent
                    print(str(self.percent) + "%")
            sys.stdout.flush()


class Connector:

    def __init__(self):
        self.parameters = dict()

    def __str__(self):
        return "URLConnector"

    def load(self, *args, **kwargs):
        if isinstance(args, dict):
            # print(args)
            self.parameters = args
        else:
            # print(args[0])
            self.parameters = args[0]

    def download(self, url: str, file_path='', progress: str = None,  attempts=2):
        """Downloads a URL content into a file (with large file support by streaming)

        :param url: URL to download
        :param file_path: Local file name to contain the data downloaded
        :param attempts: Number of attempts
        :return: New file path. Empty string if the download failed
        """
        if not file_path:
            file_path = os.path.realpath(os.path.basename(url))
        url_sections = urlparse(url)
        if not url_sections.scheme:
            # logger.debug('The given url is missing a scheme. Adding http scheme')
            url = f'http://{url}'
            # logger.debug(f'New url: {url}')
        for attempt in range(1, attempts + 1):
            ckc = 0
            try:
                if attempt > 1:
                    time.sleep(10)  # 10 seconds wait time between downloads
                with requests.get(url, stream=True, verify=False) as response:
                    h = response.headers
                    total_size = 0
                    if "Content-Length" in h:
                        total_size = int(h["Content-Length"])
                    response.raise_for_status()
                    with open(file_path, 'wb') as out_file:
                        for chunk in response.iter_content(chunk_size=8192):  # 1MB chunks
                            out_file.write(chunk)
                            if progress is not None:
                                progress(ckc, 8192, total_size)
                                ckc += 1

                    # logger.info('Download finished successfully')
                    return file_path
            except Exception as ex:
                # logger.error(f'Attempt #{attempt} failed with error: {ex}')
                pass
        return ''

    def connect(self, command: str, file: str, debug: str):

        if os.environ.get("ANSIBOOT_DRY_RUN") is not None:
            print("URL STRING:" + command)
        else:
            chunk = 0
            r = Reporter(debug)
            self.download(command, file, attempts=2, progress=r.progress)
            # with urllib.request.urlopen(command, context=ssl.SSLContext()) as url:
            #     meta = url.headers
            #     print("Content-Length:", meta["Content-Length"])
            #     with open(file, 'wb') as f:
            #         b = url.read()
            #
            #         f.write(b)

                # print(url.read())


            #urllib3.request.urlretrieve(command, filename=file, reporthook=r.progress)

        return command

    def play(self, play, variables=None):
        url = None
        debug = None
        if "url" in play:
            url = play["url"]
        if "dest" in play:
            file = play["dest"]
        if "progress" in play:
            debug = play["progress"]

        if url is not None:
            transferred = 0
            command_text = url
            c = self.connect(command_text, file=file, debug=debug)
            print("Transfer Complete.")
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