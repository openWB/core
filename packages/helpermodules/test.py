# class Test:
#     def __init__(self) -> None:
#         self._test = {}


# t1 = Test()
# t2 = Test()
# t1._test["a"] = 5
# print(str(t2._test))

# import json
# from pathlib import Path
# import pathlib
# d = "20211129"
# with open(str(pathlib.Path('../../data/daily_log/'+d+".json")), "r") as jsonFile:
#     print(json.load(jsonFile))


import logging


class MainLogger:
    instance = None
    level_conversion = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}

    def __init__(self):
        if not MainLogger.instance:
            MainLogger.instance = logging.getLogger("main")
            MainLogger.instance.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - {%(pathname)s:%(lineno)s} - %(levelname)s - %(message)s')
            fh = logging.FileHandler(
                '/var/www/html/openWB/ramdisk/main.log')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            MainLogger.instance.addHandler(fh)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def set_log_level(self, level):
        MainLogger.instance.setLevel(self.level_conversion[level])


MainLogger().debug("debug")
MainLogger().info("info")
MainLogger().error("error")
print("change level")
MainLogger().set_log_level(0)
MainLogger().debug("debug")
MainLogger().info("info")
MainLogger().error("error")
