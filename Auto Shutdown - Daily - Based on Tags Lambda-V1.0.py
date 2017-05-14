# Created by Anandan Kumaraswamy
#
# Pre-requisites
# --------------
# Mandatory: CBD codes tagged to the EC2.  If CBD code is not passed as parameter,
#   "*All*" instances under the REGION is considered.  Hence, CBD code is mdantory.
#   If No CBD code is passed as parm, the program will terminate.
#
#    A tag *Auto_Shutdown* is required to identify which instances can be
#          Automatically stopped
#
# Event parameters:
#-------------------
#   * CBD
#       CBD code for which the Auto Shutdown needs to be done.
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
#                "ec2:StopInstances",
#            ],
#            "Resource": [
#                "*"
#            ]
#        }
#    ]
#}


import boto3
from datetime import tzinfo, timedelta, datetime
import sys
import json, datetime


def lambda_handler(event, context):
    ec = boto3.resource('ec2')

    # The below hard coded value is used for testing.  Please un-comment the sys.exit line for live
    # Make sure CBD code tag is populated for EC2 instances and passed as parm/event for this function
    # Make sure EC2 instances are tagged with Auto_Shutdown = "Y"

    if 'CBD' in event:
        CBD = event['CBD']
    else:
        CBD = "AK-0031-0670-0310"
        #sys.exit("No CBD code passed as Parm!")
    #currrentTime=datetime.now(tzlocal())

    currrentTime = datetime.datetime.now() - datetime.timedelta(hours=4)
    print("currrentTime.hour %d" %currrentTime.hour)
    if currrentTime.hour >=20:
        print ("CBD Code: %s" % CBD)
        print ("Automatic Shutdown of EC2 instances is in Progress....")
        instances = ec.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']},
                                                {'Name': 'tag:CBD','Values': [CBD]},
                                                {'Name': 'tag:StartStop','Values': ['Auto']},
                                                ])
        print("Instance [%s]" % instances)
        client = boto3.client('ec2')
        for i in instances:
            stopResponse = client.stop_instances(InstanceIds=[i.id])
            waiter = client.get_waiter('instance_stopped')
            print ("The instance %s Successfully Stopped!" % i.id)
    elif currrentTime.hour <= 8 :
        print ("CBD Code: %s" % CBD)
        print ("Automatic Startup of EC2 instances is in Progress....")
        instances = ec.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']},
                                                {'Name': 'tag:CBD','Values': [CBD]},
                                                {'Name': 'tag:StartStop','Values': ['Auto']},
                                                ])
        print("Instance [%s]" % instances)
        client = boto3.client('ec2')
        for i in instances:
            startResponse = client.start_instances(InstanceIds=[i.id])
            waiter = client.get_waiter('instance_running')
            print ("The instance %s Successfully Started!" % i.id)
