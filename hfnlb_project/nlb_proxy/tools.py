import socket, os, re, datetime
from threading import Thread

from django.conf import settings

def validateIP(address):
    if re.search('^[0-9]*$', address):
        return False
    try:
        # print("address %s is a ip!" % address)
        socket.inet_aton(address)
        return True
    except:
        return False

def validatePort(port):
    if re.search('[1-9][0-9]+',str(port)):
        port_number = int(port)
        if port_number < 65535:
            return True
    return False

def validateSubnet(subnet):
    tmp_l = subnet.split('/')
    if len(tmp_l) != 2:
        return False

    if not validateIP(tmp_l[0]):
        return False

    try:
        subnet_mask_len = int(tmp_l[1])
    except:
        return False

    if subnet_mask_len < 0 or subnet_mask_len > 32:
        return False
    return True

def static_render(template_name):
    root_dir= os.path.join(settings.BASE_DIR, 'nlb_proxy/static')
    file_name = os.path.join(root_dir, template_name)
    if os.path.isfile(file_name):
        return open(file_name).read()
    else:
        return "ERROR: Static template not exist: %s" % file_name

def unique_list_elements(l):
    new_list = []
    for i in l:
        if i not in new_list:
            new_list.append(i)
    return new_list

class InitException(Exception):
    pass

class Logging(object):
    def __init__(self, log_file, log_prefix=None):
        self.log_file = log_file
        self.log_path = os.path.dirname(log_file)
        if not self.log_path:
            raise InitException('ERROR: Log path cannot be empty!')
        if not os.path.isdir(self.log_path):
            os.makedirs(self.log_path)
        self.f_obj = open(self.log_file, 'a')
        self.log_prefix = log_prefix

    def log(self,record_line):
        if self.log_prefix:
            log_line = "%s [%s] %s\n" % (datetime.datetime.now().strftime('%F %T'), self.log_prefix, record_line)
        else:
            log_line = "%s %s\n" % (datetime.datetime.now().strftime('%F %T'), record_line)
        self.f_obj.write(log_line)
        self.f_obj.flush()

class MyThread(Thread):
    def __init__(self, works):
        self.works = works
        self.works_return = None
        super().__init__()

    def run(self):
        self.works_return = self.works()
