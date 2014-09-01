
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
        types_linked = [t.type for t in self.parts if type(t) is type_link]
        if len(types_linked) > 0:
            from alamatic.types import get_type_display_names
            type_names = get_type_display_names(types_linked)

        def expand(part):
            if type(part) is type_link:
                return type_names[part.type]
            else:
                return unicode(s)

        return "".join((unicode(s) for s in self.parts))

    @property
    def positions_mentioned(self):
        return [x.position for x in self.parts if type(x) is pos_link]

    @property
    def source_ranges_mentioned(self):
        return [x.source_range for x in self.parts if type(x) is range_link]


class pos_link(object):
    def __init__(self, position, text=None):
        from alamatic.scanner import SourceLocation, SourceRange

        if isinstance(position, tuple):
            # Upgrade legacy tuple-based position to real location object.
            position = SourceLocation(
                filename=position[0],
                line=position[1],
                column=position[2],
            )
        elif isinstance(position, SourceRange):
            # Lower a source range into its start position.
            position = position.start
        elif position is not None and not isinstance(position, SourceLocation):
            raise Exception(
                "Position is defined but it's a %s when it should "
                "be a SourceLocation, SourceRange, or tuple" % (
                    type(position)
                )
            )

        self.position = position
        if text is not None:
            self.text = text
        else:
            if position is not None:
                self.text = "%s:%s,%s" % (
                    position.filename,
                    position.line,
                    position.column,
                )
            else:
                self.text = "unknown position"

    def __unicode__(self):
        return self.text

    @property
    def filename(self):
        return self.position.filename

    @property
    def line(self):
        return self.position.line

    @property
    def column(self):
        return self.position.column


class range_link(object):
    def __init__(self, source_range, highlight_ranges=set(), text=None):
        self.source_range = source_range
        self.highlight_ranges = highlight_ranges
        if text is not None:
            self.text = text
        else:
            if source_range is not None:
                self.text = str(source_range)
            else:
                self.text = "unknown position"

    def __unicode__(self):
        return self.text


class type_link(object):
    def __init__(self, type):
        self.type = type

    def __unicode__(self):
        return self.type.display_name


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

    def close(self):
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
        self._generated_error = False
        self._generated_out = False

        if self.error_stream.isatty():
            self.error_stream.write("\x1b[0;37;40m")
        if self.out_stream.isatty():
            self.out_stream.write("\x1b[0;37;40m")

    def __call__(self, line):
        msg = str(line)
        level = "???????"
        color = ""
        stream = self.error_stream
        if line.level == ERROR:
            level = " ERROR "
            color = "\x1b[31m"
            self._generated_error = True
        if line.level == WARNING:
            level = "WARNING"
            color = "\x1b[33m"
            self._generated_error = True
        if line.level == INFO:
            level = " INFO  "
            color = "\x1b[36m"
            stream = self.out_stream
            self._generated_out = True

        if len(line.additional_info_lines) > 0:
            stream.write("\n")

        if stream.isatty():
            uncolor = "\x1b[37m"
        else:
            uncolor = ""
            color = ""

        stream.write("\n[ %s%s%s ] %s\n" % (color, level, uncolor, msg))

        for source_range in line.source_ranges_mentioned:
            self._write_source_range(
                source_range,
                stream,
                indent=12,
            )

        if len(line.additional_info_lines) > 0:
            for additional_line in line.additional_info_lines:
                stream.write("            %s\n" % str(additional_line))
            stream.write("\n")

    def close(self):
        if self.error_stream.isatty():
            self.error_stream.write("\x1b[0m")
        if self.out_stream.isatty():
            self.out_stream.write("\x1b[0m")

        if self._generated_error:
            self.error_stream.write("\n")
        elif self._generated_out:
            self.out_stream.write("\n")

    def _write_source_range(self, source_range, stream, indent=0):
        # TODO: Actually go fetch the source code line and show it
        # with the given range highlighted.
        start_str = str(source_range.start.filename)

        source_str = "(source not available)"

        # This should always be true for all sane ranges, but
        # let's just be sure so we don't end up doing something crazy.
        if (
            source_range.start.filename == source_range.end.filename
            and source_range.start.line <= source_range.end.line
        ):
            try:
                f = open(source_range.start.filename, 'r')
            except IOError, ex:
                pass

            start_line = source_range.start.line
            end_line = source_range.end.line
            found_snippet = False
            source_str_parts = []

            if f is not None:

                line_number_format = "%%%ii: " % len(str(end_line))

                for idx, line in enumerate(f):
                    line_number = idx + 1

                    # Put the end marker in first, before the start marker,
                    # so that we don't need to worry about the start
                    # marker moving the end position later in the string.
                    if line_number == end_line:
                        if stream.isatty():
                            line = (
                                line[0:source_range.end.column] +
                                "\x1b[0;37;40m" +
                                line[source_range.end.column:]
                            )

                    if line_number == start_line:
                        found_snippet = True
                        if stream.isatty():
                            line = (
                                line[0:source_range.start.column] +
                                "\x1b[1;4;40m" +
                                line[source_range.start.column:]
                            )

                    if found_snippet:
                        source_str_parts.append(
                            " " * (indent + 4)
                        )
                        source_str_parts.append(
                            line_number_format % line_number
                        )
                        source_str_parts.append(line)

                    if line_number == end_line:
                        break

            if found_snippet:
                source_str = "".join(source_str_parts)

        stream.write("%s%s:\n%s\n" % (
            " " * indent,
            start_str,
            source_str,
        ))


class MultiCompileLogHandler(CompileLogHandler):

    def __init__(self, handlers):
        self.handlers = handlers

    def __call__(self, line):
        for handler in self.handlers:
            handler(line)
