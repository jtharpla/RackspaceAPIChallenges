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

import java.text.SimpleDateFormat;
import java.util.Date;
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
import org.jclouds.compute.domain.ImageTemplate;
import org.jclouds.compute.domain.NodeMetadata;
import org.jclouds.compute.domain.Template;
import org.jclouds.compute.extensions.ImageExtension;
import org.jclouds.compute.predicates.NodePredicates;
import org.jclouds.domain.Location;
import org.jclouds.util.Preconditions2;

import com.google.common.base.Predicate;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.FutureCallback;
import com.google.common.util.concurrent.ListenableFuture;

/**
 * API Challenge 2: Write a script that clones a server (takes an image and 
 *                deploys the image as a new server). Worth 2 Point
 *
 * Assumptions:
 *               A server named web1 exists, .rackspace_cloud_credentials is a 
 *               file in ini format with a single section. Format is as follows:
 *
 *                    [rackspace_cloud]
 *                    username=<cloud account username>
 *                    api_key=<cloud account api key>
 *
 * @author Jeff Tharp, Managed Cloud
 */

public class challenge2 {
	 private ComputeService compute;
	 
	 // Constants
	 private static final String POLL_PERIOD_THIRTY_SECONDS = String.valueOf(SECONDS.toMillis(30));
	 
	 public static void main(String[] args) {
		 challenge2 challenge2 = new challenge2();
		 
		 try {
			 challenge2.init();
			 Image myimage = challenge2.imageServer();
			 System.out.println("Image ID: " + myimage.getProviderId() + " and status " + myimage.getStatus());

			 if (myimage != null && myimage.getStatus().equals("AVAILABLE")) {
				 challenge2.cloneServer(myimage); 
			 } else {
				 System.err.println("ERROR: " + myimage.getName() + " has status " + myimage.getStatus());
				 System.exit(1);
			 }
		 }
		 catch (Exception e) {
			 e.printStackTrace();
		 }
	  
		 System.exit(0);
	 }
	 
	 /**
	  * Creates an image of the first server in the group with the designated 
	  * prefix.
	  * 
	  * @return The new Image
	  */
	 private Image imageServer() {
		 // Need to determine node id of first server in group with designated
		 // prefix (aka web1, but because jclouds doesn't work that way, this
		 // is a bit more involved)
		 Set<? extends NodeMetadata> nodes = compute.listNodesDetailsMatching(nameStartsWith("web"));
		 NodeMetadata sourcenode = nodes.iterator().next(); // We just want the first node in the group
		 
		 String imagename = "challenge2-" + sourcenode.getName() + "-image-" + getCurrentTimestamp();
		 
		 ImageExtension glance = compute.getImageExtension().get();
		 ImageTemplate imagetemplate = glance.buildImageTemplateFromNode(imagename, sourcenode.getId());
		 try{
			 System.out.println("Creating image of " + sourcenode.getName() + " named " + imagename + ", please wait...");
			 return glance.createImage(imagetemplate).get();
		 }
		 catch (Exception e) {
			 System.err.println("ERROR: Unable to create image named " + imagename + " from server " + sourcenode.getName());
			 System.err.println(e);
			 System.exit(1);
		 }
		 
		 // We'll never reach here, as we exit if the image fails
		 return null;
	 }
	 
	 /**
	  * Creates a server using a source image, then prints details
	  * on how to access the new system (IP address and admin password)
	  * 
	  * @throws RunNodesException
	  * @throws TimeoutException
	  */
	 private void cloneServer(Image sourceimage) throws RunNodesException, TimeoutException{
		 Template template = compute.templateBuilder()
				 .locationId(getLocationId())
				 .fromHardware(getHardware()) // 512 MB Flavor
		         .imageId(sourceimage.getProviderId()) // Use the source image
		         .build();

		 System.out.println("Cloning server, please wait...");

		 // This method will continue to poll for the server status and won't return until this server is ACTIVE
		 // If you want to know what's happening during the polling, enable logging. See
		 // /jclouds-exmaple/rackspace/src/main/java/org/jclouds/examples/rackspace/Logging.java
		 Set<? extends NodeMetadata> nodes = compute.createNodesInGroup("web", 1, template);

		 NodeMetadata nodeMetadata = nodes.iterator().next();

		 String publicAddress = nodeMetadata.getPublicAddresses().iterator().next();  
		 	// Only the IPv4 address seems to be returned by getPublicAddress() anyhow
		 
		 System.out.println(nodeMetadata.getName() + ":");
		 System.out.println("\tIP addresses: " + publicAddress);
		 System.out.println("\tAdmin password: " + nodeMetadata.getCredentials().getPassword());
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
	 
	 public static Predicate<ComputeMetadata> nameStartsWith(final String prefix) {
		 Preconditions2.checkNotEmpty(prefix, "prefix must be defined");

		 return new Predicate<ComputeMetadata>() {
			 @Override
			 public boolean apply(ComputeMetadata computeMetadata) {
				 return computeMetadata.getName().startsWith(prefix);
		     }

		     @Override
		     public String toString() {
		    	 return "nameStartsWith(" + prefix + ")";
		     }
		 };
	 }
	 
	 /**
	  * Utility method to return the current date/time in a format suitible
	  * for use in timestamps
	  * @return Current date/time in yyyyMMddHHmmss format
	  */
	 private String getCurrentTimestamp() {
		 SimpleDateFormat timestampFormat = new SimpleDateFormat("yyyyMMddHHmmss");
		 return timestampFormat.format(new Date());
	 }
}
