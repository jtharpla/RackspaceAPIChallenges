#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 5: Write a script that creates a Cloud Database instance. This
#                 instance should contain at least one database, and the 
#                 database should have at least one user that can connect to it.
#
# Assumptions:
#               .rackspace_cloud_credentials is a file in ini format
#               with a single section. Format is as follows:
#
#                    [rackspace_cloud]
#                    username=<cloud account username>
#                    api_key=<cloud account api key>
#
# Copyright 2013 Jeff Tharp
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License
#
import os, sys, time,argparse
import pyrax

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cdb = pyrax.cloud_databases

parser = argparse.ArgumentParser(description="Create a Cloud Databases instance with a database and database user")
parser.add_argument("instancename", help="Name of the Cloud Databases instance")
parser.add_argument("dbname", help="Name of database to create within the Cloud Databases instance")
parser.add_argument("username", help="Username to connect to the database")
parser.add_argument("password", help="Password to connect to the database")

args = parser.parse_args()

try:
    mycdb_inst = cdb.create(args.instancename, flavor=u'512MB Instance', volume=1)
except:
    print >> sys.stderr, "ERROR: Unable to create new Cloud Databases instance named " + args.instancename + "\n"
    sys.exit(1)

# Wait until instance is ACTIVE/ERROR (but only 30 minutes or 60 attempts @ every 30 secs each)
pyrax.utils.wait_until(mycdb_inst, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)

mycdb_inst.get() # Refresh Cloud DB instance object
if mycdb_inst.status == 'ACTIVE':
    # Instance created successfully, lets create the database
    try:
        mycdb_database = mycdb_inst.create_database(args.dbname)
    except:
        print >> sys.stderr, "ERROR: Unable to create database named {0} within Cloud Databases instance named {1}\n".format(args.dbname, args.instancename)
        sys.exit(1)
        
    # Database created, add user
    try:
        mycdb_inst.create_user(name=args.username, password=args.password, database_names=[args.dbname])
    except:
        print >> sys.stderr, "ERROR: Unable able to create user {0} with password {1} for accessing {2}\n".format(args.username, args.password, args.dbname)
        sys.exit(1)
else:
    print >> sys.stderr, "ERROR: Cloud Databases instance named " + args.instancename + " failed to build.\n"
    sys.exit(1)
    
# If we reach here, the instance, database, and user all created successfully, so let's return the info to connect
print "Successfully created Cloud Databases instance named {0} and database named {1}".format(args.instancename, args.dbname)
print "\tHostname:", mycdb_inst.hostname
print "\tDatabase:", args.dbname
print "\tUsername:", args.username
print "\tPassword:", args.password
 


