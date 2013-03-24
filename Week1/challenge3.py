#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 3: Write a script that accepts a directory as an argument as
#                  well as a container name. The script should upload the 
#                  contents of the specified directory to the container
#                 (or create it if it doesn't exist). The script should 
#                 handle errors appropriately. (Check for invalid paths,
#                 etc.) Worth 2 Points
#
# Assumptions:
#               Passed directory path, container name as arguments
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
import os, sys, time
import pyrax

if len(sys.argv) < 2:
    # Check that required number of arguments have been supplied
    print >> sys.stderr, "Usage: {} SOURCEFOLDERPATH DESTCONTAINER\n".format(sys.argv[0])
    sys.exit(1)

source_folderpath = sys.argv[1]
dest_containername = sys.argv[2]

if not os.path.exists(source_folderpath):
    # Check that this is a valid path (will also fail if we don't have permissions)
    print >> sys.stderr, "ERROR: {} does not exist or is not accessible\n".format(source_folderpath)
    sys.exit(1)

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cf = pyrax.cloudfiles

# Start the upload (asynchronously)
print "Uploading {0} to container \"{1}\"...".format(source_folderpath, dest_containername)
try:
    upload_key, total_bytes = cf.upload_folder(source_folderpath, dest_containername)
except:
    print >> sys.stderr, "ERROR: Unable to upload {0} to container named \"{1}\"".format(source_folderpath, dest_containername)
    sys.exit(1)
 
# Monitor and report progress of upload.. 
uploaded_bytes = cf.get_uploaded(upload_key)    
while uploaded_bytes < total_bytes:
    uploaded_pct = int(round(((1.0 * uploaded_bytes / total_bytes) * 100), 0))
    print "{}% uploaded...".format(uploaded_pct)
    time.sleep(30) # Avoid overloading the API, only check every 30 secs
    uploaded_bytes = cf.get_uploaded(upload_key)
    
if uploaded_bytes == total_bytes:
    # One more check, make sure all the bits got there
    print "Upload of {0} to container \"{1}\" complete!".format(source_folderpath, dest_containername)
else:
    print >> sys.stderr, "ERROR: Unable to upload {0} to container named \"{1}\"".format(source_folderpath, dest_containername)
    sys.exit(1)