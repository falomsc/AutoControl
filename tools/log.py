import logging
import time


class SSHLogger:
    def __init__(self):
        filename = time.strftime("./log/" + "%Y%m%d_%H%M%S", time.localtime()) + ".log"
        self.logger = logging.getLogger()
        self.logger.setLevel(level=logging.INFO)
        consolehandler = logging.StreamHandler()
        consolehandler.terminator = ""
        filehandler = logging.FileHandler(filename, "a")
        filehandler.terminator = ""
        formatter1 = logging.Formatter(fmt="%(message)s")
        # formatter2 = logging.Formatter(fmt="%(asctime)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        consolehandler.setFormatter(formatter1)
        filehandler.setFormatter(formatter1)
        self.logger.addHandler(consolehandler)
        self.logger.addHandler(filehandler)

    # TODO perfect the function
    def change_filename(self):
        pass

    # TODO perfect the function
    def change_format(self):
        pass