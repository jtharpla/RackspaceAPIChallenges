#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 6: Write a script that creates a CDN-enabled container in
#                  Cloud Files.
#
# Assumptions:
#               Passed container name as argument
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
import os, sys, time, argparse
import pyrax

parser = argparse.ArgumentParser(description="Create a CDN-enabled Cloud Files container")
parser.add_argument("containername", help="Name of Cloud Files container")
args = parser.parse_args()

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cf = pyrax.cloudfiles

# Create container if it does not already exist
containerExists = False
for name in cf.list_containers():
    if name == args.containername:
        containerExists = True
        break # Found it, no need to continue

if not containerExists:
    # Didn't find it, so create it
    try:
        mycontainer = cf.create_container(args.containername)
    except:
        print >> sys.stderr, "ERROR: Unable to create container named \"{}\"\n".format(args.containername)
        sys.exit(1)
else:
    # Already exists, let the user know this
    print >> sys.stderr, "WARNING: container named \"{}\" already exists, making public\n".format(args.containername)
    mycontainer = cf.get_container(args.containername)
    
# Now make container CDN enabled.
if mycontainer.cdn_enabled:
    # Already CDN enabled, nothing to do
    print >> sys.stderr, "ERROR: container named \"{}\" is already CDN enabled, nothing to do!\n".format(args.containername)
    sys.exit(1)
else:
    # Ok, enough sanity checking, lets make the container public, shall we?
    try:
        mycontainer.make_public(ttl=900)
        mycdnmetadata = cf.get_container_cdn_metadata(mycontainer)
    except:
        print >> sys.stderr, "ERROR: Unable to make container \"{}\" public!\n".format(args.containername)
        sys.exit(1)
    
    # Successfully made public, print the details
    print "Container named \"{}\" successfully published to the CDN with the following URLs:".format(args.containername)
    print "\tCDN URL:\t\t" + mycdnmetadata["x-cdn-uri"]
    print "\tCDN SSL URL:\t\t" + mycdnmetadata["x-cdn-ssl-uri"]
    print "\tCDN Streaming URL:\t" + mycdnmetadata["x-cdn-streaming-uri"]
    print "\tCDN iOS URL:\t\t" + mycdnmetadata["x-cdn-ios-uri"]

    
    