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

    def __init__(self, success: int = 0, error: int = 84) -> None:
        # ---- The colours for the TUI ----
        self.colors = {
            "default": "",
            "white": "\x1b[01;37m",
            "gray": "\x1b[00;37m",
            "purple": "\x1b[00;35m",
            "cyan": "\x1b[01;36m",
            "green": "\x1b[01;32m",
            "red": "\x1b[01;05;37;41m"
        }
        # ---- The status code ----
        self.success = success
        self.error = error

    def has_colors(self, stream) -> bool:
        """ Check if the ncurse library is present in the system for the colour management """
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
        """ Get the type of document in order to apply some colour """
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

    def get_user_info(self, uid) -> str:
        """ Get the info of the user """
        try:
            import pwd
            user_info = pwd.getpwuid(uid)
            return user_info.pw_name
        except ImportError:
            return str(uid)

    def get_group_info(self, gid) -> str:
        """ Get the pid of the active groupe """
        try:
            import grp
            group_info = grp.getgrgid(gid)
            return group_info.gr_name
        except ImportError:
            return str(gid)

    def list_files(self, files: list) -> int:
        """ List the files contained in the path """
        global_status = self.success
        table = PrettyTable(
            [
                "Permissions",
                "# Links",
                "Owner",
                "Group",
                "Size",
                "Last Mod",
                "Name"
            ]
        )

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
                global_status = self.error
                continue

            perms, color, link = self.get_mode_info(
                stat_info.st_mode,
                filename
            )

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

            table.add_row(
                [
                    perms,
                    nlink,
                    name,
                    group,
                    size,
                    time_str,
                    filenameStr
                ]
            )

        table.align["Permissions"] = 'l'
        table.align["# Links"] = 'r'
        table.align["Owner"] = 'l'
        table.align["Group"] = 'l'
        table.align["Size"] = 'r'
        table.align["Last Mod"] = 'l'
        table.align["Name"] = 'l'
        print(table)
        return global_status

    def ls(self, path: str or list = "") -> int:
        """ 
        A basic loop manager to make this P.O.S POC a minimum functional and feel like the core of the real ls
        """
        if path == "":
            content = os.listdir(".")
            self.list_files(content)
        if isinstance(path, list):
            global_status = self.success
            for item in path:
                print(f"Content of: {item}")
                content = [item]
                if os.path.isdir(item):
                    content = os.listdir(item)
                status = self.list_files(content)
                if status != self.success:
                    global_status = self.error
            return global_status
        if os.path.isdir(path):
            files = os.listdir(path)
            return self.list_files(files)
        files = [path]
        return self.list_files(files)


if __name__ == '__main__':
    LS = LsPython()
    if len(sys.argv) == 1:
        files = os.listdir(".")
    else:
        files = sys.argv[1:]

    print("With a simple file:")
    print(f"status={LS.ls(files)}")
    print("With a full blown path:")
    print(f"status={LS.ls(os.getcwd())}")
    data = [
        os.getcwd(),
        os.getcwd(),
        os.getcwd(),
        os.getcwd()
    ]
    print("With a list of paths:")
    print(f"status={LS.ls(data)}")
