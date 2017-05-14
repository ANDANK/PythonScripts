# This script has been modified and customized from the below githut source.
# AWS auto snapshot script - 2015-10-09
# https://github.com/viyh/aws-scripts
#
# Modified by Anandan Kumaraswamy
#
# Pre-requisites
# --------------
# Mandatory: CBD codes tagged to the EC2.  If CBD code is not passed as parameter,
#   "*All*" instances under the REGION is considered.  Hence, CBD code is mdantory.
#   If No CBD code is passed as parm, the program will terminate.
# Optional: A tag *Backup* is required to identify which volumes are required for
#     snapshot and move the snapshot to DR region.  If Backup tag NOT found, the
#     volume is skipped from being snapshot and hence no DR available.
#
# Event parameters:
#-------------------
#   * regions (default: [region where Lambda function is running])
#       Source region
#   *  DR Region (default: us-west-1)
#        DR region where the snap shot needs to be copied for DR purpusoes.
#   * retention_days (default: 7)
#       integer number of days to keep snapshots
#   * CBD
#       CBD code for which the snapshot needs to be backed up in DR region
#
#
# Permisions required:  (In PoC use the role: "LambdaSnapshot_Role")
# -------------------------------------------------------------------
#{
#    "Version": "2012-10-17",
#    "Statement": [
#        {
#            "Sid": "Stmt1426256275000",
#            "Effect": "Allow",
#            "Action": [
#                "ec2:CreateSnapshot",
#                "ec2:CreateTags",
#                "ec2:DeleteSnapshot",
#                "ec2:DescribeSnapshots",
#                "ec2:DescribeVolumes",
#                "ec2:DescribeInstances",
#                "ec2:ModifySnapshotAttribute",
#                "ec2:CopySnapshot"
#            ],
#            "Resource": [
#                "*"
#            ]
#        }
#    ]
#}


import boto3
import json, datetime
from datetime import tzinfo, timedelta, datetime
import sys


def lambda_handler(event, context):
    global DRregions
    global CBD

    if 'regions' in event:
        regions = event['regions']
    else:
        regions = [context.invoked_function_arn.split(':')[3]]

    if 'DRregions' in event:
        DRregions = event['DRregions']
    else:
        DRregions = "us-west-1"

    if 'retention_days' in event:
        retention_days = event['retention_days']
    else:
        retention_days = 7

# The below hard coded value is used for testing.  Please un-comment the sys.exit line for live
# Make sure CBD code tag is populated for EC2 instances and passed as parm/event for this function
# Make sure volumes are tagged with Backup "Y".
    if 'CBD' in event:
        CBD = event['CBD']
    else:
        CBD = "AK-0031-0670-0310"
        #sys.exit("No CBD code passed as Parm!")

# If needed App_Name can be passed.  This needs further code change.
    #if 'App_Name' in event:
    #    App_Name = event['App_name']

    print("AWS snapshot backups stated at %s...\n" % datetime.now())
    for region in regions:
        print("Region: %s" % region)
        create_region_snapshots(region, retention_days,DRregions)
    print("\nAWS snapshot backups completed at %s\n" % datetime.now())

# create snapshot for (a) EC2 instances matching the CBD code and (b) Volumes having Backup as "Y"
def create_region_snapshots(region, retention_days, DRregions):
    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']},
                                              {'Name': 'tag:CBD','Values': [CBD]}])
    print ("Instances %s" %instances)
    for i in instances:
        #instance_name = filter(lambda tag: tag['Key'] == 'Name', i.tags)[0]['Value']
        #print("\t%s - %s" % (instance_name, i.id))
        print ("i = %s" % i)
        volumes = ec2.volumes.filter(Filters=[{'Name': 'attachment.instance-id', 'Values': [i.id]},
                                              {'Name': 'tag:Backup','Values': ['Y']}])
        snapshot_volumes(region, retention_days, volumes,DRregions)

# create and prune snapshots for volume.  # Prune is disable at this point.
def snapshot_volumes(region, retention_days, volumes, DRregions):
    for v in volumes:
        print("\t\tVolume found: \t%s" % v.volume_id)
        create_volume_snapshot(region, v,DRregions)
        #prune_volume_snapshots(retention_days, v)

# create snapshot for volume.  Tags are created for the snapshot
def create_volume_snapshot(region, volume,DRregions):
    description = 'autosnap-%s.%s.%s-%s' % (region, CBD, volume.volume_id,
        datetime.now().strftime("%Y%m%d-%H%M%S") )
    snapshot = volume.create_snapshot(Description=description)
    if snapshot:
        snapshot.create_tags(Tags=[{'Key': 'Name', 'Value': description}])
        print("\t\t\tSnapshot created with description [%s]" % description)
        copy_snapshot_cross_region(snapshot, description,region,DRregions)

# Copy the snapshot to cross region for DR
def copy_snapshot_cross_region(snapshot, description,regions, DRregions):
    ec2 = boto3.resource('ec2', region_name=regions)
    print("Waiting for the SnapShot to Complete.......")
    client = boto3.client('ec2')
    waiter = client.get_waiter('snapshot_completed')
    waiter.wait(SnapshotIds=[snapshot.id])
    print("Snapshot Complete!")

    modifyatt = client.modify_snapshot_attribute(
        SnapshotId = snapshot.id,
        Attribute = 'createVolumePermission',
        OperationType = 'add' ,
        GroupNames = ['all']
    )
    print ("Snaphot attribute modified..")
# Copy Snapshot was not copied to Destination Region at the point of testing.
    description = "DR-copy-" + description
    client = boto3.client('ec2', region_name=DRregions)
    copysnapshot = client.copy_snapshot(
        DestinationRegion = DRregions,
        SourceRegion = regions,
        SourceSnapshotId = snapshot.id,
        Description = description
    )
    print ("Snapshot copied %s" % copysnapshot)

    if copysnapshot:
        print("Snapshot copy initiated to DRregions: %s" % DRregions)
        print("Validate the snapshot copy in DR region")


# find and delete snapshots older than retention_days
#def prune_volume_snapshots(retention_days, volume):
#    for s in volume.snapshots.all():
#        now = datetime.now(s.start_time.tzinfo)
#        old_snapshot = ( now - s.start_time ) > timedelta(days=retention_days)
#        if not old_snapshot or not s.description.startswith('autosnap-'): continue
#        print("\t\t\tDeleting snapshot [%s - %s] created [%s]" % ( s.snapshot_id, s.description, str( s.start_time )))
#        s.delete()
