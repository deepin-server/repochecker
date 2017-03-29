#!/usr/bin/env python

import apt
import apt_pkg
import platform
from optparse import OptionParser
import multiprocessing
import logging
import ConfigParser
import os.path
import smtplib
from email.message import Message

class CheckBroken(object):
    """AutoAPT: a series of auto tests for package system"""

    def __init__(self, work_mode, with_filter=False, debug=False):
        super(CheckBroken, self).__init__()

        self.work_mode_map = {
            "CHECK_BROKEN": self.check_broken,
            "CHECK_BUILD": self.check_build,
            "USAGE": self.usage,
        }

        # system platform
        self.pkg_arch = self.get_pkg_architecture()

        # construct cache
        self.pkg_cache = apt_pkg.Cache()
        self.apt_cache = apt.cache.Cache()

        # construct file filters
        self.file_filter = ["deepin", "Deepin", "Debian", "Deepin Server kui", "Deepin Linux Server Main Repo"]

        # if just check the pkgs in included by file_filter
        self.with_filter = with_filter
        self.filter_filenames = self.get_filter_filenames()

        # debug information
        self.debug = debug
        self.logger = logging.getLogger()

        # construct record files
        record_file_path = "record.rd"
        self.record_file = open(record_file_path, "w")

        # construct handle method
        self.work_mode_handler = self.work_mode_map.get(work_mode, self.usage)
        # run
        self.work_mode_handler()

    def get_pkg_architecture(self):
        sys_pf = platform.machine()
        if sys_pf == "x86_64":
            return "amd64"
        elif sys_pf == "i686":
            return "i386"
        elif sys_pf == "mips64":
            return "mips64el"
        else:
            print("Unknow system platform.\n %s"%sys_pf[0])
            quit()

    def get_filter_filenames(self):
        pkg_file_list = []
        all_pkg_file_list = self.pkg_cache.file_list
        for pkg_file in all_pkg_file_list:
            if pkg_file.label in self.file_filter:
                pkg_file_list.append(pkg_file.filename)

        return pkg_file_list

    def package_filter(self, pkg_package):
        """
        package filter:
            return True: the package met the the filter conditions
            otherwise return False.

            check range:
            1, package file label should be included by file_filter
            2, it should be an not-installed package
        """
        version_list = pkg_package.version_list

        # get pkg version
        version = version_list[0]
        file_list = version.file_list

        # filter(ignore) the installed packages
        for f in file_list:
            if f[0].filename == "/var/lib/dpkg/status":
                return False

        # filter(ignore) the mismatching architecture packages
        if pkg_package.architecture != self.pkg_arch:
            return False

        # filter the package file
        file_name = file_list[0][0].filename
        if file_name in self.filter_filenames:
            return True

        return False

    def usage(self, **args):
        print("help .... ")

    def check_base(self, build=False):
        # all packages
        packages = self.pkg_cache.packages

        processes = []
        for p in packages:
            #self.check_package(p)
            if build:
                process = multiprocessing.Process(target=self.check_package, args=[p, True])
            else:
                process = multiprocessing.Process(target=self.check_package, args=[p])
            processes.append(process)
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def check_broken(self):
        self.check_base()

    def check_build(self):
        self.check_base(build=True)

    def check_package(self, p, build=False):
        pkg_name = ""
        if self.pkg_arch == "i386":
            pkg_name = p.name
        else:
            pkg_name = p.get_fullname()

        try:
            if pkg_name not in self.apt_cache:
                return
            package = self.apt_cache[pkg_name]

            if self.with_filter:
                if not self.package_filter(p):
                    return

            dep_pkg = ''
            if build:
                source = apt_pkg.SourceRecords()
                lookup_pkg = pkg_name.split(':')[0]
                if self.debug:
                   self.logger.info("Package: %s" % lookup_pkg)
                source.lookup(lookup_pkg)
                try:
                    build_depends = source.build_depends['Build-Depends']
                except:
                    return
                for pkg_list in build_depends:
                    for pkg, _, _ in pkg_list:
                        if self.debug:
                            self.logger.info("\tDepends: %s" % pkg)
                        if pkg not in self.apt_cache:
                            if self.debug:
                                self.logger.info("%s -- missing package" % pkg)
                            continue
                        dep_pkg = self.apt_cache[pkg]
                        dep_pkg.mark_install()
            else:
                #pkg_name = package.fullname
                package.mark_install()
        except SystemError as e:
            #print(package)
            if build:
                if self.debug:
                    self.logger.info("%s -- %s" % (dep_pkg.name, str(e)))
                self.record(dep_pkg, str(e))
            else:
                if self.debug:
                    self.logger.info("%s -- %s" % (package.name, str(e)))
                self.record(package, str(e))
            self.apt_cache.clear()

    def record(self, package, err):
        write_str = "%s -- %s\n" % (package.name, err)
        #write_str = "Package: %s\nErrorInfo: %s\n\n" %(pkg_name, err)
        self.record_file.write(write_str)
        self.record_file.close()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m", metavar="CHECK_MODE", dest="check_mode", help="cb: check broken package. cd: check build depends.", type="string", action="store")
    parser.add_option("-f", dest="with_filter", action="store_true", help="filter packages")
    parser.add_option("-d", dest="debug", action="store_true", help="debug information")
    (options, args) = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG) 

    mode = None
    arg_mode = options.check_mode
    if arg_mode == "cb":
        mode = "CHECK_BROKEN"
    elif arg_mode == "cd":
        mode = "CHECK_BUILD"

    with_filter = options.with_filter
    if None in (mode, with_filter):
        parser.print_help()
        quit()

    if options.debug:
        at = CheckBroken(mode, True, True)
    else:
        at = CheckBroken(mode, True)

    record_file = 'record.rd'
    if os.path.getsize(record_file) == 0:
        quit()

    config = ConfigParser.ConfigParser()
    config.read('mail_config.ini')
    SEND_MAIL = config.get('default', 'send_mail')
    SEND_MAIL_PASS = config.get('default', 'send_mail_pass')
    RECEIVE_MAIL = config.get('default', 'receive_mail')

    msg = Message()
    msg['From'] = SEND_MAIL
    msg['To'] = RECEIVE_MAIL
    msg['Subject'] = 'Deepin Repository Checker Report'

    with open(record_file) as f:
        lines = f.readlines()
    lines = [item.strip() for item in lines]
    lines = list(set(lines))
    lines.sort()
    body = '\n'.join(lines)
    msg.set_payload(body)

    try:
        smtp = smtplib.SMTP_SSL(host='smtp.exmail.qq.com', port=465)
        smtp.login(SEND_MAIL, SEND_MAIL_PASS)
        smtp.sendmail(SEND_MAIL, RECEIVE_MAIL.split(','), msg.as_string())
        smtp.quit()
    except smtplib.SMTPServerDisconnected as e:
        print(e)
