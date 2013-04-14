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

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;

import org.jclouds.ContextBuilder;
import org.jclouds.blobstore.BlobStore;
import org.jclouds.blobstore.BlobStoreContext;
import org.jclouds.openstack.swift.CommonSwiftAsyncClient;
import org.jclouds.openstack.swift.CommonSwiftClient;
import org.jclouds.openstack.swift.options.CreateContainerOptions;
import org.jclouds.rest.RestContext;

/**
 * API Challenge Write a script that accepts a directory as an argument as well
 * as a container name. The script should upload the contents of the specified
 * directory to the container (or create it if it doesn't exist). The script
 * should handle errors appropriately. (Check for invalid paths, etc.) Worth 2
 * Points
 * 
 * Assumptions: .rackspace_cloud_credentials is a file in ini format with a
 * single section. Format is as follows:
 * 
 * [rackspace_cloud] username=<cloud account username> api_key=<cloud account
 * api key>
 * 
 * @author Jeff Tharp, Managed Cloud
 */

public class challenge3 {
	 private BlobStore storage;
	 private RestContext<CommonSwiftClient, CommonSwiftAsyncClient> swift;
	 
	 public static void main(String[] args) {
		 ArgumentParser parser = ArgumentParsers.newArgumentParser("challenge3")
				 .defaultHelp(true)
				 .description("Upload contents of a folder to a Cloud Files container");
		 parser.addArgument("sourcefolderpath")
		 		 .help("Path to the local source folder");
		 parser.addArgument("destcontainername")
		 		 .help("Name of Cloud Files container (will create if does not exist)");
		 Namespace ns = null;
		 try {
			 ns = parser.parseArgs(args);			 
		 }
		 catch (ArgumentParserException e) {
			 parser.handleError(e);
			 System.exit(1);
		 }
		 
		 challenge3 challenge3 = new challenge3();
		 
		 try {
			 challenge3.init();
			 challenge3.uploadFolder(ns.getString("sourcefolderpath"), ns.getString("destcontainername"));
		 }
		 catch (Exception e) {
			 e.printStackTrace();
		 }
	  
		 System.exit(0);
	 }
	 
	 /**
	  * Uploads the contents of a local folder to a CloudFiles container
	  * If the specified container does not exist, it is created
	  */
	 private void uploadFolder(String sourceFolderPath, String destContainerName) {
		 System.out.println("Uploading " + sourceFolderPath + " to the Cloud Files container named \"" + destContainerName + "\"");
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
			 
		      // The provider configures jclouds to use the Rackspace Cloud Files (US)
		      // to use the Rackspace Cloud Files (UK) set the provider to "cloudfiles-uk"
			 String provider = "cloudfiles-us";
			 String identity = p.getProperty("username");
			 String apiKey = p.getProperty("api_key");
			 
		     BlobStoreContext context = ContextBuilder.newBuilder(provider)
					 .credentials(identity, apiKey)
					 .buildView(BlobStoreContext.class);
			 storage = context.getBlobStore();
			 swift = context.unwrap();
		 }
		 catch (Exception e) {
			 // Problem reading the file, abort!
			 System.err.println("ERROR: Unable to read credentials file\n");
			 System.err.println(e);
			 System.exit(1);
		 }
	 }
}