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

To use this as library,

	import glusterclparser

	def parse_record(record):
		print record

	glusterclparser.parse("/bricks/b1/.glusterfs/changelogs/CHANGELOG.1439463377",
	                      callback=parse_record)

Attributes of record,

	record.ts		= Timestamp(Changelog file suffix)
	record.fop_type = E/D/M (Entry, Data, Meta)
	record.gfid		= GFID
	record.path		= Parent GFID/BASENAME
	record.fop		= FOP Type, CREATE, MKDIR etc
	record.path1	= Old Parent GFID/BASENAME in case of RENAME
	record.path2	= New Parent GFID/BASENAME in case of RENAME
	record.mode		= Mode if FOP is CREATE, MKNOD, MKDIR
	record.uid		= UID if FOP is CREATE, MKNOD, MKDIR
	record.gid		= GID if FOP is CREATE, MKNOD, MKDIR


## 3. Helper Tool to find GFID

To get GFID of a file(works both in Gluster Mount and in Backend)

    python georephelper.py gfid <PATH>

For example,

    python georephelper.py gfid /mnt/gv1/f1
    python georephelper.py gfid /bricks/b2/f1


## 4. Helper Tool to find Xtime

To get xtime of a file or dir,

    python georephelper.py xtime <PATH> <MASTER UUID>

For example,

    python georephelper.py xtime /mnt/gv1/f1 346d1076-05b6-4a59-9947-1e7d31a66294
    python georephelper.py xtime /bricks/b2/f1 346d1076-05b6-4a59-9947-1e7d31a66294


## 5. Helper Tool to find Stime

To get stime of a file or dir,

    python georephelper.py stime <PATH> <MASTER UUID> <SLAVE UUID>

For example,

    python georephelper.py stime /mnt/gv1/ 346d1076-05b6-4a59-9947-1e7d31a66294 169b8fbd-e1ec-419d-af63-215eaf69d621
    python georephelper.py stime /bricks/b2 346d1076-05b6-4a59-9947-1e7d31a66294 169b8fbd-e1ec-419d-af63-215eaf69d621

## 6. Helper Tool to get Volume Mark from Master

Mount the Master Volume with Client PID -1, For example,

    glusterfs --aux-gfid-mount --acl --volfile-server=localhost --volfile-id=gv1 --client-pid=-1 /mnt/gv1

Run georephelper to get Volmark details,

    python georephelper.py volmarkmaster <MOUNT_PATH>

For example,

    python georephelper.py volmarkmaster /mnt/gv1


## 7. Helper Tool to get Volume Mark from Slave

Run georephelper to get Volmark details,

    python georephelper.py volmarkslave <MOUNT_PATH>

For example,

    python georephelper.py volmarkslave /mnt/gv2
