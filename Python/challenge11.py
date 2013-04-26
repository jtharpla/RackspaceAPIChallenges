#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 11: Write an application that will:
#                   - Create an SSL terminated load balancer (Create
#                     self-signed certificate.)
#                   - Create a DNS record that should be pointed to 
#                     the load balancer.
#                   - Create Three servers as nodes behind the LB.
#                     Each server should have a CBS volume attached to it.
#                     (Size and type are irrelevant.)
#                     All three servers should have a private Cloud
#                     Network shared between them.
#                   Login information to all three servers returned in a
#                   readable format as the result of the script, 
#                   including connection information.
#
# Assumptions:
#               Passed FQDN (in the form of rec.domain.tld) as argument
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
num_of_servers = 3
server_prefix = "-web"
network_suffix = "-private"
network_cidr = "172.22.200.0/24"
lb_suffix = "-lb-ssl"
vol_suffix = "-vol"

# Using a self-signed cert for *.cldsrvr.com
ssl_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAxueCqNxG25dFJVCjY+egti8EvDncpFAAa8rx3H2D9+xGmd2Y\nuuV9n9W6+MotLDuEAxRPP9/s6nSNEiEOlD/wjDv7xOat3cHaPGy1DS2/XGAPzA1p\nRdamLTOZQ0/O8hiltwvcrZ3Jsq39NexW2zdNMfVtnTIBfhtGo80nwy2cSmZrczDd\nnrC8twbbFwvh/3Qu+asevCwSV/o0VefzTRH+BSKO1v48vU/Rrvd24l7HoyzcqLCZ\nW3VJi0MbBjlZ4TOfxWTmmn/S0FUe3WZeT3V9vrLSoxQtYCSDyq6NLi43skeQIZGS\nIMc0RGcR+XkoeLPKHkZFjor6z/a4hP4wu7ukBQIDAQABAoIBAFrfrsxjR2RQKmEw\nBFZCnyRdOvacIPhZLLgS0omANujwZBksKvlInCqIRZIhHJ5W2qtlfgea0O0VLtaX\nj8efptELHq4JDmqAhKqSp+1Ld2BG6zC4993WgbmpF16veccWB7AnlT0lF9+wqj0W\nq2AgVf57OQdWr2PkJlP0CTSdBAjhD5OGKyJEqnCTqIcalM3Dze6hGzLLougMJDO2\nuOxwm55CJhQaCFK99V11ubw0h/Zwp14wAL8QE1e+NJS5UhxQ/r6H3voXA5iZyFDT\nwNRlKzq3MZdjSYXFoSaZdu+u2X0kqh1Gw2AvTbIUghb1AuszW+kdcyc8qju9G3YU\nVN4xAIkCgYEA8TmtUjnrhd7TE5SzH3p9xmsPrFFIX00Y0FtVlgxs3+QuQ/XXWdbP\nDLffzVOLEYBfQsrxbAp1nEqf+Tn0WC1e0v/zS/yW/+DitNauZZdpp+0zYu0cIaBc\n8M5SxWlgxgAmei1LZUWQdQCrA1w20ABhmI7DPNy33ns3E85cwtUnC5sCgYEA0xZB\novQM+cmza1org8cMOvLJHy1KAnTSRbJIha71lqhEMlbZLnl9Zlt+IXqYgsKT5B+E\niLjw4c0vCgnYtPqmG8sMFkyrMwFAyG26D4dYoiB6UihTCvh48RVng8U7WeSfmIuZ\nZN3tSahu4nNFGYYrYoNXoe++i1JpXXLdu2AGGN8CgYADD/hjUtjqmimT1g9wFt4B\n5toMFfwVOaVW/9HWVdIMBZmQw044lcGLJ8pvkN/zGO4cqvblqDxV/5yITXQMqobJ\npvYvwMUp+nDmWtNb9tAgkaJVXy08QAzuAbCLUQspeFcEtg5++qMa2SdSo5kOivKy\nPR29aA/tgyLv3W7QCmS0gQKBgQDAMkuhK8WEynprDLcCTYJ9SgKGOJ5ijivG+gW+\ncwd6Hcu6aglln4jmYff+U7n5lWFDHM94DayGbGSgJ0cBwhbsx3xB8Z0P29w4om//\nI6U4OYomtECohITaPjr6Z+MafmgyZSlOBiPAJXSRC5OnIdru39gywjAkeu0lASmT\nKmNi0QKBgQCN9imbZtWRTIgoM11xRmK5MO3KKdZ32WTXWfcKFFjqh7cnE3/PWGz/\nFs317RorFaQRAn/gIUQ2dunrHGW+F/01QMT9k5rQoqCSdb1HNprcRN4yt74bvb9W\nkT8oP4n2DfsGAAoCi2ew0M7+ds03CXMsr9yLKBTdOmh//yW3pzAiqw==\n-----END RSA PRIVATE KEY-----\n"
ssl_cert = "-----BEGIN CERTIFICATE-----\nMIIDlTCCAn2gAwIBAgIJALEh9dJxTBZEMA0GCSqGSIb3DQEBBQUAMGExCzAJBgNV\nBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlhMQ8wDQYDVQQHDAZSaWFsdG8xFDAS\nBgNVBAoMC0V4YW1wbGUgSW5jMRYwFAYDVQQDDA0qLmNsZHNydnIuY29tMB4XDTEz\nMDQyNjEzNTg0NloXDTE0MDQyNjEzNTg0NlowYTELMAkGA1UEBhMCVVMxEzARBgNV\nBAgMCkNhbGlmb3JuaWExDzANBgNVBAcMBlJpYWx0bzEUMBIGA1UECgwLRXhhbXBs\nZSBJbmMxFjAUBgNVBAMMDSouY2xkc3J2ci5jb20wggEiMA0GCSqGSIb3DQEBAQUA\nA4IBDwAwggEKAoIBAQDG54Ko3Ebbl0UlUKNj56C2LwS8OdykUABryvHcfYP37EaZ\n3Zi65X2f1br4yi0sO4QDFE8/3+zqdI0SIQ6UP/CMO/vE5q3dwdo8bLUNLb9cYA/M\nDWlF1qYtM5lDT87yGKW3C9ytncmyrf017FbbN00x9W2dMgF+G0ajzSfDLZxKZmtz\nMN2esLy3BtsXC+H/dC75qx68LBJX+jRV5/NNEf4FIo7W/jy9T9Gu93biXsejLNyo\nsJlbdUmLQxsGOVnhM5/FZOaaf9LQVR7dZl5PdX2+stKjFC1gJIPKro0uLjeyR5Ah\nkZIgxzREZxH5eSh4s8oeRkWOivrP9riE/jC7u6QFAgMBAAGjUDBOMB0GA1UdDgQW\nBBS0Q5IT1ctWJ5BYZRftVcgsD0DWUzAfBgNVHSMEGDAWgBS0Q5IT1ctWJ5BYZRft\nVcgsD0DWUzAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4IBAQBT5WkQz+8l\nmgKxeWjQWL7T/UieaM7uMdD1xZqv5tSOHIvRoydywq+VvMtlxJ7dHyLwIS8Ar9eM\nmitiWThq6ws6PHAKsSoufVKAXfmpRxghDXgoBpFw/5efT7QiFwCEbfTU3GY/RFQm\n32tGK0zb73Aluw7EuO0fpk9bpHEld9iQ3M/TBlIXaQOp2AiBerSgzWk/WPwaev7m\nrZ5DboNXNPZ8WFWf7phdcSNUjRtPWmXWgw6HN9qt5GoOf0fi+hZuWb7sWDDBtWwb\nTVkH+YWOBmHk+7RaufjpnmDiSkv6bVMMsVlNFtQHGwXWCEUPib6R/GeOuUUPwJs/\nUzUtLlVfj5CC\n-----END CERTIFICATE-----\n"

