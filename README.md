# Scripts related to Gluster Geo-replication

Helper scripts to debug/enhance inbuilt Geo-replication feature of Gluster.

## Schedule Geo-replication
Geo-rep runs continuously once started. It is very difficult to schedule to run once if it is running always. To schedule the steps followed are,

1. Start Geo-replication
2. Set Checkpoint
3. Check the Status and see Checkpoint is Complete.(LOOP)
4. If checkpoint complete, Stop Geo-replication

**Usage:**

    python schedule_georep.py <MASTERVOL> <SLAVEHOST> <SLAVEVOL>

For example,

    python schedule_georep.py gv1 fvm1 gv2

