import sys
import stat
import os
import locale
import time
from prettytable import PrettyTable

class LsPython:
    """
    This is a cross-platform implementation of ls but for python.
    It uses the prettytable module to display the output in a nice table.
    
    This cross-platform implementation was done by Henry Letellier who'se Github profile can be found here: https://github.com/HenraL
    Most of the code was borrowed from http://www.pixelbeat.org/talks/python/ls.py.html, written by Pádraig Brady: http://www.pixelbeat.org/, so all credit goes out to him.
    All I did was use the prettytable library: https://pypi.python.org/pypi/PrettyTable to display the output.
    I couldn't find his implementation on Github to fork, and I just wanted to get it on here for my own convenience.
    Pádraig Brady's Github profile can be found here: https://github.com/pixelb.
    """
    def __init__(self):
        self.colors = {
            "default": "",
            "white": "\x1b[01;37m",
            "gray": "\x1b[00;37m",
            "purple": "\x1b[00;35m",
            "cyan": "\x1b[01;36m",
            "green": "\x1b[01;32m",
            "red": "\x1b[01;05;37;41m"
        }

    def has_colors(self, stream):
        if not hasattr(stream, "isatty"):
            return False
        if not stream.isatty():
            return False
        try:
            import curses
            curses.setupterm()
            return curses.tigetnum("colors") > 2
        except:
            return False

    def get_mode_info(self, mode, filename):
        perms = "-"
        color = "default"
        link = ""

        if stat.S_ISDIR(mode):
            perms = "d"
            color = "cyan"
        elif stat.S_ISLNK(mode):
            perms = "l"
            color = "purple"
            link = os.readlink(filename)
            if not os.path.exists(filename):
                color = "red"
        elif stat.S_ISREG(mode):
            if mode & (stat.S_IXGRP | stat.S_IXUSR | stat.S_IXOTH):
                color = "green"
            else:
                if filename[0] == '.':
                    color = "gray"
                else:
                    color = "white"

        mode = stat.S_IMODE(mode)

        for who in "USR", "GRP", "OTH":
            for what in "R", "W", "X":
                if mode & getattr(stat, "S_I" + what + who):
                    perms = perms + what.lower()
                else:
                    perms = perms + "-"

        return (perms, color, link)

    def get_user_info(self, uid):
        try:
            import pwd
            user_info = pwd.getpwuid(uid)
            return user_info.pw_name
        except ImportError:
            return str(uid)

    def get_group_info(self, gid):
        try:
            import grp
            group_info = grp.getgrgid(gid)
            return group_info.gr_name
        except ImportError:
            return str(gid)

    def list_files(self, files):
        table = PrettyTable(["Permissions", "# Links", "Owner", "Group", "Size", "Last Mod", "Name"])

        locale.setlocale(locale.LC_ALL, '')
        files.sort(key=lambda x: x.lower())

        now = int(time.time())
        recent = now - (6 * 30 * 24 * 60 * 60)

        does_have_colors = self.has_colors(sys.stdout)

        for filename in files:
            try:
                stat_info = os.lstat(filename)
            except:
                sys.stderr.write("%s: No such file or directory\n" % filename)
                continue

            perms, color, link = self.get_mode_info(stat_info.st_mode, filename)

            nlink = "%4d" % stat_info.st_nlink
            name = self.get_user_info(stat_info.st_uid)
            group = self.get_group_info(stat_info.st_gid)
            size = "%8d" % stat_info.st_size

            ts = stat_info.st_mtime
            if (ts < recent) or (ts > now):
                time_fmt = "%b %e  %Y"
            else:
                time_fmt = "%b %e %R"
            time_str = time.strftime(time_fmt, time.gmtime(ts))

            if self.colors[color] and does_have_colors:
                filenameStr = self.colors[color] + filename + "\x1b[00m"
            else:
                filenameStr = filename

            if link:
                filenameStr += " -> "
            filenameStr += link

            table.add_row([perms, nlink, name, group, size, time_str, filenameStr])

        table.align["Permissions"] = 'l'
        table.align["# Links"] = 'r'
        table.align["Owner"] = 'l'
        table.align["Group"] = 'l'
        table.align["Size"] = 'r'
        table.align["Last Mod"] = 'l'
        table.align["Name"] = 'l'
        print(table)

if __name__ == '__main__':
    ls = LsPython()
    if len(sys.argv) == 1:
        files = os.listdir(".")
    else:
        files = sys.argv[1:]
    ls.list_files(files)
