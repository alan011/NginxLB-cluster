#!/usr/local/bin/python3

import os, sys, django, time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../'))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.settings" % os.path.basename(BASE_DIR))
django.setup()

from nlb_proxy.daemon.init_handler import ServerInitHandler
from nlb_proxy.daemon.apply_handler import ApplyHandler
from nlb_proxy.daemon.health_check import MinionHealthCheck
from nlb_proxy.tools import Logging
from nlb_proxy import config
# from multiprocessing import Process
from threading       import Thread

class NLBDaemon(object):
    interval = config.TIMER_RUNTIME_INTERVAL

    def __init__(self):
        self.pool = {'server_init':None, 'manage_keys':None, 'health_check':None, 'apply_config': None}
        self.log_file = os.path.join(config.TIMER_LOG_PATH, 'nlb_timer.log')
        self.logger = Logging(self.log_file, 'NLBDaemon')

    def worker(self, name, func):
        if name in self.pool:
            if self.pool[name]  and  self.pool[name].is_alive():
                pass
                # self.logger.log("Subprocess of '%s' is not ending. Ignored it at this runtime." % name)
            else:
                # self.pool[name] = Process(target=func)
                self.pool[name] = Thread(target=func)
                self.pool[name].start()

    def run(self):
        while True:
            server_init = ServerInitHandler(self.log_file)
            apply_handler = ApplyHandler(self.log_file)
            health_check = MinionHealthCheck(self.log_file)

            self.worker('server_init',server_init.serverInit)
            self.worker('manage_keys',server_init.acceptKeys)
            self.worker('apply_config',apply_handler.applyHandler)
            self.worker('health_check',health_check.healthCheck)

            time.sleep(self.interval)


if __name__ == '__main__':
    daemon = NLBDaemon()
    daemon.run()
