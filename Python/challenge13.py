#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 13: Write an application that nukes everything in a 
#                   Cloud Account. It should:
#                   - Delete all Cloud Servers
#                   - Delete all Custom Images
#                   - Delete all Cloud Files Containers and Objects
#                   - Delete all Databases
#                   - Delete all Networks
#                   - Delete all CBS Volumes
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

# Only need to do this once, not both regions
# True on the first region, false on the second
dnsnuke=True

for region in {'DFW', 'ORD'}:
    # We have to do both regions
    print "Nuking account in {}...\n".format(region)
    
    # Get the credentials
    pyrax.set_credential_file(os.path.expanduser("~/.rackspace_cloud_credentials"), region=region)
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers
    dns = pyrax.cloud_dns
    cbs = pyrax.cloud_blockstorage
    cnw = pyrax.cloud_networks
    cf = pyrax.cloudfiles
    cdb = pyrax.cloud_databases
    

    
    # 1. Nuke Cloud Files objects then containers
    print "\t1. Deleting Cloud Files objects and containers..."
    all_containers = cf.get_all_containers()
    for container in all_containers:
        # Loop over the list of containers
        print "\t\t\tClearing " + container.name
        all_storageObjects = container.get_objects(full_listing=True)
        for storageObject in all_storageObjects:
            storageObject.delete()
        print "\t\t\tDeleting " + container.name
        container.delete()
    print "\t\tCloud Files nuked\n"
    
    # 2. Nuke Cloud Database databases then instances
    print "\t2. Delete Cloud Databases dbs and instances..."
    all_dbinstances = cdb.list()
    for dbinst in all_dbinstances:
        # Loop over the list of CDB instances
        print "\t\t\tClearing " + dbinst.name
        all_databases = dbinst.list_databases()
        for db in all_databases:
            db.delete()
        all_users = dbinst.list_users()
        for user in all_users:
            user.delete()
        print "\t\t\tDeleting " + dbinst.name
        dbinst.delete()
    print "\t\tCloud Databases nuked\n"
    
    # 3. Nuke Cloud Load Balancers
    print "\t3. Delete Cloud Load Balancers..."
    all_lbs = clb.list()
    for lb in all_lbs:
        # Loop over the list of Cloud LBs
        print "\t\t\tDeleting " + lb.name
        lb.delete()
    print "\t\tCloud Load Balancers nuked\n"
    
    # 4. Nuke Cloud DNS domains
    if dnsnuke:
        # First time, nuke and set flag to false
        print "\t4. Delete Cloud DNS domains..."
        for domain in dns.get_domain_iterator():
            # Loop over the list of Cloud DNS domains
            # ...uses special paging iterator
            print "\t\tDeleting " + domain.name
            domain.delete()
        print "\t\tCloud DNS nuked\n"
        dnsnuke = False # So we don't repeat this
    
    # 5. Nuke CBS volumes
    print "\t5. Delete Cloud Block Storage volumes..."
    all_vols = cbs.list()
    for vol in all_vols:
        # Loop over the volumes, detach and delete
        print "\t\tDeleting " + vol.name
        vol.delete(force=True) # triggers detach if needed
    print "\t\tCloud Block Storage volumes nuked\n"
    
    # 6. Nuke custom images
    print "\t6. Delete Cloud Server custom images..."
    all_snapshots = cs.list_snapshots()
    for snapshot in all_snapshots:
        # Loop over custom images
        print "\t\tDeleting " + snapshot.name
        snapshot.delete()
    print "\t\tCloud Server custom images nuked\n"
    
    # 7. Nuke Cloud Servers
    print "\t7. Delete Cloud Servers..."
    all_servers = cs.list()
    for server in all_servers:
        # Loop over servers
        print "\t\tDeleting " + server.name
        server.delete()
    print "\t\tCloud Servers nuked\n"
    
    # 8. Nuke Cloud Networks
    print "\t8. Delete Cloud Networks..."
    all_networks = cnw.list()
    for network in all_networks:
        # Loop over networks, ignore public and private
        if network.name != "public" and network.name != "private":
            print "\t\tDeleting " + network.name
            network.delete()
    print "\t\tCloud Networks nuked\n"
    
    print "Account has been successfully nuked in " + region
    

