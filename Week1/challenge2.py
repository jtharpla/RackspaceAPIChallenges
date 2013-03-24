#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 2: Write a script that clones a server (takes an image and 
#                deploys the image as a new server). Worth 2 Point
#
# Assumptions:
#               A server named web1 exists, .rackspace_cloud_credentials is a 
#               file in ini format with a single section. Format is as follows:
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
from time import gmtime, strftime

import pyrax


source_servername ='web1'
clone_servername = 'web4'
imagename_prefix = 'challenge2-web1-image-'

# Get the credentials
pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"))
cs = pyrax.cloudservers

# Add timestamp to image name
timestamp = strftime("%Y%m%d%H%M%S", gmtime())
imagename = imagename_prefix + timestamp

# According to PyRax docs, at this point I should be able to do:
#     cs.servers.create_image(source_servername, imagename)
#
# buuuuuut, novaclient says Nope! ...
#
#Traceback (most recent call last):
#  File "C:\Users\jeff4440\git\RackspaceAPIChallenges\Week1\challenge2.py", line 40, in <module>
#    cs.servers.create_image("web1", "test")
#  File "C:\Python27\lib\site-packages\novaclient\v1_1\servers.py", line 689, in create_image
#    resp = self._action('createImage', server, body)[0]
#  File "C:\Python27\lib\site-packages\novaclient\v1_1\servers.py", line 812, in _action
#    return self.api.client.post(url, body=body)
#  File "C:\Python27\lib\site-packages\novaclient\client.py", line 230, in post
#    return self._cs_request(url, 'POST', **kwargs)
#  File "C:\Python27\lib\site-packages\novaclient\client.py", line 214, in _cs_request
#    **kwargs)
#  File "C:\Python27\lib\site-packages\novaclient\client.py", line 196, in _time_request
#    resp, body = self.request(url, method, **kwargs)
#  File "C:\Python27\lib\site-packages\novaclient\client.py", line 190, in request
#    raise exceptions.from_response(resp, body, url, method)
#novaclient.exceptions.NotFound: Instance could not be found (HTTP 404) (Request-ID: req-bda58814-3377-4206-adc4-cadc62020229) 
#
# ....*sigh*...so now we gotta do it the hard way...
#

newimageid = ""
for server in cs.servers.list():
    # Yup, we're going to have to search the whole list to find the server by name...
    if server.name == source_servername:
        # Found the server in the list, now create an image
        try:
            print "Creating image of {0} named {1}...\n".format(source_servername, imagename)
            newimageid = server.create_image(imagename)
            break # We're done, no need to iterate over the rest of the list :-)
        except:
            print >> sys.stderr, "ERROR: Unable to create image of ", source_servername, "\n"
            sys.exit(1)
 
if not newimageid:
    print >> sys.stderr, "ERROR: Unable to create image of ", source_servername, "\n"
    sys.exit(1)

# And now we wait...but only for up to a half hour (= 60 attempts @ every 30 secs each)
newimage = cs.images.get(newimageid)
pyrax.utils.wait_until(newimage, 'status', 'ACTIVE', interval=30, attempts=60)
newimage.get() # Need to refresh to update status

# Abort if we do not have a good image
if newimage.status != 'ACTIVE':
    print >> sys.stderr, "ERROR: Creation of image named ", imagename, " failed\n"
    sys.exit(1)

# Get flavor of the source server
source_flavor = server.flavor['id']

# Create the clone server
try:
    print "Creating clone of {0} named {1}...\n".format(source_servername, clone_servername)
    clone_server = cs.servers.create(clone_servername, newimageid, source_flavor)
except:
    print >> sys.stderr, "ERROR: Unable to create server named " + clone_servername + "\n"
    
# Wait until server is ACTIVE/ERROR (but only 30 minutes or 60 attempts @ every 30 secs each)
pyrax.utils.wait_until(clone_server, 'status', ['ACTIVE', 'ERROR'], interval=30, attempts=60)

clone_server.get() # Refresh server object
if clone_server.status == 'ACTIVE' and clone_server.networks:
    # Server is active and has networks defined    
    
    # Retrieve the public IPv4 address
    publicips = clone_server.networks[u'public']

    # Print the details
    print clone_servername + ":"
    print "\tIP addresses:", ', '.join(str(ip) for ip in publicips)
    print "\tAdmin password:", clone_server.adminPass
    print 
elif clone_server.status == 'ACTIVE' and not clone_server.networks:
    # Server is active, but no networking, ack!
    print >> sys.stderr, "ERROR: Server " + clone_servername + " was created without any networks\n"
else:
    # Server failed to finish building, time to deliver the bad news...
    print >> sys.stderr, "ERROR: Server " + clone_servername + " failed to build\n"

    
        
        