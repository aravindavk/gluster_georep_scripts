#!/usr/bin/python
import time
import subprocess
import xml.etree.cElementTree as etree
import sys
import logging
from contextlib import contextmanager
import tempfile

"""
Configurations:
LOG_LEVEL: Available options: logging.INFO, logging.DEBUG
LOG_FILE: Default is stdout, can be changed as any file
INTERVAL: Time interval between Status check to See Status is
          Good and Checkpoint is met
TIMEOUT: Terminate the Job if Not completed in "n" Seconds(Not Used Now)
"""
LOG_LEVEL = logging.DEBUG
LOG_FILE = "/dev/stdout"
INTERVAL = 10
TIMEOUT = 60*60  # 60 mins # TODO

# Global Settings and Logging initialization
ParseError = etree.ParseError if hasattr(etree, 'ParseError') else SyntaxError
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
# create the logging file handler
fh = logging.FileHandler(LOG_FILE)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s "
                              "[%(module)s - %(lineno)s:%(funcName)s] "
                              "- %(message)s")

fh.setFormatter(formatter)
logger.addHandler(fh)


class CLIError(IOError):
    """
    Exception for All kinds of CLI Errors, derived from IOError
    Will have errno and errstr
    """
    pass


class GlusterBadXmlFormat(Exception):
    """
    Exception class for XML Parse Errors
    """
    pass


@contextmanager
def mount(volname):
    """
    Context manager for Mounting Gluster Volume
    Use as
        with mount(VOLNAME) as MNT:
            # Do your stuff
    Automatically unmounts it in case of Exceptions/out of context
    """
    mnt = tempfile.mkdtemp(prefix="georep_")
    execute(["mount", "-t", "glusterfs",
             "localhost:/%s" % volname, mnt])
    yield mnt
    execute(["umount", "-l", mnt])


def execute(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    """
    Wrapper to Execute CLI commands. Raises CLIError when return code is non
    zero. Example Usage: execute(["touch", "filename"])
    """
    p = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    (out, err) = p.communicate()
    if p.returncode != 0:
        raise CLIError("[Error %s] %s" % (p.returncode, err))
    return out


def get_bricks(volname):
    """
    Get Volume bricks list
    """
    value = []
    cmd = ["gluster", "volume", "info", volname, "--xml"]
    info = execute(cmd)
    try:
        tree = etree.fromstring(info)
        volume_el = tree.find('volInfo/volumes/volume')
        for b in volume_el.findall('bricks/brick'):
            value.append(b.text)
    except ParseError:
        raise GlusterBadXmlFormat("Bad XML Format: %s" % " ".join(cmd))

    return value


def get_georep_status(mastervol, slavehost, slavevol):
    """
    Get Geo-rep Status
    """
    value = {}
    cmd = ["gluster", "volume", "geo-replication", mastervol,
           "%s::%s" % (slavehost, slavevol), "status", "--xml"]
    info = execute(cmd)
    try:
        tree = etree.fromstring(info)
        session_el = tree.find('geoRep/volume/sessions/session')
        for pair in session_el.findall('pair'):
            master_worker = "%s:%s" % (pair.find("master_node").text,
                                       pair.find("master_brick").text)
            value[master_worker] = {
                "status": pair.find("status").text,
                "checkpoint_status": pair.find("checkpoint_completed").text
            }
    except ParseError:
        raise GlusterBadXmlFormat("Bad XML Format: %s" % " ".join(cmd))

    return value


def is_complete(master_bricks, mastervol, slavehost, slavevol):
    """
    Wrapper function around Geo-rep Status and Gluster Volume Info
    This combines the output from Bricks list and Geo-rep Status.
    If a Master Brick node is down or Status is faulty then increments
    the faulty counter. It also collects the checkpoint status from all
    workers and compares with Number of Bricks.
    """
    checkpoints_complete_count = 0
    num_bricks = len(master_bricks)
    num_faulty = 0

    georep_status = get_georep_status(mastervol, slavehost, slavevol)
    for b in master_bricks:
        if georep_status.get(b, None) is not None:
            if georep_status.get(b)["checkpoint_status"] == "Yes":
                checkpoints_complete_count += 1
            if georep_status.get(b)["status"].lower() == "faulty":
                num_faulty += 1
        else:
            # If a Master Brick node is down
            num_faulty += 1

    return (num_bricks == checkpoints_complete_count), (num_faulty == 0)


def main(mastervol, slavehost, slavevol):
    turns = 1
    master_bricks = get_bricks(mastervol)

    # Set Checkpoint to NOW
    cmd = ["gluster", "volume", "geo-replication", mastervol,
           "%s::%s" % (slavehost, slavevol), "config", "checkpoint", "now"]
    execute(cmd)

    # Start the Geo-replication
    cmd = ["gluster", "volume", "geo-replication", mastervol,
           "%s::%s" % (slavehost, slavevol), "start"]
    execute(cmd)

    # Create a Mount and Touch the Mount point root,
    # Hack to make sure some event available after
    # setting Checkpoint. Without this their is a chance of
    # Checkpoint never completes.
    with mount(mastervol) as mnt:
        execute(["touch", mnt])

    # Loop to Check the Geo-replication Status and Checkpoint
    # If All Status OK and all Checkpoints complete,
    # Stop the Geo-replication and Log the Completeness
    while True:
        checkpoint_complete, ok = is_complete(master_bricks, mastervol,
                                              slavehost, slavevol)
        chkpt_status = "COMPLETE" if checkpoint_complete else "NOT COMPLETE"
        ok_status = "OK" if ok else "NOT OK"
        logger.info("[Turns %s] All Checkpoints %s, All status %s" %
                    (turns, chkpt_status, ok_status))
        if checkpoint_complete:
            logger.info("Stopping Geo-replication session now")
            cmd = ["gluster", "volume", "geo-replication", mastervol,
                   "%s::%s" % (slavehost, slavevol), "stop"]
            execute(cmd)
            break

        if not ok:
            # TODO: Action Item for Faulty state
            logger.error("Geo-rep session is Faulty")

        # Increment the turns and Sleep for 10 sec
        turns += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    except (GlusterBadXmlFormat, CLIError) as e:
        logger.error(e)
        sys.exit(1)