parser = argparse.ArgumentParser(description="Create two servers with load balancer and add to DNS")
parser.add_argument("fqdn", help="Fully qualified domain name (FQDN) in the format of rec.domain.tld")
args = parser.parse_args()

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cs = pyrax.cloudservers
clb = pyrax.cloud_loadbalancers
dns = pyrax.cloud_dns
cbs = pyrax.cloud_blockstorage
cnw = pyrax.cloud_networks

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

# Create a private cloud network
mynetworkname = myrecname + network_suffix
try:
    mynetwork = cnw.create(label=mynetworkname, cidr=network_cidr)
except:
    print >> sys.stderr, "ERROR: Unable to create network named \"{0}\" with CIDR of {1}\n".format(mynetworkname, network_cidr)
    sys.exit(1)
networkslist = mynetwork.get_server_networks(public=True, private=True)

# Build a list of server names
for i in range(1, num_of_servers + 1): # range is normally zero indexed
    myservernames.append(myrecname + server_prefix + str(i))

# Create the servers, store as an array of Server objects
print "Creating servers..."
for servername in myservernames:
    try:
        print "Creating " + servername
        myservers.append(cs.servers.create(servername, ubu_image.id, flavor_512.id, nics=networkslist))
    except:
        print >> sys.stderr, "ERROR: Unable to create server named " + servername + "\n"
    
