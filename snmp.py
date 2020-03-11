from nagios import Check, ReturnValue
import subprocess

def toKeyValue(line):
    if "=" in line:
        newline = line.split(" = ")
        if len(newline) > 1:
            return newline[0], " = ".join(newline[1:])
    return None, line

def isip(text):
    text = text.split(".")
    if len(text) == 4:
        if all(map(str.isdigit, text)):
            text = map(int,text)
            text = map(lambda a: a in range(266),text)
            return all(text)
    return False

def s(text):
    value = str(text)
    value = value.strip()
    return value


class SNMPConfig (object):
    def __init__(self):
        self._version = None
        self._community = None
        self._ip = None
        self._oid = None
        self._protocol = None
        self._passphrase = None
        self._security_engine = None
        self._context_engine = None
        self._level = None
        self._context = None
        self._security_name = None
        self._privacy_protocol = None
        self._privacy_passphrase = None
        self._destination_engine_boots = None
        self._destination_engine_time = None
        self._retries = None
        self._timeout = None
        self._dump_in_hex = None
        self._mibs = None
        self._dir_mibs = None
        self._mibopts = None
        self._outopts = None
        self._inopts = None
        self._logopts = None
        self._appopts = None

    @property
    def v1(self):
        self._version = "1"
        return self

    @property
    def v2c(self):
        self._version = "2c"
        return self

    @property
    def v3(self):
        self._version = "3"
        return self

    def community(self, value):
        self._community = s(value)
        return self

    def ip(self, value):
        value = s(value)
        value = value.strip()
        if isip(value):
            self._ip = value
        return self

    def fqdn(self, value):
        self._ip = s(value)
        return self

    def oid(self, value):
        self._oid = s(value)
        return self

    @property
    def MD5 (self):
        self._protocol = "MD5"
        return self

    @property
    def SHA (self):
        self._protocol = "SHA"
        return self

    def passphrase (self, value):
        self._passphrase = s(value)

    def security_engine(self,value):
        self._security_engine = s(value)
        return self

    def context_engine(self, value):
        self._context_engine = s(value)
        return self

    @property
    def noAuthNoPriv(self):
        self._level = "noAuthNoPriv"
        return self

    @property
    def authNoPriv(self):
        self._level = "authNoPriv"
        return self

    @property
    def authPriv(self):
        self._level = "authPriv"
        return self

    def context(self, name):
        self._context = s(name)
        return self

    def security_name(self, name):
        self._security_name = s(name)

    @property
    def DES(self):
        self._privacy_protocol = "DES"
        return self

    @property
    def AES(self):
        self._privacy_protocol = "AES"
        return self

    def privacy_passphrase(self, password):
        self._privacy_passphrase = s(password)
        return self

    def boots(self, boots):
        self._destination_engine_boots = s(boots)

    def time(self, time):
        self._destination_engine_time = s(time)

    def retries(self, number):
        number = s(number)
        if number.isdigit():
            self._retries = number

    def timeout(self,timeout):
        timeout = s(timeout)
        if timeout.isdigit():
            self._timeout = timeout

    def mibopts(self, mibopts):
        self._mibopts = s(mibopts)
        return self

    def outopts(self, outopts):
        self._outopts = s(outopts)
        return self

    def toList(self):
        res = []
        if self._version:
            res.append("-v{0}".format(self._version))
        if self._version in ["1", "2c"]:
            if self._community:
                res.append("-c")
                res.append(self._community)
        if self._version == "3":
            if self._protocol:
                res.append("-a")
                res.append(self._protocol)
            if self._passphrase:
                res.append("-A")
                res.append(self._passphrase)
            if self._security_engine:
                res.append("-e")
                res.append(self._security_engine)
            if self._context_engine:
                res.append("-E")
                res.append(self._context_engine)
            if self._level:
                res.append("-l")
                res.append(self._level)
            if self._context:
                res.append("-n")
                res.append(self._context)
            if self._security_name:
                res.append("-u")
                res.append(self._security_name)
            if self._privacy_protocol:
                res.append("-x")
                res.append(self._privacy_protocol)
            if self._privacy_passphrase:
                res.append("-X")
                res.append(self._privacy_passphrase)
            if self._destination_engine_boots and self._destination_engine_time:
                res.append("-Z")
                res.append(self._destination_engine_boots+","+self._destination_engine_time)
        if self._retries:
            res.append("-r")
            res.append(self._retries)
        if self._timeout:
            res.append("-t")
            res.append(self._timeout)
        if self._mibopts:
            res.append("-P")
            res.append(self._mibopts)
        if self._outopts:
            res.append("-O")
            res.append(self._outopts)
        if self._ip:
            res.append(self._ip)
        if self._oid:
            res.append(self._oid)
        return res

    def __str__(self):
        return " ".join(self.toList())

    def __call__(self, *args, **kwargs):
        return subprocess.Popen(self.toList(),stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT).communicate()

    def get(self, oid):
        conf = self.oid(oid)
        out, err = subprocess.Popen(["snmpget"] + conf.toList(), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).communicate()
        k, v = toKeyValue(out)
        return v


    def walk(self, oid):
        conf = self.oid(oid)
        out, err = subprocess.Popen(["snmpwalk"] + conf.toList(), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).communicate()
        print(repr(out))
        print(out)
        out = out.split("\n")
        out = filter(len, out)
        res = {}
        for key, value in map(toKeyValue, out):
            res[key] = value

        return res


def snmp(config):
    pass

"""
if __name__ == '__main__':
    conf = SNMPConfig()\
        .v2c\
        .community("public")\
        .context("bla")\
        .authPriv\
        .context_engine("0x80004fb805636c6f75644dab22cc")\
        .fqdn("snmp.live.gambitcommunications.com")\
        .outopts("Q")
    print(conf)
    out = conf.walk("system")
    print(out)
    out = conf.get("SNMPv2-MIB::sysName.0")
    print(out)
"""