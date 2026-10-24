"""Top-level standard-library module names (CPython 3.9-3.13, including modules removed since 3.11).

Frozen so that name checks give the same answer on every interpreter. A generated package with one of these
names shadows (or is shadowed by) the standard library."""

STDLIB_MODULES = frozenset(
    """
    217
    abc aifc antigravity argparse array ast asynchat asyncio asyncore atexit audioop base64 bdb binascii bisect
    builtins bz2 cProfile calendar cgi cgitb chunk cmath cmd code codecs codeop collections colorsys compileall
    concurrent configparser contextlib contextvars copy copyreg crypt csv ctypes curses dataclasses datetime dbm
    decimal difflib dis distutils doctest email encodings ensurepip enum errno faulthandler fcntl filecmp fileinput
    fnmatch fractions ftplib functools gc genericpath getopt getpass gettext glob graphlib grp gzip hashlib heapq
    hmac html http idlelib imaplib imghdr imp importlib inspect io ipaddress itertools json keyword lib2to3
    linecache locale logging lzma mailbox mailcap marshal math mimetypes mmap modulefinder msilib msvcrt
    multiprocessing netrc nis nntplib nt ntpath nturl2path numbers opcode operator optparse os ossaudiodev pathlib
    pdb pickle pickletools pipes pkgutil platform plistlib poplib posix posixpath pprint profile pstats pty pwd
    py_compile pyclbr pydoc pydoc_data pyexpat queue quopri random re readline reprlib resource rlcompleter runpy
    sched secrets select selectors shelve shlex shutil signal site smtpd smtplib sndhdr socket socketserver spwd
    sqlite3 sre_compile sre_constants sre_parse ssl stat statistics string stringprep struct subprocess sunau
    symtable sys sysconfig syslog tabnanny tarfile telnetlib tempfile termios textwrap this threading time timeit
    tkinter token tokenize tomllib trace traceback tracemalloc tty turtle turtledemo types typing unicodedata
    unittest urllib uu uuid venv warnings wave weakref webbrowser winreg winsound wsgiref xdrlib xml xmlrpc zipapp
    zipfile zipimport zlib zoneinfo
    """.split()
)
