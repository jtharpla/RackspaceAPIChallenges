#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 1: Write a script that builds three 512 MB Cloud Servers that
#                following a similar naming convention. (ie., web1, web2, web3)
#                and returns the IP and login credentials for each server. Use
#                any image you want.
#
# Assumptions:
#               .rackspace_cloud_credentials is a file in ini format with a
#               single section.  Format is as follows:
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
import os, sys
import pyrax


myservernames = ('web1', 'web2', 'web3')
myservers = []

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cs = pyrax.cloudservers

# Get flavor and image ids
ubu_image = [img for img in cs.images.list()
        if "Ubuntu 12.04" in img.name][0]
        
flavor_512 = [flavor for flavor in cs.flavors.list()
        if flavor.ram == 512][0]

# Create the servers, store as an array of Server objects
for servername in myservernames:
    try:
        myservers.append(cs.servers.create(servername, ubu_image.id, flavor_512.id))
    except:
        print >> sys.stderr, "ERROR: Unable to create server named " + servername + "\n"
    
# Now loop through created servers, wait until each finishes building, then
# display the name, ip address, and admin password
for server in myservers:
    # Wait until server is ACTIVE (but only 30 minutes or 60 attempts @ every 30 secs each)
    pyrax.utils.wait_until(server, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)
    
    server.get() # Refresh server object
    if server.status == 'ACTIVE' and server.networks:
        # Server is active and has networks defined    
        
        # Retrieve the public IPv4 address
        publicips = server.networks[u'public']
    
        # Print the details
        print server.name + ":"
        print "\tIP addresses:", ', '.join(str(ip) for ip in publicips)
        print "\tAdmin password:", server.adminPass
        print 
    elif server.status == 'ACTIVE' and not server.networks:
        # Server is active, but no networking, ack!
        print >> sys.stderr, "ERROR: Server " + server.name + " was created without any networks\n"
    else:
        # Server failed to finish building, time to deliver the bad news...
        print >> sys.stderr, "ERROR: Server " + server.name + " failed to build\n"

    
        
        