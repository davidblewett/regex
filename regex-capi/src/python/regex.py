from collections import namedtuple

from .lib import RURE_DEFAULT_FLAGS, ffi, lib, checked_call


RegexMatch = namedtuple("RegexMatch", ("start", "end"))


class Regex(object):
    """ A compiled regular expression for matching Unicode strings.

    It is represented as either a sequence of bytecode instructions (dynamic)
    or as a specialized Rust function (native). It can be used to search,
    split or replace text. All searching is done with an implicit .*?
    at the beginning and end of an expression. To force an expression to match
    the whole string (or a prefix or a suffix), you must use an anchor
    like ^ or $ (or \A and \z).

    While this crate will handle Unicode strings (whether in the regular
    expression or in the search text), all positions returned are byte indices.
    Every byte index is guaranteed to be at a Unicode code point boundary.
    """

    def __init__(self, re, _pointer=None,
                 flags=RURE_DEFAULT_FLAGS, **options):
        """ Compiles a regular expression. Once compiled, it can be used
        repeatedly to search, split or replace text in a string.

        :param re:      Expression to compile
        :param flags:   Bitmask of flags
        :param kwargs:  Config options to pass (size_limit, dfa_size_limit)
        """
        self._err = ffi.gc(lib.rure_error_new(), lib.rure_error_free)
        self._opts = ffi.gc(lib.rure_options_new(), lib.rure_options_free)
        self.options = options
        if 'size_limit' in options:
            lib.rure_options_size_limit(self._opts, options['size_limit'])
        if 'dfa_size_limit' in options:
            lib.rure_options_dfa_size_limit(self._opts,
                                            options['dfa_size_limit'])
        if re:
            s = checked_call(
                lib.rure_compile,
                self._err,
                re.encode('utf8'),
                len(re),
                flags,
                self._opts
            )
        else:
            s = _pointer
        self._ptr = ffi.gc(s, lib.rure_free)

    def is_match(self, text, start=0):
        """ Returns true if and only if the regex matches the string given.

        It is recommended to use this method if all you need to do is test
        a match, since the underlying matching engine may be able to do less
        work.
        """
        haystack = text.encode('utf8')
        return bool(lib.rure_is_match(
            self._ptr,
            haystack,
            len(haystack),
            start
        ))

    def find(self, text, start=0):
        """ Returns the start and end byte range of the leftmost-first match
        in text. If no match exists, then None is returned.

        Note that this should only be used if you want to discover the position
        of the match. Testing the existence of a match is faster if you use
        is_match.
        """
        haystack = text.encode('utf8')
        match = ffi.new('rure_match *')
        lib.rure_find(
            self._ptr,
            haystack,
            len(haystack),
            start,
            match
        )
        fr = RegexMatch(match.start, match.end)
        return fr

    def find_captures(self, text, start=0):
        """ Returns the start and end byte range of the leftmost-first match
        in text. If no match exists, then None is returned.

        Note that this should only be used if you want to discover the position
        of the match. Testing the existence of a match is faster if you use
        is_match.
        """
        haystack = text.encode('utf8')
        captures = ffi.gc(lib.rure_captures_new(self._ptr),
                          lib.rure_captures_free)
        lib.rure_find_captures(
            self._ptr,
            haystack,
            len(haystack),
            start,
            captures
        )
        # FIXME: convert captures to a Pythonic interface using the C
        #        introspection functions
        return captures
