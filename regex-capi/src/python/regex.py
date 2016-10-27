import re
import warnings

from rure import Rure
from rure import DEFAULT_FLAGS
from rure import CASEI, MULTI, DOTNL, SWAP_GREED, SPACE, UNICODE


FLAG_MAP = {
    re.IGNORECASE: CASEI,
    re.LOCALE: None,
    re.MULTILINE: MULTI,
    re.DOTALL: DOTNL,
    re.UNICODE: UNICODE,
    re.VERBOSE: SPACE,
}

FLAG_NAMES = {
    re.IGNORECASE: 'IGNORECASE',
    re.LOCALE: 'LOCALE',
    re.MULTILINE: 'MULTILINE',
    re.DOTALL: 'DOTALL',
    re.UNICODE: 'UNICODE',
    re.VERBOSE: 'VERBOSE',
}


U_WARN = u'Expect undefined behavior by not passing a Unicode string to {}.{}::{}'


class RegexObject(object):

    def __init__(self, pattern, flags=0, **options):
        if isinstance(pattern, bytes):
            self._warn(u'__init__')

        self.flags = flags
        self.pattern = pattern.encode('utf8')
        self.submatches = options.pop('submatches', False)

        self.rure_flags = DEFAULT_FLAGS
        for flag, rure_flag in FLAG_MAP.items():
            if flags & flag:
                if rure_flag is None:
                    msg = u"rure doesn't support the flag '%s'"
                    warnings.warn(msg % FLAG_NAMES[flag], SyntaxWarning)
                else:
                    self.rure_flags = self.rure_flags | rure_flag

        self._rure = Rure(self.pattern, flags=self.rure_flags, **options)

        names = [name for name in self.capture_names()]
        # This can be greater than len(self.groupindex) due to
        # unnamed groupes
        self.groups = len(names)
        self.groupindex = {
            name: pos
            for pos, name in enumerate(names)
            if name is not None
        }

    def _warn(self, mname):
        warnings.warn(U_WARN.format(self.__class__.__module__,
                                    self.__class__.__name__,
                                    mname),
                      UnicodeWarning,
                      stacklevel=2)

    def capture_names(self):
        return self._rure.capture_names()

    def is_match(self, string, pos=0, endpos=None):
        if isinstance(string, bytes):
            self._warn(u'is_match')

        haystack = string[:endpos].encode('utf8')
        return self._rure.is_match(haystack, pos)

    def search(self, string, pos=0, endpos=None):
        if isinstance(string, bytes):
            self._warn(u'search')

        haystack = string[:endpos].encode('utf8')
        if self.submatches:
            captures = self._rure.captures(haystack, pos)
            if captures:
                return MatchObject(pos, endpos, self, haystack, captures)
        else:
            match = self._rure.find(haystack, pos)
            if match:
                return MatchObject(pos, endpos, self, haystack, None)

    def match(self, string, pos=0, endpos=None):
        if isinstance(string, bytes):
            self._warn(u'match')

        match = self.search(string, pos, endpos)
        if match and match.start == 0:
            return match

    def split(self, string, maxsplit=0):
        if isinstance(string, bytes):
            self._warn(u'split')

        # Not supported by the C library yet
        raise NotImplementedError

    def findall(self, string, pos=0, endpos=None):
        if isinstance(string, bytes):
            self._warn(u'findall')

        return [match for match in self.finditer(string, pos, endpos)]

    def finditer(self, string, pos=0, endpos=None):
        if isinstance(string, bytes):
            self._warn(u'finditer')

        haystack = string[:endpos].encode('utf8')
        if self.submatches:
            captures = self._rure.captures(haystack, pos)
            for captures in self._rure.captures_iter(haystack, pos):
                yield MatchObject(pos, endpos, self, haystack, captures)
        else:
            for match in self._rure.find_iter(haystack, pos):
                yield MatchObject(pos, endpos, self, haystack, None)

    def sub(self, repl, string, count=0):
        if isinstance(string, bytes):
            self._warn(u'sub')

        # Not supported by the C library yet
        raise NotImplementedError

    def subn(self, repl, string, count=0):
        if isinstance(string, bytes):
            self._warn(u'subn')

        # Not supported by the C library yet
        raise NotImplementedError


class MatchObject(object):

    offset_warning = u"This returns byte offsets; use with {}.{}::string"

    def __bool__(self):
        return True

    def __nonzero__(self):
        return self.__bool__()

    def __init__(self, pos, endpos, re, string, captures):
        self.pos = pos
        self.endpos = pos
        self.re = re
        self.string = string
        self._captures = captures

    def _warn(self, mname):
        warnings.warn(
            self.offset_warning.format(
                self.__class__.__module__,
                self.__class__.__name__,
                mname),
            UnicodeWarning,
            stacklevel=2)

    @property
    def lastindex(self):
        groups = [
            gindex
            for gindex, gname in enumerate(self.re.capture_names())
            if self.captures[gindex] is not None
        ]
        if groups:
            return groups[-1]

    @property
    def lastgroup(self, decode=True):
        groups = [
            gname
            for gindex, gname in enumerate(self.re.capture_names())
            if gname is not None and self.captures[gindex] is not None
        ]
        if groups:
            if decode:
                return groups[-1].decode('utf8')
            else:
                return groups[-1]

    @property
    def captures(self):
        if self._captures is None:
            self._captures = self.re._rure.captures(self.string, self.pos)
        return self._captures

    def expand(self, template):
        # Not supported by the C library yet
        raise NotImplementedError

    def group(self, *groups, **kwargs):
        default = kwargs.get('default', None)
        decode = kwargs.get('decode', True)
        if not groups:
            start, end = self.captures[0].start, self.captures[0].end
            if decode:
                return self.string[start:end].decode('utf8')
            else:
                return self.string[start:end]

        capture_data = []
        for i in groups:
            if isinstance(i, basestring):
                match = getattr(self.captures, i)
            else:
                if i < 0:
                    raise IndexError(i)
                match = self.captures[i]
            if match is None:
                capture_data.append(default)
            else:
                data = self.string[match.start:match.end]
                if decode:
                    capture_data.append(data.decode('utf8'))
                else:
                    capture_data.append(data)
        return tuple(capture_data)

    def groups(self, default=None):
        # Exclude the entire match (index 0)
        return self.group(*[i for i in range(len(self.captures)) if i > 0],
                          default=default)

    def groupdict(self, default=None, decode=True):
        group_indices = sorted(self.re.groupindex.values())
        group_data = self.group(*[i for i in group_indices], default=default)
        gdict = {}
        for pos, g_name_index in enumerate(
                sorted(self.re.groupindex.items(),
                       # Sort by value
                       key=lambda x: x[1])):
            gname = g_name_index[0]
            gval = group_data[pos]
            if decode:
                gdict[gname.decode('utf8')] = gval.decode('utf8')
            else:
                gdict[gname] = gval
        return gdict

    def start(self, group=0):
        self._warn(u'start')

        if self.captures[group] is None:
            return -1
        else:
            return self.captures[group].start

    def end(self, group=0):
        self._warn(u'end')

        if self.captures[group] is None:
            return -1
        else:
            return self.captures[group].end

    def span(self, group=0):
        self._warn(u'span')

        return (self.start(group), self.end(group))
