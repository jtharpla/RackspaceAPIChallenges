#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 7: Write a script that will create 2 Cloud Servers and add 
#                  them as nodes to a new Cloud Load Balancer. Worth 3 Points
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


myservernames = ('c7-web1', 'c7-web2')
mylbname = 'c7-lb-http'
myservers = []
mynodes = []

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cs = pyrax.cloudservers
clb = pyrax.cloud_loadbalancers

# Get flavor and image ids
ubu_image = [img for img in cs.images.list()
        if "Ubuntu 12.04" in img.name][0]
        
flavor_512 = [flavor for flavor in cs.flavors.list()
        if flavor.ram == 512][0]

print "Creating servers..."

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
        privateip = server.networks[u'private'][0] # Servers only have 1 private IP
    
        # Print the details
        print server.name + ":"
        print "\tPublic IP addresses:", ', '.join(str(ip) for ip in publicips)
        print "\tPrivate IP address:", privateip
        print "\tAdmin password:", server.adminPass
        print 
        
        # Create a load balancer node for this server
        mynodes.append(clb.Node(address=privateip, port=80, condition="ENABLED"))
    elif server.status == 'ACTIVE' and not server.networks:
        # Server is active, but no networking, ack!
        print >> sys.stderr, "ERROR: Server " + server.name + " was created without any networks\n"
    else:
        # Server failed to finish building, time to deliver the bad news...
        print >> sys.stderr, "ERROR: Server " + server.name + " failed to build\n"
        
# Now create the load balancer (but only if we have nodes!)
if len(mynodes) > 1:
    print "Creating load balancer..."
    
    # We have nodes to load balance
    try:
        # Get a virtual IP address assigned
        vip = clb.VirtualIP(type="PUBLIC")
        
        # Create the load balancer
        mylb = clb.create(mylbname, port=80, protocol="HTTP",
                           nodes=mynodes, virtual_ips=[vip])
    except:
        print >> sys.stderr, "ERROR: Unable to create Cloud Load Balancer named \"{}\"\n".format(mylbname)
        sys.exit(1)

    # Wait until load balancer is ACTIVE (but only 30 minutes or 60 attempts @ every 30 secs each)
    pyrax.utils.wait_until(mylb, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)
    
    mylb.get() # Refresh lb object
    if mylb.status == 'ACTIVE':
        # load balancer created successfully, print the details
        print mylb.name + ":"
        print "\tVirtual IP:", mylb.virtual_ips[0].address
        print "\tAlgorithm:", mylb.algorithm
        print "\tProtocol:", mylb.protocol
        print "\tNodes:", ', '.join(str(node.address) for node in mynodes)
        print
    else:
        # load balancer ended up in ERROR or create timedout
        print >> sys.stderr, "ERROR: Cloud Load Balancer \"{}\" failed to build\n".format(mylbname)
        sys.exit(1)
else:
    # Not enough servers to build a load balancer for
    print >> sys.stderr, "ERROR: Not enough servers built successfully, aborting creation of \"{}\"\n".format(mylbname)
    sys.exit(1)

    
        
        