#!/usr/bin/python
#
# Jeff Tharp, Managed Cloud
#
# API Challenge 12: Write an application that will create a route in MailGun 
#                   so that when an email is sent to 
#                   <YourSSO>@apichallenges.mailgun.org it calls your
#                   Challenge 1 script that builds 3 servers.
#
# Assumptions:
#               Passed SSO username as an argument
#
#               .mailgunapi is a file containing the MailGun api key.
#               Challenge 1 can be kicked off by accessing
#               http://cldsrvr.com/challenge1 
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
import os, sys, urllib, urllib2, base64, argparse

mailgun_apiuri = "https://api.mailgun.net/v2"
challenge1_uri = "http://cldsrvr.com/challenge1"
email_domain = "apichallenges.mailgun.org"

parser = argparse.ArgumentParser(description="Setup MailGun account to call Challenge 1 script")
parser.add_argument("ssouser", help="SSO Username")
args = parser.parse_args()

# Get the API Key
apikey_filepath = os.path.expanduser("~/.mailgunapi")
with open(apikey_filepath, 'r') as apikey_file:
    apikey = apikey_file.readline().rstrip('\n')

# Build match recipient string
match_recipient = "match_recipient('" + args.ssouser + "@" + email_domain + "')"
forward_action = "forward(\"" + challenge1_uri + "\")"

# Build auth header
auth_header_data = "Basic " + base64.encodestring("api:" + apikey).rstrip('\n')

# Build request
data = urllib.urlencode([
                         ("expression", match_recipient),
                         ("action", forward_action),
                         ("action", "stop()")
                        ])

req = urllib2.Request(mailgun_apiuri + "/routes", data)
req.add_header("Authorization", auth_header_data)

# Call the Mailgun Routes API
try:    
    print "Adding Mailgun route for {0}@{1} to forward to {2}...".format(args.ssouser, email_domain, challenge1_uri)
    response = urllib2.urlopen(req)
except urllib2.HTTPError, e:
    print >> sys.stderr, "ERROR: Unable to make HTTP call\n{}\n".format(e)
    sys.exit(1)

print "Response from Mailgun API...\n"
print response.read()

