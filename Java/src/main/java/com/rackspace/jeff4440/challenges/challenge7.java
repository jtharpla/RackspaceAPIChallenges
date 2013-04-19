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
import org.jclouds.loadbalancer.LoadBalancerService;
import org.jclouds.loadbalancer.LoadBalancerServiceContext;
import org.jclouds.loadbalancer.domain.LoadBalancerMetadata;
import org.jclouds.rackspace.cloudloadbalancers.CloudLoadBalancersApi;
import org.jclouds.rackspace.cloudloadbalancers.CloudLoadBalancersAsyncApi;
import org.jclouds.rackspace.cloudloadbalancers.features.LoadBalancerApi;
import org.jclouds.rackspace.cloudloadbalancers.domain.LoadBalancer;
import org.jclouds.util.Preconditions2;
import org.jclouds.domain.Location;
import org.jclouds.rest.RestContext;

import com.google.common.base.Predicate;

/**
 * API Challenge 7: Write a script that will create 2 Cloud Servers and add 
 * them as nodes to a new Cloud Load Balancer.
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

public class challenge7 {
	 private ComputeService compute;
	 private LoadBalancerService clb;
	 private RestContext<CloudLoadBalancersApi, CloudLoadBalancersAsyncApi> clbapi;

	 // Constants
	 private static final String POLL_PERIOD_THIRTY_SECONDS = String.valueOf(SECONDS.toMillis(30));
	 
	 public static void main(String[] args) {
		 challenge7 challenge7 = new challenge7();
		 
		 try {
			 challenge7.init();
			 challenge7.createServers();
			 challenge7.createLoadBalancer();
		 }
		 catch (Exception e) {
			 e.printStackTrace();
		 }
	  
		 System.exit(0);
	 }
	 
	 /**
	  * Creates 2 servers using a common naming scheme, then prints the details
	  * on how to access these (IP address and admin password)
	  * 
	  * @throws RunNodesException
	  * @throws TimeoutException
	  */
	 private void createServers() throws RunNodesException, TimeoutException {
		 Template template = compute.templateBuilder()
				 .locationId(getLocation().getId())
				 .fromHardware(getHardware()) // 512 MB Flavor
		         .fromImage(getImage()) // Ubuntu 12.04 Image
		         .build();

		 System.out.println("Creating servers, please wait...");

		 // This method will continue to poll for the server status and won't return until this server is ACTIVE
		 // If you want to know what's happening during the polling, enable logging. See
		 // /jclouds-exmaple/rackspace/src/main/java/org/jclouds/examples/rackspace/Logging.java
		 Set<? extends NodeMetadata> nodes = compute.createNodesInGroup("c7web", 2, template);

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
	  * Creates a load balancer and adds the servers in the 'c7web' node group
	  * as nodes.  Prints the details of the load balancer
	  * 
	  * @throws TimeoutException
	  */
	 private void createLoadBalancer() throws TimeoutException {
		// Grab a set of the nodes we just created
		Set<? extends NodeMetadata> nodes = compute.listNodesDetailsMatching(nameStartsWith("c7web"));
		
		// Create the load balancer
		System.out.println("\nCreating load balancer...");
		LoadBalancerMetadata newlb = clb.createLoadBalancerInLocation(
				getLocation(), 	// First available location
				"c7-lb-http",  	// Name of new load balancer
				"HTTP", 		// Protocol
				80, 			// Port of load balancer
				80, 			// Port of backend nodes
				nodes);			// Set of nodes to add
		
		// Determine the newly assigned virtual IP
		String vip = newlb.getAddresses().iterator().next();
		
		// Have to dig into the backend API for the algorithm
		LoadBalancerApi clbzoneapi = clbapi.getApi().getLoadBalancerApiForZone(getLocation().getId());
		LoadBalancer api_lb = clbzoneapi.get(Integer.parseInt(newlb.getProviderId()));
		String algorithm = api_lb.getAlgorithm();
		
		
		// Now print out the details of the new LB
		System.out.println(newlb.getName() + ":");
		System.out.println("\tVirtual IP Address: " + vip);
		System.out.println("\tAlgorithm: " + algorithm);
		System.out.println("\tNodes: " + getNodeList(nodes));
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
			 // Note that later versions of jClouds use "rackspace-cloudloadbalancers-us" and
			 // "rackspace-cloudloadbalancers-uk" for Cloud Load Balancers providers in US/UK
			 String novaprovider = "rackspace-cloudservers-us";
			 String lbprovider = "cloudloadbalancers";
			 String identity = p.getProperty("username");
			 String apiKey = p.getProperty("api_key");
			 
			 
		     // These properties control how often jclouds polls for a status update
		     Properties overrides = new Properties();
		     overrides.setProperty(ComputeServiceProperties.POLL_INITIAL_PERIOD, POLL_PERIOD_THIRTY_SECONDS);
		     overrides.setProperty(ComputeServiceProperties.POLL_MAX_PERIOD, POLL_PERIOD_THIRTY_SECONDS);
			 
		     // Get service for compute/Nova (Cloud Servers)
		     ComputeServiceContext novacontext = ContextBuilder.newBuilder(novaprovider)
					 .credentials(identity, apiKey)
					 .buildView(ComputeServiceContext.class);
			 compute = novacontext.getComputeService();
			 
			 // Get service for load balancers/LBaaS (Cloud Load Balancers)
			 LoadBalancerServiceContext lbcontext = ContextBuilder.newBuilder(lbprovider)
					 .credentials(identity, apiKey)
					 .buildView(LoadBalancerServiceContext.class);
			 clb = lbcontext.getLoadBalancerService();
			 clbapi = lbcontext.unwrap();
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
	 private Location getLocation() {
		 Set<? extends Location> locations = compute.listAssignableLocations();
		 return locations.iterator().next();
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
	 
	 /**
	  * Creates a predicate for locating nodes whose names start with "prefix"
	  * 
	  * @param prefix
	  * @return a predicate matching nodes whose names start with prefix
	  */
	 private static Predicate<ComputeMetadata> nameStartsWith(final String prefix) {
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
	  * This method returns a comma separated list of the names in the set of nodes
	  * passed to it
	  * 
	  * @param set of NodeMetadata objects representing the nodes
	  * @return string containing a comma-separated list of nodes
	  */
	 private String getNodeList(Set<? extends NodeMetadata> nodes) {
		 StringBuilder result = new StringBuilder();
		 // Walk through the nodes, adding their names to the list
		 for(NodeMetadata node : nodes) {
			 result.append(node.getName());
			 result.append(",");
		 }
		 
		 // Chop off the last "," from the resulting string
		 return result.length() > 0 ? result.substring(0, result.length() - 1): "";
	 }
}