# PythonScripts
<Heading> Simple Lambda Scripts written in Python. </Heading>


Auto Shutdown - Daily - Based on Tags Lambda-V1.0

This script is a Lambda Function.  This Script is used to Shutdown the EC2 instances between 8PM EST and 11:59PM EST.  The shutdown of instances take place based on the time of the script scheduled.  


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
