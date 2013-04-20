#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 9: Write an application that when passed the arguments FQDN,
#                 image, and flavor it creates a server of the specified 
#                 image and flavor with the same name as the fqdn, and 
#                 creates a DNS entry for the fqdn pointing to the server's 
#                 public IP. 
#
# Assumptions:
#               Passed image, flavor, and FQDN (in the form of rec.domain.tld)
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

parser = argparse.ArgumentParser(description="Create a server and add to DNS")
parser.add_argument("fqdn", help="Fully qualified domain name (FQDN) in the format of rec.domain.tld")
parser.add_argument("image", help="Image to build server from")
parser.add_argument("flavor", help="Flavor to build server from")
args = parser.parse_args()

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cs = pyrax.cloudservers
dns = pyrax.cloud_dns

# Get flavor and image ids, verify valid image/flavor was specified
try:
    chosen_image = [img for img in cs.images.list()
            if args.image in img.name][0]
            
    chosen_flavor = [flavor for flavor in cs.flavors.list()
            if args.flavor in flavor.name][0]
except:
    print >> sys.stderr, "ERROR: Unable locate image named \"{0}\" and/or flavor named \"{1}\"\n".format(args.image, args.flavor)
    sys.exit(1)

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
    
# Nope, looks good, so create the server
try:
    print "Creating {0} {1} server named {2}, please wait...\n".format(args.flavor, args.image, args.fqdn)
    myserver = cs.servers.create(args.fqdn, chosen_image.id, chosen_flavor.id)
except:
    print >> sys.stderr, "ERROR: Unable to create server named " + servername + "\n"
    
# Wait until server is ACTIVE (but only 30 minutes or 60 attempts @ every 30 secs each)
pyrax.utils.wait_until(myserver, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)

myserver.get() # Refresh server object
if myserver.status == 'ACTIVE' and myserver.networks:
    # Server is active and has networks defined    
    
    # Have to find the IPv4 IP from list of public IPs
    publicip = ""
    for ip in myserver.networks[u'public']:
        if ip.count('.') == 3:
            # Found it!
            publicip = ip
    
    # If we found a valid IPv4 address, add it to DNS
    if publicip:
        rec = [{
                 "type": "A",
                 "name": args.fqdn,
                 "data": publicip,
                 "ttl": "300"
                 }]
        try:
            mydomain.add_records(rec)
        except:
            print >> sys.stderr, "ERROR: Unable to add record for {0} pointing to IP address {1}\n".format(args.fqdn, args.ipaddr)
            sys.exit(1)
    else:
        print >> sys.stderr, "ERROR: No valid IPv4 address found for server named {}\n".format(args.fqdn)
        sys.exit(1)
                
    # Print the details
    print myserver.name + ":"
    print "\tIP address:", publicip
    print "\tAdmin password:", myserver.adminPass
    print 
elif myserver.status == 'ACTIVE' and not myserver.networks:
    # Server is active, but no networking, ack!
    print >> sys.stderr, "ERROR: Server " + myserver.name + " was created without any networks\n"
else:
    # Server failed to finish building, time to deliver the bad news...
    print >> sys.stderr, "ERROR: Server " + myserver.name + " failed to build\n"

    
        
        