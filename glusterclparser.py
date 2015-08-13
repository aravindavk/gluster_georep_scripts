# -*- coding: utf-8 -*-
"""
    glusterclparser.py
    :copyright: (c) 2015 by Aravinda VK <mail@aravindavk.in>
    :license: MIT, see LICENSE for more details.
"""

import sys

ENTRY = 'E'
META = 'M'
DATA = 'D'
SEP = "\x00"

GF_FOP = [
    "NULL", "STAT", "READLINK", "MKNOD", "MKDIR", "UNLINK",
    "RMDIR", "SYMLINK", "RENAME", "LINK", "TRUNCATE", "OPEN",
    "READ", "WRITE", "STATFS", "FLUSH", "FSYNC", "SETXATTR",
    "GETXATTR", "REMOVEXATTR", "OPENDIR", "FSYNCDIR", "ACCESS",
    "CREATE", "FTRUNCATE", "FSTAT", "LK", "LOOKUP", "READDIR",
    "INODELK", "FINODELK", "ENTRYLK", "FENTRYLK", "XATTROP",
    "FXATTROP", "FSETXATTR", "FGETXATTR", "RCHECKSUM", "SETATTR",
    "FSETATTR", "READDIRP", "GETSPEC", "FORGET", "RELEASE",
    "RELEASEDIR", "FREMOVEXATTR", "FALLOCATE", "DISCARD", "ZEROFILL"]


class NumTokens_V11(object):
    E = 7
    M = 3
    D = 2
    NULL = 3
    MKNOD = 7
    MKDIR = 7
    UNLINK = 4
    RMDIR = 4
    SYMLINK = 4
    RENAME = 5
    LINK = 4
    SETXATTR = 3
    REMOVEXATTR = 3
    CREATE = 7
    SETATTR = 3
    FTRUNCATE = 3


class NumTokens_V12(NumTokens_V11):
    UNLINK = 5
    RMDIR = 5


class Version:
    V11 = "v1.1"
    V12 = "v1.2"


def get_num_tokens(data, tokens, version=Version.V11):
    if version == Version.V11:
        cls_numtokens = NumTokens_V11
    elif version == Version.V12:
        cls_numtokens = NumTokens_V12
    else:
        sys.stderr.write("Unknown Changelog Version\n")
        sys.exit(1)

    if data[tokens[0]] in [ENTRY, META]:
        if len(tokens) >= 3:
            return getattr(cls_numtokens, GF_FOP[int(data[tokens[2]])])
        else:
            return None
    else:
        return getattr(cls_numtokens, data[tokens[0]])


def process_record(data, tokens, changelog_ts):
    if data[tokens[0]] in [ENTRY, META]:
        try:
            tokens[2] = GF_FOP[int(data[tokens[2]])]
        except ValueError:
            tokens[2] = "NULL"

    sys.stdout.write("%s " % changelog_ts)

    for slc in tokens:
        try:
            sys.stdout.write("%s " % data[slc])
        except TypeError:
            if isinstance(slc, str):
                sys.stdout.write("%s " % slc)
            else:
                raise

    sys.stdout.write("\n")

count = 0


def print_tokens(data, tokens):
    pass
    # global count
    # sys.stdout.write("%s" % len(tokens))
    # for t in tokens:
    #     sys.stdout.write("%s " % data[t])
    # sys.stdout.write("\n")
    # count += 1

    # if count > 5:
    #     sys.exit(0)


def parse(filename):
    data = None
    tokens = []
    changelog_ts = filename.rsplit(".")[-1]
    with open(filename, "r+b") as f:
        # GlusterFS Changelog | version: v1.1 | encoding : 2
        header = f.readline()
        version = header.split()[4]

        data = f.read()

        slice_start = 0
        in_record = False

        prev_char = ""
        next_char = ""
        for i, c in enumerate(data):
            if len(data) >= (i + 2):
                next_char = data[i+1]

            if not in_record and c in [ENTRY, META, DATA]:
                tokens.append(slice(slice_start, i+1))
                slice_start = i+1
                in_record = True
                continue

            if c == SEP and prev_char != SEP and next_char != SEP:
                tokens.append(slice(slice_start, i))
                print_tokens(data, tokens)
                slice_start = i+1

                num_tokens = get_num_tokens(data, tokens, version)

                if num_tokens == len(tokens):
                    process_record(data, tokens, changelog_ts)
                    in_record = False
                    tokens = []

            prev_char = c

        # process last record
        if slice_start < (len(data) - 1):
            tokens.append(slice(slice_start, len(data)))
            process_record(data, tokens, changelog_ts)
            tokens = []


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("USAGE: ./%s <CHANGELOG_FILE>\n")
        sys.exit(1)

    parse(sys.argv[1])
    sys.exit(0)
