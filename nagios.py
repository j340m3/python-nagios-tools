# coding=utf-8
import sys
import argparse
import itertools


def gen_parser(description, community=False, authentication=False, logname=False, password=False, port=False, url=False, username=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-v", "--verbose", help="Set verbosity level (0-3). Default 0", default=0)
    parser.add_argument("-w", "--warning", nargs='+', help="Set warning range(s).", action="append")
    parser.add_argument("-c", "--critical", nargs='+', help="Set critical range(s).", action="append")
    parser.add_argument("-t", "--timeout", help="Set timeout in seconds. Default 60 seconds.", default=60)
    parser.add_argument("-V", "--version", help="Display plugin version.")
    parser.add_argument("-H", "--hostname", help="The hostname of the client to check")
    if community:
        parser.add_argument("-C", "--community", help="Set SNMP community. Default 'public'.", default="public")
    if authentication:
        parser.add_argument("-a","--authentication", help="Authentication password")
    if logname:
        parser.add_argument("-l","--logname",help="The login name used for authentication.")
    if password and not port:
        parser.add_argument("-p", "--passwd","--password" , help="The password used for authentication.")
    elif port and not password:
        parser.add_argument("-p", "--port", help="The port of the client to run the check on.")
    elif port and password:
        parser.add_argument("--password", "--passwd", help="The password used for authentication.")
        parser.add_argument("--port", help="The port of the client to run the check on.")
    if username and not url:
        parser.add_argument("-u", "--username", help="The username.")
    elif url and not username:
        parser.add_argument("-u", "--url", help="The url to check.")
    elif url and username:
        parser.add_argument("--username", help="The username.")
        parser.add_argument("--url", help="The url to check.")
    return parser

def yield_from(iterator):
    for i in iterator:
        yield i

def get_pairs(warning, critical):
    w_flattened = list(itertools.chain.from_iterable(warning))
    c_flattened = list(itertools.chain.from_iterable(critical))
    if len(w_flattened) == len(c_flattened):
        yield_from(zip(w_flattened, c_flattened))
    elif len(w_flattened) == 1 and len(c_flattened) > 1:
        for warn, crit in zip(itertools.repeat(w_flattened[0]), c_flattened):
            yield warn, crit
    elif len(w_flattened) > 1 and len(c_flattened) == 1:
        for warn, crit in zip(w_flattened, itertools.repeat(c_flattened[0])):
            yield warn, crit
    elif len(w_flattened) > len(c_flattened) and len(w_flattened) % len(c_flattened) == 0:
        for warn, crit in zip(itertools.cycle(w_flattened), c_flattened):
            yield warn, crit
    elif len(c_flattened) > len(w_flattened) and len(c_flattened) % len(w_flattened) == 0:
        for warn, crit in zip(w_flattened, itertools.cycle(c_flattened)):
            yield warn, crit
    else:
        raise ValueError("Could not build pairs from the command line argument")


def get_range(nrange):
    out = []
    if nrange.count(":") == 1:
        w = nrange.split(":")
        w = list(map(str.strip, w))
        if w[0] == "~" and w[1].isdigit():
            out.append(Range(low=int(w[1])))
        elif len(w[1]) == 0:
            out.append(Range(high=int(w[0])))
        elif w[0].isdigit() and w[1].isdigit():
            wmin = int(w[0])
            wmax = int(w[1])
            if wmin <= wmax:
                out.append(Range(high=wmin))
                out.append(Range(low=wmax))
            else:
                raise ValueError("Error parsing \"{}\": "
                                 "the start variable (here: {}) has to be "
                                 "smaller or equal to the end variable (here: {}".format(nrange, wmin, wmax))
        elif w[0][0] == "@":
            w[0] = w[0][1:]
            if w[0] == "~" and w[1].isdigit():
                out.append(Range(high=int(w[1])))
            elif len(w[1]) == 0:
                out.append(Range(low=int(w[0])))
            elif w[0].isdigit() and w[1].isdigit():
                wmin = int(w[0])
                wmax = int(w[1])
                if wmin <= wmax:
                    out.append(Range(low=wmin, high=wmax, low_incl=True, high_incl=True))
                else:
                    raise ValueError("Error parsing \"{}\": "
                                     "the start variable (here: {}) has to be "
                                     "smaller or equal to the end variable (here: {}".format(nrange, wmin, wmax))
    elif nrange.count(":") == 0:
        nrange = nrange.strip()
        if nrange[0] == "@":
            if nrange[1:].isdigit():
                out.append(Range(low=0, high=int(nrange[1:]), low_incl=True, high_incl=True))
            else:
                raise ValueError("Error parsing \"{}\": {} is not a number!".format(nrange, nrange[1:]))
        else:
            if nrange.isdigit():
                out.append(Range(high=0))
                out.append(Range(low=int(nrange)))
            else:
                raise ValueError("Error parsing \"{}\": {} is not a number!".format(nrange, nrange[1:]))
    elif nrange.count(":") > 2:
        raise ValueError("Error parsing \"{}\": Too much colons ({} > 1) found!".format(nrange, len(nrange.split(":"))))
    return out


def parse(warning=None, critical=None):
    if not critical:
        if warning:
            w_flattened = itertools.chain.from_iterable(warning)
            for i in w_flattened:
                warn = get_range(i)
                yield Threshold(warning=warn)
    elif not warning:
        if critical:
            c_flattened = itertools.chain.from_iterable(critical)
            for i in c_flattened:
                crit = get_range(i)
                yield Threshold(critical=crit)
    else:
        for warn, crit in get_pairs(warning, critical):
            warn = get_range(warn)
            crit = get_range(crit)
            yield Threshold(warning=warn, critical=crit)


class Range(object):
    def __init__(self, low=None, low_incl=False, high=None, high_incl=False):
        self.low = low
        self.high = high
        self.low_incl = low_incl
        self.high_incl = high_incl

    def inside(self, value):
        if self.low is not None:
            if self.low > value:
                return False
            elif self.low_incl is False and self.low == value:
                return False
        if self.high is not None:
            if self.high < value:
                return False
            elif self.high_incl is False and self.high == value:
                return False
        return True

    def __str__(self):
        out = ""
        if self.low_incl:
            out += "["
        else:
            out += "("
        if self.low:
            out += str(self.low)
        else:
            out += "-∞"
        out += ", "
        if self.high:
            out += str(self.high)
        else:
            out += "∞"
        if self.high_incl:
            out += "]"
        else:
            out += ")"
        return out

    def __repr__(self):
        return "Range: <{}>".format(str(self))


class Threshold(object):
    OK = "0"
    WARNING = "1"
    CRITICAL = "2"
    UNKNOWN = "3"

    def __init__(self, critical=None, warning=None):
        self.critical = critical
        self.warning = warning
        if self.critical is None:
            self.critical = []
        if self.warning is None:
            self.warning = []

    def state(self, value):
        try:
            for i in self.critical:
                if i.inside(value):
                    return self.CRITICAL
            for i in self.warning:
                if i.inside(value):
                    return self.WARNING
            return self.OK
        except Exception as e:
            return self.UNKNOWN


class Output(object):
    def __init__(self, service, output_lines=None, performance_data=None):
        self.service = service
        self.output_lines = output_lines
        if self.output_lines is None:
            self.output_lines = []
        self.performance_data = performance_data
        if self.performance_data is None:
            self.performance_data = []

    def ok(self):
        print(self.format_output("OK"))
        sys.exit(0)

    def warning(self):
        print(self.format_output("Warning"))
        sys.exit(1)

    def critical(self):
        print(self.format_output("Critical"))
        sys.exit(2)

    def unknown(self):
        print(self.format_output("Unknown"))
        sys.exit(3)

    def format_output(self, state):
        try:
            first_line = ""
            if self.service:
                first_line += self.service.upper() + " "
            else:
                raise NameError("Cannot create output format for an Output class when the *service* variable is empty!")
            first_line += state
            first_line += ": "
            if len(self.output_lines) > 0:
                first_line += self.output_lines[0]
            if len(self.performance_data) > 0:
                first_line += " | " + self.performance_data[0].format()
            first_line += "\n"
            if len(self.output_lines) > 1:
                first_line += "\n".join(self.output_lines[1:])
            if len(self.performance_data) > 1:
                first_line += " | "
                first_line += "\n".join(map(PerformanceData.format, self.performance_data[1:]))
            return first_line
        except Exception as e:
            print("Error Unknown: {0}".format(str(e)))
            sys.exit(3)


class PerformanceData(object):
    def __init__(self, label=None, value=None, uom=None, warn=None, crit=None, min_=None, max_=None):
        self.label = label
        self.value = value
        self.uom = uom
        self.warn = warn
        self.crit = crit
        self.min = min_
        self.max = max_

    def format(self):
        if not self.label:
            raise NameError(
                "Cannot create the output format the performance data when the *label* variable is not set!")
        elif not self.value:
            raise NameError(
                "Cannot create the output format the performance data when the *value* variable is not set!")
        else:
            out = "'{0}'={1}".format(self.label, self.value)
            if self.uom and self.uom in ["s", "us", "ms", "%", "B", "KB", "MB", "TB", "c"]:
                out += self.uom
            if self.warn:
                out += ";"
                out += self.warn
            if self.crit:
                out += ";"
                out += self.crit
            if self.min:
                out += ";"
                out += self.min
            if self.max:
                out += ";"
                out += self.max
            return out


class Check(object):
    def __init__(self, name, description=None, uom=None):
        self.name = name
        self.description = description
        self.uom = uom

    def __call__(self, *args, **kwargs):
        self.run(**self.cli_args)

    def output(self, return_values, out_lines):
        if return_values is None:
            Output(service=self.name, output_lines=["Got no values to return."] + out_lines).unknown()
        else:
            perfdata = []
            state = Threshold.OK
            for value, threshold, pair in zip(return_values, itertools.cycle(self.thresholds), itertools.cycle(self.pairs)):
                warn, crit = pair
                perfdata.append(
                    PerformanceData(label=value.label, value=value.value, uom=self.uom, crit=crit, warn=warn))
                if threshold.state(value.value) > state:
                    state = threshold.state(value.value)
            output = Output(service=self.name, output_lines=out_lines, performance_data=perfdata)
            if state is Threshold.OK:
                output.ok()
            elif state is Threshold.WARNING:
                output.warning()
            elif state is Threshold.CRITICAL:
                output.critical()
            elif state is Threshold.UNKNOWN:
                output.unknown()
            else:
                print("Unknown state: {}".format(state))

    def run(self, **kwargs):
        self.output(None, ["The method run has not been overridden, to create a check, start by inheriting "
                           "the 'Check' class and override the 'run' method."])

    @property
    def parser(self):
        parser = gen_parser(self.description)
        parser = self.adjust_parser(parser)
        return parser

    @property
    def cli_args(self):
        return vars(self.parser.parse_args())

    @property
    def pairs(self):
        return get_pairs(warning=self.cli_args["warning"], critical=self.cli_args["critical"])

    @property
    def thresholds(self):
        return parse(warning=self.cli_args["warning"], critical=self.cli_args["critical"])

    def adjust_parser(self, parser):
        return parser


class ReturnValue(object):
    def __init__(self, value, label):
        self.value = value
        self.label = label