# Now loop through created servers, wait until each finishes building, then
# display the name, ip address, and admin password
print "\n" # adding a newline for better output formatting
for server in myservers:
    # Wait until server is ACTIVE (but only 30 minutes or 60 attempts @ every 30 secs each)
    pyrax.utils.wait_until(server, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)
    
    server.get() # Refresh server object
    if server.status == 'ACTIVE' and server.networks:
        # Server is active and has networks defined, so create the CBS volume    
        volumename = server.name + vol_suffix
        try:
           print "Creating storage volume {0} for {1}".format(volumename, server.name)
           vol = cbs.create(name=volumename, size=100, volume_type='SATA')
        except:
            print >> sys.stderr, "ERROR: Unable to create storage volume {}\n".format(volumename)
            sys.exit(1)
        
        # Attach storage volume to server
        try:
            print "Attaching storage volume {0} to {1}".format(volumename, server.name)
            vol.attach_to_instance(server, mountpoint='/dev/xvdb')
        except:
            print >> sys.stderr, "ERROR: Unable to attach storage volume {0} to {1}\n".format(volumename, server.name)
            sys.exit(1)
        print "Storage volume {} attached successfully".format(volumename)            
               
        # Retrieve the public IPv4 address
        publicips = server.networks[u'public']
        snetip = server.networks[u'private'][0] # Servers only have 1 snet IP
        privateip = server.networks[mynetworkname][0]
    
        # Print the details
        print server.name + ":"
        print "\tPublic IP addresses:", ', '.join(str(ip) for ip in publicips)
        print "\tService Net IP address:", snetip
        print "\tPrivate IP address:", privateip
        print "\tAdmin password:", server.adminPass
        print 
        
        # Create a load balancer node for this server
        mynodes.append(clb.Node(address=snetip, port=80, condition="ENABLED"))
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
        # Add SSL termination to the load balancer
        try:
            print "Adding SSL termination to load balancer..."
            mylb.add_ssl_termination(
                                     securePort=443,
                                     enabled=True,
                                     secureTrafficOnly=False,
                                     certificate=ssl_cert,
                                     privatekey=ssl_key)
        except:
            print >> sys.stderr, "ERROR: Unable to add SSL termination to Cloud Load Balancer \"{}\"\n".format(mylb.name)
            sys.exit(1)
        
        # Wait until LB has updated (but only 30 minutes or 60 attempts @ every 30 secs each)
        pyrax.utils.wait_until(mylb, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)
        print "SSL termination added successfully\n"
        
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