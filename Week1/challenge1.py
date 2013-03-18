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
import os, sys
import pyrax


######################
"""
main stub
"""
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
        print "Unable to create server named {}".format(servername)
    
# Now loop through created servers, wait until each finishes building, then
# display the name, ip address, and admin password
for server in myservers:
    adminpass = server.adminPass # have to do this before we refresh the server object
    
    # Wait until server is assigned IP addresses
    while not server.networks:
        server = cs.servers.get(server.id)
        
    # Retrieve the public IPv4 address
    publicips = server.networks[u'public']
    
    # Print the details
    print "{0}: addresses are {1}, and admin password is {2} ".format(server.name, publicips, adminpass, )

    
        
        