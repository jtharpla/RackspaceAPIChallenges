#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 10: Write an application that will:
#                   - Create 2 servers, supplying a ssh key to be installed at
#                     /root/.ssh/authorized_keys.
#                   - Create a load balancer
#                   - Add the 2 new servers to the LB
#                   - Set up LB monitor and custom error page.
#                   - Create a DNS record based on a FQDN for the LB VIP.
#                   - Write the error page html to a file in cloud files for
#                     backup.
#
# Assumptions:
#               Passed ssh pubkey file and FQDN (in the form of rec.domain.tld)
#               as arguments
#
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
import os, sys, argparse
import pyrax

myservernames = []
myservers = []
mynodes = []
num_of_servers = 2
server_prefix = "-web"
lb_suffix = "-lb-http"
container_suffix = "-errorpage"
errorpage="""<html><head>
<title>Danger Will Robinson, Danger!</title></head>
<body><h1><blink>Danger Will Robinson, Danger!</blink></h1>
</body></html>"""

parser = argparse.ArgumentParser(description="Create two servers with load balancer and add to DNS")
parser.add_argument("fqdn", help="Fully qualified domain name (FQDN) in the format of rec.domain.tld")
parser.add_argument("sshkey", help="SSH public key file")
args = parser.parse_args()


# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"), region='ORD')
cs = pyrax.cloudservers
clb = pyrax.cloud_loadbalancers
dns = pyrax.cloud_dns
cf = pyrax.cloudfiles

# Get flavor and image ids
ubu_image = [img for img in cs.images.list()
        if "Ubuntu 12.04" in img.name][0]
        
flavor_512 = [flavor for flavor in cs.flavors.list()
        if flavor.ram == 512][0]

# Verify valid FQDN was specified
# ...first, is domain.tld is a valid Cloud DNS domain
if args.fqdn.count('.') != 2:
    # FQDN is not in the format of rec.domain.tld
    print >> sys.stderr, "ERROR: FQDN {} is not in a valid rec.domain.tld format\n".format(args.fqdn)
    sys.exit(1)
myrecname, mydomainname = args.fqdn.split('.', 1)
try:
    mydomain = dns.findall(name=mydomainname)[0] # .findall() returns a list, just using the first result
except:
    print >> sys.stderr, "ERROR: Unable to find domain {} in Cloud DNS\n".format(mydomainname)
    sys.exit(1)
    
#...next check if FQDN already exists in DNS
if mydomain.search_records(record_type="CNAME", name=args.fqdn):
    print >> sys.stderr, "ERROR: Found existing CNAME record for {}\n".format(args.fqdn)
    sys.exit(1)
elif mydomain.search_records(record_type="A", name=args.fqdn):
    print >> sys.stderr, "ERROR: Found existing A record for {}\n".format(args.fqdn)
    sys.exit(1)

# Build a list of server names
for i in range(1, num_of_servers + 1): # range is normally zero indexed
    myservernames.append(myrecname + server_prefix + str(i))
    
# Verify that ssh key is a valid file
if not os.path.isfile(args.sshkey):
    print >> sys.stderr, "ERROR: Unable to access SSH key {}\n".format(args.sshkey)
    sys.exit(1)
else:  
    myfiles = {"/root/.ssh/authorized_keys": open(args.sshkey, 'r')}

# Create the servers, store as an array of Server objects
print "Creating servers..."
for servername in myservernames:
    try:
        myservers.append(cs.servers.create(servername, ubu_image.id, flavor_512.id, files=myfiles))
    except:
        e = sys.exc_info()[0]
        print >> sys.stderr, "ERROR: Unable to create server named " + servername + "\n"
        print >> sys.stderr, "ERROR: {}\n".format(e)

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
mylbname = myrecname + lb_suffix
mylbvip = ""
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
    mylbvip = mylb.virtual_ips[0].address
    if mylb.status == 'ACTIVE':
        # load balancer created successfully, print the details
        print mylb.name + ":"
        print "\tVirtual IP:", mylbvip
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

# Add a health monitor and custom error page to the load balancer
if mylb:
    mylb.add_health_monitor(type="HTTP", path="/",  
                            statusRegex="^[234][0-9][0-9]$",
                            bodyRegex="^[234][0-9][0-9]$",
                            delay=10, timeout=5, attemptsBeforeDeactivation=3)
    # Have to wait for health monitor change to complete before setting 
    # error page, so wait_until (but only 30 minutes or 60 attempts @ every 30 secs each)
    pyrax.utils.wait_until(mylb, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)
    mylb.set_error_page(errorpage)

# Next add the DNS if we have an assigned virtual IP for the LB
print "Adding record to DNS..."
if mylbvip: 
    rec = [{
             "type": "A",
             "name": args.fqdn,
             "data": mylbvip,
             "ttl": "300"
             }]
    try:
        mydomain.add_records(rec)
    except:
        print >> sys.stderr, "ERROR: Unable to add record for {0} pointing to virtual IP address {1}\n".format(args.fqdn, mylbvip)
        sys.exit(1)
else:
    print >> sys.stderr, "ERROR: No valid virtual IP address found for load balancer named {}\n".format(mylbname)
    sys.exit(1)
print "Successfully added an A record for {0} pointing to virtual IP {1}".format(args.fqdn, mylbvip)

# Store a backup of the error doc in Cloud Files
# Create container if it does not already exist
containername = myrecname + container_suffix
containerExists = False
for name in cf.list_containers():
    if name == containername:
        containerExists = True
        break # Found it, no need to continue

if not containerExists:
    # Didn't find it, so create it
    try:
        mycontainer = cf.create_container(containername)
    except:
        print >> sys.stderr, "ERROR: Unable to create container named \"{}\"\n".format(containername)
        sys.exit(1)
else:
    # Container already exists
    print >> sys.stderr, "ERROR: container named \"{}\" already exists\n".format(containername)
    sys.exit(1)
    
# Now upload a copy of the error page...
try:
    mycontainer.store_object("error.html", errorpage, content_type="text/html")
except:
    print >> sys.stderr, "ERROR: Unable to upload error page\n"
    sys.exit(1)

print "\nA backup of the error page has been saved to the Cloud Files container named \"{}\"\n".format(containername)
    
    
        
        