import os
import sys

from rure._ffi import ffi
from rure import exceptions


RURE_FLAG_MULTI = 1 << 1
RURE_FLAG_DOTNL = 1 << 2
RURE_FLAG_SWAP_GREED = 1 << 3
RURE_FLAG_SPACE = 1 << 4
RURE_FLAG_UNICODE = 1 << 5
RURE_DEFAULT_FLAGS = RURE_FLAG_UNICODE




def find_library():
    libname = "rure"
    if sys.platform == 'win32':
        prefix = ''
        suffix = 'dll'
    elif sys.platform == 'darwin':
        prefix = 'lib'
        suffix = 'dylib'
    else:
        prefix = 'lib'
        suffix = 'so'
    cur_dir = os.path.dirname(__file__)
    return os.path.join(cur_dir, "{}{}.{}".format(prefix, libname, suffix))


_lib = ffi.dlopen(find_library())


def checked_call(fn, err, *args):
    all_args = list(args) + [err]
    res = fn(*all_args)
    msg = ffi.string(_lib.rure_error_message(err))
    if msg == 'no error':
        return res
    elif msg.startswith('Error parsing regex'):
        raise exceptions.RegexSyntaxError(msg)
    elif msg.startswith('Compiled regex exceeds size limit'):
        raise exceptions.CompiledTooBigError(msg)
    else:
        raise RegexError(msg)
