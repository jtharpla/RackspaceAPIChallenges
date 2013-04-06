#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 3: Write a script that uses Cloud DNS to create a new A record
#                  when passed a FQDN and IP address as arguments.
#                  Worth 1 Point
#
# Assumptions:
#               Passed FQDN (in the form of rec.domain.tld), and IP as arguments
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

parser = argparse.ArgumentParser(description="Add A record to Cloud DNS domain")
parser.add_argument("fqdn", help="Fully qualified domain name (FQDN) in the format of rec.domain.tld")
parser.add_argument("ipaddr", help="IP address to resolve to")
args = parser.parse_args()

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
dns = pyrax.cloud_dns

# Verify domain.tld is a valid Cloud DNS domain
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

# Verify IP address is in the correct format
if args.ipaddr.count('.') != 3:
    # Not in a.b.c.d IP address format
    print >> sys.stderr, "ERROR: {} is not a valid IP address\n".format(args.ipaddr)
    sys.exit(1)
    
# Could also check that each octet is a valid octet, but this is probably enough
# sanity checking, lets go ahead and add the record...
rec = [{
         "type": "A",
         "name": args.fqdn,
         "data": args.ipaddr,
         "ttl": "300"
         }]
try:
    mydomain.add_records(rec)
except:
    print >> sys.stderr, "ERROR: Unable to add record for {0} pointing to IP address {1}\n".format(args.fqdn, args.ipaddr)
    sys.exit(1)

print "Successfully added new A record to {0} for {1} pointing to IP address {2}\n".format(mydomainname, args.fqdn, args.ipaddr)
