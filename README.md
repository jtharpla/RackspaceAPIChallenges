RackspaceAPIChallenges
======================

A set of 13 API challenges against the OpenCloud APIs

I choose to implement all 13 challenges in Python and a select few in
Java.  For Python, see the Python folder in this repo, each solution 
is named challengeXX.py where XX = 1 - 13.

Note on challenge 11 -- I built and tested these solutions on 
my local Windows desktop, so I went with a canned self-signed
cert rather than generate a new cert using pyOpenSSL, which is
somewhat difficult to install on Windows

For Java, please see the Java folder.  This is the root of an
Eclipse-based Java project with the jClouds dependencies pulled
in via Maven (see pom.xml for details.)

Java solutions are located in 
/Java/src/main/java/com/rackspace/jeff4440/challenges
(sorry, this is Java convention)

Solutions are named challengeXX.java, each can be ran as an
independent class.

jClouds does not include support for Cloud Databases or
Cloud DNS, so challenges involving these APIs were not attempted

Note on challenge2 -- this currently fails to build a clone 
server after the image is taken.  I reported this to the
SDK Support team, who reported it does appear to be a caching
bug betwen the upper levels of the jClouds SDK implementation
and the lower level Rackspace provider
(see https://github.com/jclouds/jclouds/issues/1560)
(example for this bug is based on my Challenge 2 :-) )
