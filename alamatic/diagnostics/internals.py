
import string
import re


__all__ = [
    "ERROR",
    "WARNING",
    "register_diagnostic",
    "Diagnostic",
]


class Level:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "[%s]" % name


ERROR = Level("ERROR")
WARNING = Level("WARNING")


class RangeLink(object):

    def __init__(self, source_range, caption=None):
        self.source_range = source_range
        if caption is not None:
            self.caption = caption
        else:
            self.caption = unicode(source_range)

    def __unicode__(self):
        return unicode(self.caption)

    def __repr__(self):
        return u"<RangeLink %s(%s)>" % (self.caption, self.source_range)

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        return (
            self.source_range == other.source_range and
            self.caption == other.caption
        )


class LocationLink(object):

    def __init__(self, source_location, caption=None):
        self.source_location = source_location
        if caption is not None:
            self.caption = caption
        else:
            self.caption = unicode(source_location)

    def __unicode__(self):
        return u'%s (at %s)' % (unicode(self.caption), self.source_location)

    def __repr__(self):
        return u"<LocationLink %s(%s)>" % (self.caption, self.source_location)

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        return (
            self.source_location == other.source_location and
            self.caption == other.caption
        )


class Formatter(string.Formatter):
    field_name_match = re.compile(r'\w+')

    def vformat(self, format_string, args, kwargs):
        return u''.join([
            unicode(x) for x in self.vformat_parts(format_string, kwargs)
        ])

    def vformat_parts(self, format_string, kwargs):
        for part in self.parse(format_string):
            if part[0] is not None and part[0] != '':
                yield part[0]
            if part[1] is not None:
                value = self.get_field(part[1], (), kwargs)[0]
                if part[3] is not None and part[3] != '':
                    value = self.convert_field(value, part[3])
                if part[2] is not None and part[2] != '':
                    value = self.format_field(value, part[2])
                yield value

    def get_param_names(self, format_string):
        parts = self.parse(format_string)
        for part in parts:
            field_name = part[1]
            match = re.match(self.field_name_match, field_name)
            if match:
                yield match.group(0)
            else:
                raise ValueError(
                    "Field name %r does not start with a valid variable name" %
                    field_name
                )

    def format_field(self, value, format_spec):
        if format_spec.startswith('link(') and format_spec.endswith(')'):
            link_caption = format_spec[5:-1]

            from alamatic.scanner import SourceRange, SourceLocation

            if isinstance(value, SourceRange):
                return RangeLink(value, link_caption)
            elif isinstance(value, SourceLocation):
                return LocationLink(value, link_caption)
            else:
                return link_caption
        else:
            raise ValueError(
                'Invalid format spec %r' % format_spec
            )


formatter = Formatter()


class Diagnostic(Exception):

    def __init__(self, **kwargs):
        self.values = kwargs
        self.message = formatter.vformat(self.format_string, [], kwargs)

    def __str__(self):
        return self.message

    def __repr__(self):
        return u"<%s: %s>" % (type(self).__name__, self.message)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.values == other.values
        else:
            return False


def make_diagnostic_class(name, level, format_string):
    if type(format_string) is str:
        format_string = format_string.decode('utf8')
    diag_type_dict = {}
    diag_type_dict["format_string"] = format_string
    diag_type_dict["level"] = level
    return type(name, (Diagnostic,), diag_type_dict)


def register_diagnostic(module_dict, name, level, format_string):
    module_dict["__all__"].append(name)
    module_dict[name] = make_diagnostic_class(name, level, format_string)
