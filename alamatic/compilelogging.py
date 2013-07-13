
INFO = 1
WARNING = 2
ERROR = 3


class LogLine(object):
    def __init__(self, level, parts):
        self.level = level
        self.parts = parts

    def __unicode__(self):
        return self.as_string

    @property
    def as_string(self):
        return "".join((unicode(s) for s in self.parts))

    @property
    def positions_mentioned(self):
        return [x.position for x in self.parts if type(x) is pos_link]


class pos_link(object):
    def __init__(self, position, text=None):
        self.position = position
        if text is not None:
            self.text = text
        else:
            self.text = "%s:%s,%s" % position

    def __unicode__(self):
        return self.text

    @property
    def filename(self):
        return self.position[0]

    @property
    def line(self):
        return self.position[1]

    @property
    def column(self):
        return self.position[2]


class CompilerError(Exception):
    def __init__(self, *log_parts):
        self.log_line = LogLine(ERROR, log_parts)
        Exception.__init__(self, self.log_line.as_string)


class CompileLogHandler(object):
    def __call__(self, line):
        pass


class LoggingCompileLogHandler(CompileLogHandler):

    def __init__(self):
        import logging
        self.logger = logging.getLogger("alamatic.compilelogging")

    def __call__(self, line):
        msg = str(line)
        # There's probably a less dumb way to do this if I actually
        # bother to read the logging docs. But that's for later.
        if line.level == ERROR:
            self.logger.error(msg)
        elif line.level == WARNING:
            self.logger.warning(msg)
        elif line.level == INFO:
            self.logger.info(msg)


class InMemoryCompileLogHandler(CompileLogHandler):

    def __init__(self):
        self.lines = []

    def __call__(self, line):
        self.lines.append(line)
