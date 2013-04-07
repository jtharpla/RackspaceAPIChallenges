/**
 * Copyright 2013 Jeff Tharp
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use
 * this file except in compliance with the License. You may obtain a copy of the
 * License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License
 */

package com.rackspace.jeff4440.challenges;

import java.util.Set;
import java.util.Properties;
import java.io.*;
import java.lang.Thread.UncaughtExceptionHandler;
import java.util.concurrent.TimeoutException;
import static java.util.concurrent.TimeUnit.SECONDS;
 
import org.jclouds.ContextBuilder;
import org.jclouds.compute.ComputeService;
import org.jclouds.compute.ComputeServiceContext;
import org.jclouds.compute.RunNodesException;
import org.jclouds.compute.config.ComputeServiceProperties;
import org.jclouds.compute.domain.ComputeMetadata;
import org.jclouds.compute.domain.Hardware;
import org.jclouds.compute.domain.Image;
import org.jclouds.compute.domain.NodeMetadata;
import org.jclouds.compute.domain.Template;
import org.jclouds.domain.Location;

/**
 * API Challenge 1: Write a script that builds three 512 MB Cloud Servers that
 * following a similar naming convention. (ie., web1, web2, web3)
 * and returns the IP and login credentials for each server. Use
 * any image you want.
 *
 * Assumptions:
 * .rackspace_cloud_credentials is a file in ini format with a
 * single section. Format is as follows:
 *
 * [rackspace_cloud]
 * username=<cloud account username>
 * api_key=<cloud account api key>
 *
 * @author Jeff Tharp, Managed Cloud
 */

public class challenge1 {
	 private ComputeService compute;
	 
	 // Constants
	 private static final String POLL_PERIOD_THIRTY_SECONDS = String.valueOf(SECONDS.toMillis(30));
	 
	 public static void main(String[] args) {
		 challenge1 challenge1 = new challenge1();
		 
		 try {
			 challenge1.init();
			 challenge1.createServers();
		 }
		 catch (Exception e) {
			 e.printStackTrace();
		 }
	  
		 System.exit(0);
	 }
	 
	 /**
	  * Creates 3 servers using a common naming scheme, then prints the details
	  * on how to access these (IP address and admin password)
	  * 
	  * @throws RunNodesException
	  * @throws TimeoutException
	  */
	 private void createServers() throws RunNodesException, TimeoutException {
		 Template template = compute.templateBuilder()
				 .locationId(getLocationId())
				 .fromHardware(getHardware()) // 512 MB Flavor
		         .fromImage(getImage()) // Ubuntu 12.04 Image
		         .build();

		 System.out.println("Creating servers, please wait...");

		 // This method will continue to poll for the server status and won't return until this server is ACTIVE
		 // If you want to know what's happening during the polling, enable logging. See
		 // /jclouds-exmaple/rackspace/src/main/java/org/jclouds/examples/rackspace/Logging.java
		 Set<? extends NodeMetadata> nodes = compute.createNodesInGroup("web", 3, template);

		 for (NodeMetadata nodeMetadata : nodes) {
			 // Loop for each node created and print the details
			 
			 String publicAddress = nodeMetadata.getPublicAddresses().iterator().next();  
			 	// Only the IPv4 address seems to be returned by getPublicAddress() anyhow
			 
			 System.out.println(nodeMetadata.getName() + ":");
			 System.out.println("\tIP addresses: " + publicAddress);
			 System.out.println("\tAdmin password: " + nodeMetadata.getCredentials().getPassword());
		 }
	 }

	 /**
	  * Reads Rackspace API credentials from .rackspace_cloud_credentials ini file
	  * in users home directory, and then creates a new ComputeService object using
	  * these credentials.
	  */
	 private void init() {
		 Thread.setDefaultUncaughtExceptionHandler(new UncaughtExceptionHandler() {
			 public void uncaughtException(Thread t, Throwable e) {
				 e.printStackTrace();
				 System.exit(1);
			 }
		 });

		 // Read in Rackspace API credentials from file in users home directory
		 try{
			 Properties p = new Properties();
			 p.load(new FileInputStream(System.getProperty("user.home") + File.separator + ".rackspace_cloud_credentials"));
			 
		      // The provider configures jclouds to use the Rackspace open cloud (US)
		      // to use the Rackspace open cloud (UK) set the provider to "rackspace-cloudservers-uk"
			 String provider = "rackspace-cloudservers-us";
			 String identity = p.getProperty("username");
			 String apiKey = p.getProperty("api_key");
			 
			 
		     // These properties control how often jclouds polls for a status update
		     Properties overrides = new Properties();
		     overrides.setProperty(ComputeServiceProperties.POLL_INITIAL_PERIOD, POLL_PERIOD_THIRTY_SECONDS);
		     overrides.setProperty(ComputeServiceProperties.POLL_MAX_PERIOD, POLL_PERIOD_THIRTY_SECONDS);
			 
		     ComputeServiceContext context = ContextBuilder.newBuilder(provider)
					 .credentials(identity, apiKey)
					 .buildView(ComputeServiceContext.class);
			 compute = context.getComputeService();
		 }
		 catch (Exception e) {
			 // Problem reading the file, abort!
			 System.err.println("ERROR: Unable to read credentials file\n");
			 System.err.println(e);
			 System.exit(1);
		 }
	 }
	 
	 /**
	  * This method uses the generic ComputeService.listAssignableLocations() to find the location.
	  *
	  * @return The first available Location
	  */
	 private String getLocationId() {
		 Set<? extends Location> locations = compute.listAssignableLocations();
		 return locations.iterator().next().getId();
	 }

	 /**
	 * This method uses the generic ComputeService.listHardwareProfiles() to find the hardware profile.
	 *
	 * @return The Hardware flavor with 512 MB of RAM
	 */
	 private Hardware getHardware() {
		 Set<? extends Hardware> profiles = compute.listHardwareProfiles();
	     Hardware result = null;

	     for (Hardware profile: profiles) {
	    	 if (profile.getRam() == 512) {
	    		 result = profile;
	    	 }
	     }

	     if (result == null) {
	    	 System.err.println("ERROR: Flavor with 512 MB of RAM not found. Using first flavor found\n");
	         result = profiles.iterator().next();
	     }

	     return result;
	 }

	 /**
	  * This method uses the generic ComputeService.listImages() to find the image.
	  *
	  * @return An Ubuntu 12.04 Image
	  */
	 private Image getImage() {
		 Set<? extends Image> images = compute.listImages();
	     Image result = null;

	     for (Image image: images) {
	    	 if (image.getOperatingSystem().getName().equals("Ubuntu 12.04 LTS (Precise Pangolin)")) {
	    		 result = image;
	         }
	     }

	     if (result == null) {
	    	 System.err.println("ERROR: Image with Ubuntu 12.04 operating system not found. Using first image found.\n");
	    	 result = images.iterator().next();
	     }

	     return result;
	 }
}
