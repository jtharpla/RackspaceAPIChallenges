#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 8: Write a script that will create a static webpage served out 
#                 of Cloud Files. The script must create a new container, cdn
#                 enable it, enable it to serve an index file, create an index
#                 file object, upload the object to the container, and create
#                 a CNAME record pointing to the CDN URL of the container.
#                 Worth 3 Points
#
# Assumptions:
#               Passed container name and cname fqdn as arguments
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

indexpage = """<html><head>
<title>Geoff Metcalf</title>
</head>
<body>
<!-- BEGIN PAGE CONTENTS HERE -->
<center><h1>The Dangers of Bread</h1></center>
<p>A recent Cincinnati Enquirer headline read, "Smell of baked bread
may be health hazard." The article went on to describe the dangers of
the smell of baking bread. The main danger, apparently, is that the
organic components of this aroma may break down ozone (I'm not making
this stuff up).

</p><p>I was horrified. When are we going to do something about bread-
induced global warming? Sure, we attack tobacco companies, but
when is the government going to go after Big Bread?

</p><p>Well, I've done a little research, and what I've discovered should
make anyone think twice....

</p><ol>

<li>More than 98 percent of convicted felons are bread eaters.

</li><li>Fully HALF of all children who grow up in bread-consuming
households score below average on standardized tests.

</li><li>In the 18th century, when virtually all bread was baked in the
home, the average life expectancy was less than 50 years; infant
mortality rates were unacceptably high; many women died in
childbirth; and diseases such as typhoid, yellow fever and influenza
ravaged whole nations.

</li><li>More than 90 percent of violent crimes are committed within 24
hours of eating bread.

</li><li>Bread is made from a substance called "dough." It has been proven
that as little as one pound of dough can be used to suffocate a
mouse.  The average American eats more bread than that in one month!

</li><li>Primitive tribal societies that have no bread exhibit a low
occurrence of cancer, Alzheimer's, Parkinson's disease and
osteoporosis.

</li><li>Bread has been proven to be addictive. Subjects deprived of bread
and given only water to eat begged for bread after only two days.

</li><li>Bread is often a "gateway" food item, leading the user to
"harder" items such as butter, jelly, peanut butter and even cold
cuts.

</li><li>Bread has been proven to absorb water. Since the human body is
more than 90 percent water, it follows that eating bread could lead to
your body being taken over by this absorptive food product, turning you
into a soggy, gooey bread-pudding person.

</li><li>Newborn babies can choke on bread.

</li><li>Bread is baked at temperatures as high as 400 degrees
Fahrenheit! That kind of heat can kill an adult in less than one
minute.

</li><li>Most American bread eaters are utterly unable to distinguish
between significant scientific fact and meaningless statistical
babbling.

</li></ol>

<p>In light of these frightening statistics, we propose the following
bread restrictions:

</p><ol>

<li>No sale of bread to minors.

</li><li>No advertising of bread within 1000 feet of a school.

</li><li>A 300 percent federal tax on all bread to pay for all the
societal ills we might associate with bread.

</li><li>No animal or human images, nor any primary colors (which may
appeal to children) may be used to promote bread usage.

</li><li>A $4.2 zillion fine on the three biggest bread manufacturers.
Please send this e-mail on to everyone you know who cares about this
crucial issue.

</li></ol>
<!-- END OF PAGE CONTENTS -->
</body></html>"""

parser = argparse.ArgumentParser(description="Create a static web site using a CDN-enabled Cloud Files container")
parser.add_argument("containername", help="Name of Cloud Files container")
parser.add_argument("cname_fqdn", help="Fully qualified domain name (FQDN) to use as a CNAME in the format of rec.domain.tld")
args = parser.parse_args()

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cf = pyrax.cloudfiles
dns = pyrax.cloud_dns

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
    print >> sys.stderr, "WARNING: container named \"{}\" is already CDN enabled\n".format(args.containername)
    mycdnmetadata = cf.get_container_cdn_metadata(mycontainer)
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
    print
    
# Now that the container is CDN-enabled, add an index page and configure as a static site
print "Uploading index page..."
mycontainer.set_web_index_page("index.html")

try:
    mycontainer.store_object("index.html", indexpage, content_type="text/html")
except:
    print >> sys.stderr, "ERROR: Unable to upload index page\n"
    sys.exit(1)

print "Upload complete, adding CNAME to DNS..."
    
# Finally, add the CNAME
# Verify domain.tld is a valid Cloud DNS domain
if args.cname_fqdn.count('.') != 2:
    # FQDN is not in the format of rec.domain.tld
    print >> sys.stderr, "ERROR: FQDN {} is not in a valid rec.domain.tld format\n".format(args.cname_fqdn)
    sys.exit(1)
myrecname, mydomainname = args.cname_fqdn.split('.', 1)
try:
    mydomain = dns.findall(name=mydomainname)[0] # .findall() returns a list, just using the first result
except:
    print >> sys.stderr, "ERROR: Unable to find domain {} in Cloud DNS\n".format(mydomainname)
    sys.exit(1)

# Create CNAME record and add it...
rec = [{
         "type": "CNAME",
         "name": args.cname_fqdn,
         "data": mycdnmetadata["x-cdn-uri"][7:], # Need to remove http://
         "ttl": "300"
         }]
try:
    mydomain.add_records(rec)
except:
    print >> sys.stderr, "ERROR: Unable to add record for {0} pointing to CDN URL {1}\n".format(args.cname_fqdn, mycdnmetadata["x-cdn-uri"])
    sys.exit(1)

print "Added new CNAME record to {0} for {1} pointing to CDN URL {2}\n".format(mydomainname, args.cname_fqdn, mycdnmetadata["x-cdn-uri"])
print
print "New static web site http://{}/ successfully created".format(args.cname_fqdn)
    


    
    