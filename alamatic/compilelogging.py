
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
