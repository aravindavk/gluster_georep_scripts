# -*- coding: utf-8 -*-
"""
    georephelper.py
    :copyright: (c) 2015 by Aravinda VK <mail@aravindavk.in>
    :license: MIT, see LICENSE for more details.
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import uuid
import xattr
import sys
from errno import ENODATA
import os
import struct
import tarfile


PROG_DESCRIPTION = """
GlusterFS Georep Helper Tool
"""


def mode_gfid(args):
    try:
        try:
            print uuid.UUID(bytes=xattr.get(args.path, "trusted.gfid"))
        except (IOError, OSError) as e:
            if e.errno == ENODATA:
                print uuid.UUID(bytes=xattr.get(args.path, "glusterfs.gfid"))
            else:
                raise
    except (OSError, IOError) as e:
        print "[Error %s] %s" % (e.errno, os.strerror(e.errno))
        sys.exit(-1)


def mode_xtime(args):
    xtime_key = "trusted.glusterfs.%s.xtime" % args.master_uuid
    try:
        print struct.unpack("!II", xattr.get(args.path, xtime_key))
    except (OSError, IOError) as e:
        print "[Error %s] %s" % (e.errno, os.strerror(e.errno))
        sys.exit(-1)


def mode_stime(args):
    try:
        stime_key = "trusted.glusterfs.%s.%s.stime" % (args.master_uuid,
                                                       args.slave_uuid)
        print struct.unpack("!II", xattr.get(args.path, stime_key))
    except (OSError, IOError) as e:
        print "[Error %s] %s" % (e.errno, os.strerror(e.errno))
        sys.exit(-1)


def mode_listfromtar(args):
    tar = tarfile.open(args.path)
    tar.list()


def mode_volmarkmaster(args):
    fmt_string = "!" + "B" * 19 + "II"
    try:
        vm = struct.unpack(fmt_string, xattr.get(
            args.path,
            "trusted.glusterfs.volume-mark"))
        print "UUID        : %s" % uuid.UUID(
            "".join(['%02x' % x for x in vm[2:18]]))
        print "VERSION     : %s.%s" % vm[0:2]
        print "RETVAL      : %s" % vm[18]
        print "VOLUME MARK : %s.%s" % vm[19:21]
    except (OSError, IOError) as e:
        if e.errno == ENODATA:
            pass
        else:
            print "[Error %s] %s" % (e.errno, os.strerror(e.errno))
            sys.exit(-1)


def mode_volmarkslave(args):
    all_xattrs = xattr.list(args.path)
    fmt_string = "!" + "B" * 19 + "II" + "I"
    volmark_xattrs = []
    for x in all_xattrs:
        if x.startswith("trusted.glusterfs.volume-mark."):
            volmark_xattrs.append(x)

    for vx in volmark_xattrs:
        try:
            vm = struct.unpack(fmt_string, xattr.get(
                args.path,
                vx))

            print "UUID        : %s" % uuid.UUID(
                "".join(['%02x' % x for x in vm[2:18]]))
            print "VERSION     : %s.%s" % vm[0:2]
            print "RETVAL      : %s" % vm[18]
            print "VOLUME MARK : %s.%s" % vm[19:21]
            print "TIMEOUT     : %s" % vm[-1]
        except (OSError, IOError) as e:
            if e.errno == ENODATA:
                pass
            else:
                print "[Error %s] %s" % (e.errno, os.strerror(e.errno))
                sys.exit(-1)


def _get_args():
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=PROG_DESCRIPTION)
    subparsers = parser.add_subparsers(dest="mode")

    parser_getgfid = subparsers.add_parser('gfid')
    parser_getgfid.add_argument("path", help="Path")

    parser_getxtime = subparsers.add_parser('xtime')
    parser_getxtime.add_argument("path", help="Path")
    parser_getxtime.add_argument("master_uuid", help="Master UUID")

    parser_getstime = subparsers.add_parser('stime')
    parser_getstime.add_argument("path", help="Path")
    parser_getstime.add_argument("master_uuid", help="Master UUID")
    parser_getstime.add_argument("slave_uuid", help="Master UUID")

    parser_archivelist = subparsers.add_parser('listfromtar')
    parser_archivelist.add_argument("path", help="Path of Archive(Tar file)")

    parser_volmark_master = subparsers.add_parser('volmarkmaster')
    parser_volmark_master.add_argument("path", help="Path")

    parser_volmark_slave = subparsers.add_parser('volmarkslave')
    parser_volmark_slave.add_argument("path", help="Path")

    return parser.parse_args()


def main():
    args = _get_args()
    globals()["mode_" + args.mode](args)


if __name__ == "__main__":
    main()
