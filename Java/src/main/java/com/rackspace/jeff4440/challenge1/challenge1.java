package com.rackspace.jeff4440.challenge1;

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

public class challenge1 {
	 private ComputeService compute;
	 
	 // Constants
	 private static final String POLL_PERIOD_THIRTY_SECONDS = String.valueOf(SECONDS.toMillis(30));
	 private static final String[] myservernames = {"web1", "web2", "web3"};
	 
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
	 
	 private void createServers() throws RunNodesException, TimeoutException {
		 Template template = compute.templateBuilder()
				 .locationId(getLocationId())
				 .fromHardware(getHardware())
		         .fromImage(getImage())
		         .build();

		 System.out.println("Create Server");

		 // This method will continue to poll for the server status and won't return until this server is ACTIVE
		 // If you want to know what's happening during the polling, enable logging. See
		 // /jclouds-exmaple/rackspace/src/main/java/org/jclouds/examples/rackspace/Logging.java
		 Set<? extends NodeMetadata> nodes = compute.createNodesInGroup("web1", 1, template);

		 NodeMetadata nodeMetadata = nodes.iterator().next();
		 String publicAddress = nodeMetadata.getPublicAddresses().iterator().next();

		 System.out.println(" " + nodeMetadata);
		 System.out.println(" Login: ssh " + nodeMetadata.getCredentials().getUser() + "@" + publicAddress);
		 System.out.println(" Password: " + nodeMetadata.getCredentials().getPassword());
	 }


	  
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
	 * @return The Hardware with 512 MB of RAM
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
