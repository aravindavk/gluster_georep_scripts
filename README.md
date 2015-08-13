# Scripts related to Gluster Geo-replication

Helper scripts to debug/enhance inbuilt Geo-replication feature of Gluster.

## 1. Schedule Geo-replication
Geo-rep runs continuously once started. It is very difficult to schedule to run once if it is running always. To schedule the steps followed are,

1. Start Geo-replication
2. Set Checkpoint
3. Check the Status and see Checkpoint is Complete.(LOOP)
4. If checkpoint complete, Stop Geo-replication

**Usage:**

    python schedule_georep.py <MASTERVOL> <SLAVEHOST> <SLAVEVOL>

For example,

    python schedule_georep.py gv1 fvm1 gv2


## 2. Gluster Changelog Parser

**Why?** Converts this

    GlusterFS Changelog | version: v1.1 | encoding : 2
    E0b99ef11-4b79-4cd0-9730-b5a0e8c4a8c0^@4^@16877^@0^@0^@00000000-0000-0000-0000-000000000001/dir1^@Ec5250af6-720e-4bfe-b938-827614304f39^@23^@33188^@0^@0^@0b99ef11-4b79-4cd0-9730-b5a0e8c4a8c0/hello.txt^@Dc5250af6-720e-4bfe-b938-827614304f39^@Dc5250af6-720e-4bfe-b938-827614304f39^@

to human readable :)

    E 0b99ef11-4b79-4cd0-9730-b5a0e8c4a8c0 MKDIR 16877 0 0 00000000-0000-0000-0000-000000000001/dir1
    E c5250af6-720e-4bfe-b938-827614304f39 CREATE 33188 0 0 0b99ef11-4b79-4cd0-9730-b5a0e8c4a8c0/hello.txt
    D c5250af6-720e-4bfe-b938-827614304f39
    D c5250af6-720e-4bfe-b938-827614304f39

**Usage:**

    python glusterclparser.py <CHANGELOG_FILE>

For example,

    python glusterclparser.py /bricks/b1/.glusterfs/changelogs/CHANGELOG.1439463377
