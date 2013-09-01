
INFO = 1
WARNING = 2
ERROR = 3


class LogLine(object):
    def __init__(self, level, parts, additional_info_lines=[]):
        self.level = level
        self.parts = parts
        self.additional_info_lines = additional_info_lines

    def __unicode__(self):
        return self.as_string

    def __str__(self):
        return self.__unicode__().encode('utf-8')

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
            if position is not None:
                self.text = "%s:%s,%s" % position
            else:
                self.text = "unknown position"

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
        additional_info_lines = [
            LogLine(ERROR, parts) for parts in self.additional_info_items
        ]
        self.log_line = LogLine(
            ERROR,
            log_parts,
            additional_info_lines=additional_info_lines,
        )
        Exception.__init__(self, self.log_line.as_string)

    @property
    def additional_info_items(self):
        return []


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


class TerminalCompileLogHandler(CompileLogHandler):

    def __init__(self, error_stream, out_stream=None):
        if out_stream is None:
            out_stream = error_stream
        self.error_stream = error_stream
        self.out_stream = out_stream

    def __call__(self, line):
        msg = str(line)
        level = "???????"
        stream = self.error_stream
        if line.level == ERROR:
            level = " ERROR "
        if line.level == WARNING:
            level = "WARNING"
        if line.level == INFO:
            level = " INFO  "
            stream = self.out_stream

        if len(line.additional_info_lines) > 0:
            stream.write("\n")

        stream.write("[ %s ] %s\n" % (level, msg))

        if len(line.additional_info_lines) > 0:
            for additional_line in line.additional_info_lines:
                stream.write("            %s\n" % str(additional_line))
            stream.write("\n")


class MultiCompileLogHandler(CompileLogHandler):

    def __init__(self, handlers):
        self.handlers = handlers

    def __call__(self, line):
        for handler in self.handlers:
            handler(line)
