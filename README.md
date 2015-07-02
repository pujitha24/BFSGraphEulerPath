GTA-X: Plugin Developer Guide
=============================

Contents
--------

 - [Overview and Key Concepts](#overview-and-key-concepts)
 - [How to Create a Plugin](#how-to-create-a-plugin)
 - [How to Work with Global/Remote Assets](#how-to-work-with-globalremote-assets)
 - [How to Call Another Plugin](#how-to-call-another-plugin)
 - [How to Specify Timeout for Runner Calls in a Plugin](#how-to-specify-timeout-for-runner-calls-in-a-plugin)
 - [How to Perform Operations after Task is Complete](#how-to-perform-operations-after-task-is-complete)
 - [Runner Helper Functions](#runner-helper-functions)


###Overview and Key Concepts

GTA-X is designed to be extensible through plugins. A plugin is a Python file that defines a single run function to parse a line from the request file. All plugins are located in the plugins folder on the server's install folder (`C:\gtax\plugins` or `/usr/share/gtax/plugins`).

Here's how GTA-X interacts with the command plug-ins:

  1.  For every line in the job file, GTA-X looks at the first word to determine the plugin to run. It looks for the file PLUGIN.py, eg. test_runbat. If found, GTA-X loads the Python file.  If the plugin .py file is not found, an appropriate error message is logged for the line and the result is 'fail'.

  2.  The plugin run() method is called with a runner object and the line text for the plugin. The plugin can push and pull files, execute commands, parse logs files, etc. The runner object passed into the run() method provides some API calls to make it GTA-X files (results.txt, log directories, etc) and the test sytem.

  3.  When the command plug-in exits, GTA-X continues executing the next line in the job file until all job tasks are completed.


GTA-X has support for some special plugins (called hooks), which are designed to make some additional operations during events send by runner e.g. onjobstart, ontaskend etc. It could be used for e.g. custom results reporting.

Here's how hooks work:

* All hook files need to be placed in plugin/hooks directory of gtax tool.
* In job.txt file runner is checking hooks attribute (e.g. -hooks: vpg_results,controller_notifications), and adding to events list available events in hook files (basing on methods name "on(job|tasklist|task)(start|end)").
* In job.txt could be provided more then one hook - it's comma separated list of hook file names (e.g. -hooks: vpg_results,controller_notifications)
* When runner is calling event (e.g. onjobstart), all connected events are called (e.g. all onjobstart methods from all hooks)

There is possibility to automatically add some hooks to all jobs submitted by Controller UI/API. Controller has JOB_DEFAULT_HOOKS setting, which by default is set to controller_notifications, but it could be extended to longer list of default hooks e.g. controller_notifications,vpg_results. Use Controller's /settings POST endpoint to edit this.


###How to Create a Plugin
In the following section, we'll walk through the process of creating a
plugin. If you follow this example and check out the available functions
in tools/gta/runner/runner.py (see class TaskRunner), you'll be on your way
to writing custom plugins.

#####Step 1: Define your command line 

First things first. You want to decide on the command syntax. 
How do you want your command to look in the job file? 
Create a sample job file using the following  link.

https://github.intel.com/GSAE/gtax/blob/master/Quick-Start.md#create-simple-job-files.

For our example
we'll be creating a generic test command launcher. We'll assume our
test will exist in the tests share under a directory(i.e plugin / test). It will contain
a BAT file named run.bat that will return zero if the test passed and
non-zero if the test fails. Note : We use bat files to run on windows machine. 
Here what we assume the syntax will be:

`test_runbat mytestfolder`

Here mytestfolder is the folder where we place our test_runbat plugin. 

To run the plugin on Linux machine, we should create a shell script file instead of batch. create a  sample shell script(run.sh) as shown below. Do not try to create  or open the following shell script on windows machine as it produces unexpected results.
```python
    #!/bin/sh
     echo "hello world"
```
Place this run.sh, In the same folder where our plugin is present

#####Step 2: Create the Python plugin file 

If you were to run a job file now using this plugin, you would get an error
saying the plugin test_runbat.py does not exist. On our server, we create
the file `plugins/test_runbat.py` and add the following lines:
```python
	"""
	test_runbat test_folder [optional_args...]

	Description:
	    Generic test plugin that copies tests/test_folder to the client and
	    then runs tests/test_folder/run.bat. The exit code determines pass/
	    fail (0 is pass, non-zero is fail).

	   Inside the run.bat script, the unique line ID + any optional
	   parameters are passed into the script.

	Examples:

	    # Runs tests/Performance11/run.bat task_id
	    test_runbat Performance11

	    # Runs tests/3DMark11/run.bat task_id perf_preset.xml
	    test_runbat 3DMark11 perf_preset.xml

	"""
	def run(runner, line):
	    return 'pass'
```
When writing a plugin, it's helpful to provide a comment header describing
what the command does along with some examples of how to call the command from
the request. The plugin defines one Python run() function. The function
accepts two arguments and is expected to return a string indicating the status
of the command. Conventional return values are "pass" and "fail".

**Inputs:**

- runner:
  TaskRunner object that holds helper functions to interact with GTA-X (ex: adding properties to the results.txt).
- line:
  String holding the parsed line from the job file minus the name of the
  plugin

The run method is called every time the plugin is listed in a job file. So for
example let's say you have the following lines in a job file:

    test_runbat mytestfolder
    test_runbat mytestfolder2
    test_runbat mytestfolder2

The test_runbat plug-in would be run three times:

    => test_runbat.run([object], "mytestfolder")
    => test_runbat.run([object], "mytestfolder2")
    => test_runbat.run([object], "mytestfolder2")

#####Step 3: Add Your Plugin Content

Now we get to the meaty part of the plug-in. You get to write the script
that handles shelling out, copying files, creating logs, whatever your
test needs to do. GTA-X exposes a number of helper functions to
aid in doing common things. The best way to learn what to do is to look
at other plugins and see how they are doing things.

Given below, we have three different versions of sample plugin based on the platform you run the plugin. There are few  differences in the plugin content based on each of these versions.

Following are the few  observations to make :

Batch file is used for windows where as shell script is used for linux machine.

The path seperator in windows machine is '\' where as in linux the path seperator is '/'.

Windows accepts '/' as path seperator. So '/' is used as a path seperator  when  cross platform plugin is created.

To check the the platform on which our DUT (TC ) is running 
 Use the following code.
 ```python
       os_type = runner.client_setting("os_type")
       if "windows" in os_type:
          runbat = os.path.join(test_dir, 'run.bat')
          print("DUT OS type is Windows")
          cmd = 'run.bat'
       else:
          runbat = os.path.join(test_dir, 'run.sh')
          print("DUT OS type is Linux/Mac")
          cmd = './run.sh'   
```
Following sample plugin content  runs on windows. 
 


```python
        """
    test_runbat test_folder [optional_args...]
    Description:
    Generic test plugin that copies    tests/test_folder to the client and
    then runs tests/test_folder/run.bat. The exit code determines pass/fail 
    (0 is pass, non-zero is fail).Inside the run.bat script, 
    the unique line ID + any optional parameters are passed into the script.
    Examples:
    # Runs tests/Performance11/run.bat task_id
    test_runbat Performance11
    # Runs tests/3DMark11/run.bat task_id   perf_preset.xml
    test_runbat 3DMark11 perf_preset.xml
    Note:  This sample plugin is intended for use with a Windows DUT
      """
    import os
    def run(runner, line):
    # First get the test directory we will be running. Since we only
    # have one argument on the line, the test_dir is the whole line test_dir = line
    # Now we check the parameters and make sure they are valid. If we
    # detect an error we use the GTA-X helper function runner.add_error().
    # This adds a line to the results.txt file like:
    #     --err_msg: [message]
    # For convenience, we also print a log message to the Runner console
	    
	if test_dir == '':
	   runner.add_error('You must specify a test folder - Ex: test_runbat myfolder')
	   return 'fail'

	    # We create a couple of path variables and verify the test script
	    # exists on runner machine
	runbat = os.path.join(test_dir, 'run.bat')
	if not os.path.exists(runbat):
	   runner.add_error('Cannot find batch file ' + runbat)
	   runner.log_msg('Cannot find batch file: ' + runbat)
	   return 'fail'
	  # Always place executable tests in a folder underneath the folder returned by 
    # rtests_dir().  This is where tests are stored on the DUT.  
    remote_dir = runner.rtests_dir()  + '\\' + test_dir

	  # We synchronize the test folder down onto the test system by using
	  # runner.rpush(). This function pushes files from the controller to
	  # the test system. It only pushes files that are different
	  # so the first time it may take a while but all other calls will be
	  # quick.
	runner.rpush(test_dir, remote_dir)
	   # Define our command string and add some test results to the results.txt
    # file using runner.add_result().
    cmd = 'run.bat'
    runner.add_result('cmd', cmd)
    runner.add_result('wd', remote_dir)

    # Now we actually run the test. We use the runner.rexecute() call to
    # execute a command on the DUT. 
    proc = runner.rexecute(cmd, cwd=remote_dir)

    # Add exit code, stdout and stderr to results.txt and Runner console
    runner.add_result('exit_code: ', proc.exit_code)
    runner.add_result('stdout: ', proc.stdout)
    runner.add_result('stderr: ', proc.stderr)
    runner.log_msg('exit code: ' + str(proc.exit_code))
    runner.log_msg('stdout: ' + proc.stdout)
    if proc.stderr: 
        runner.log_msg('stderr: ' + proc.stderr) 

    # Return pass or fail depending on what the exit code was
    if proc.exit_code == 0:
        return 'pass'
    else:
        runner.log_msg('Return code is not zero - failing task')
        return 'fail' 
	     
```

Following  sample plugin content  runs on  Linux  machine. 
```python

	"""
        test_runbat test_folder [optional_args...]

         Description:
    Generic test plugin that copies tests/test_folder to the client and
    then runs tests/test_folder/run.sh. The exit code determines pass/
    fail (0 is pass, non-zero is fail).

     Inside the run.sh script, the unique line ID + any optional
    parameters are passed into the script.

     Examples:

    # Runs tests/Performance11/run.sh task_id
    test_runbat Performance11

    # Runs tests/3DMark11/run.sh task_id perf_preset.xml
    test_runbat 3DMark11 perf_preset.xml

     Note:  This sample plugin is intended for use with a linux DUT
       """
    import os

    def run(runner, line):
    # First get the test directory we will be running. Since we only
    # have one argument on the line, the test_dir is the whole line
    test_dir = line

    # Now we check the parameters and make sure they are valid. If we
    # detect an error we use the GTA-X helper function runner.add_error().
    # This adds a line to the results.txt file like:
    #     --err_msg: [message]
    # For convenience, we also print a log message to the Runner console
    if test_dir == '':
        runner.add_error('You must specify a test folder - Ex: test_runbat myfolder')
        runner.log_msg('You must specify a test folder - Ex: test_runbat myfolder')
        return 'fail'

    # We verify the test script exists on the Runner machine
    # Create sample shell script run.sh on linux machine and copy it to plugin
    # folder 
    runbat = os.path.join(test_dir, 'run.sh')
    if not os.path.exists(runbat):
        runner.add_error('Cannot find batch file: ' + runbat)
        runner.log_msg('Cannot find batch file: ' + runbat)
        return 'fail'

    # Always place executable tests in a folder underneath the folder returned by 
    # rtests_dir().  This is where tests are stored on the DUT.  
    print(runner.rtests_dir())
    #Linux machine recognizes forward slash. the working directory format for linux
    #is /home/bin/bash
    remote_dir = runner.rtests_dir()  + '/' + test_dir
    print(remote_dir)
    # We synchronize the test folder down onto the test system by using
    # runner.rpush(). This function pushes files from the controller to
    # the test system. It only pushes files that are different
    # so the first time it may take a while but all other calls will be
    # quick.
    runner.rpush(test_dir, remote_dir )

    # Define our command string and add some test results to the results.txt
    # file using runner.add_result().
    # To execute a shell script on linux, the command is './file.sh'
    cmd = './run.sh'
    runner.add_result('cmd', cmd)
    runner.add_result('wd', remote_dir)
    print (remote_dir)
    # Now we actually run the test. We use the runner.rexecute() call to
    # execute a command on the DUT. 
    proc = runner.rexecute(cmd, cwd=remote_dir)

    # Add exit code, stdout and stderr to results.txt and Runner console
    runner.add_result('exit_code: ', proc.exit_code)
    runner.add_result('stdout: ', proc.stdout)
    runner.add_result('stderr: ', proc.stderr)
    runner.log_msg('exit code: ' + str(proc.exit_code))
    runner.log_msg('stdout: ' + proc.stdout)
    if proc.stderr: 
        runner.log_msg('stderr: ' + proc.stderr) 

    # Return pass or fail depending on what the exit code was
    if proc.exit_code == 0:
        return 'pass'
    else:
        runner.log_msg('Return code is not zero - failing task')
        return 'fail'
```

Following  is  the sample cross platform plugin content.   
```python

	"""
        test_runbat test_folder [optional_args...]

         Description:
    Generic test plugin that copies tests/test_folder to the client and
    then runs tests/test_folder/run.sh. The exit code determines pass/
    fail (0 is pass, non-zero is fail).

     Inside the run.sh script, the unique line ID + any optional
    parameters are passed into the script.

     Examples:

    # Runs tests/Performance11/run.sh task_id
    test_runbat Performance11

    # Runs tests/3DMark11/run.sh task_id perf_preset.xml
    test_runbat 3DMark11 perf_preset.xml

     Note:  This sample plugin is intended for use with a Windows DUT
       """
    import os

    def run(runner, line):
    # First get the test directory we will be running. Since we only
    # have one argument on the line, the test_dir is the whole line
    test_dir = line

    # Now we check the parameters and make sure they are valid. If we
    # detect an error we use the GTA-X helper function runner.add_error().
    # This adds a line to the results.txt file like:
    #     --err_msg: [message]
    # For convenience, we also print a log message to the Runner console
    if test_dir == '':
        runner.add_error('You must specify a test folder - Ex: test_runbat myfolder')
        runner.log_msg('You must specify a test folder - Ex: test_runbat myfolder')
        return 'fail'
    #This is to check the platform in which our DUT (TC ) is running and
    #use files and commands based on the platform
    os_type = runner.client_setting("os_type")
    if "windows" in os_type:
        runbat = os.path.join(test_dir, 'run.bat')
        print("DUT OS type is Windows")
        cmd = 'run.bat'
    else:
        runbat = os.path.join(test_dir, 'run.sh')
        print("DUT OS type is Linux/Mac")
        cmd = './run.sh'  
    # We verify the test script exists on the Runner machine
    if not os.path.exists(runbat):
        runner.add_error('Cannot find batch file: ' + runbat)
        runner.log_msg('Cannot find batch file: ' + runbat)
        return 'fail'

    # Always place executable tests in a folder underneath the folder returned by 
    # rtests_dir().  This is where tests are stored on the DUT.  
    print(runner.rtests_dir())
    #Linux/window  machine recognizes forward slash. 
    #Though windows machine directory format has backward slash.
    #it recognizes the forward slash
    remote_dir = runner.rtests_dir()  + '/' + test_dir
    print(remote_dir)
    # We synchronize the test folder down onto the test system by using
    # runner.rpush(). This function pushes files from the controller to
    # the test system. It only pushes files that are different
    # so the first time it may take a while but all other calls will be
    # quick.
    runner.rpush(test_dir, remote_dir )
    # Define our command string and add some test results to the results.txt
    # file using runner.add_result().
    runner.add_result('cmd', cmd)
    runner.add_result('wd', remote_dir)
    print (remote_dir)
    # Now we actually run the test. We use the runner.rexecute() call to
    # execute a command on the DUT. 
    proc = runner.rexecute(cmd, cwd=remote_dir)
    # Add exit code, stdout and stderr to results.txt and Runner console
    runner.add_result('exit_code: ', proc.exit_code)
    runner.add_result('stdout: ', proc.stdout)
    runner.add_result('stderr: ', proc.stderr)
    runner.log_msg('exit code: ' + str(proc.exit_code))
    runner.log_msg('stdout: ' + proc.stdout)
    if proc.stderr: 
        runner.log_msg('stderr: ' + proc.stderr) 

    # Return pass or fail depending on what the exit code was
    if proc.exit_code == 0:
        return 'pass'
    else:
        runner.log_msg('Return code is not zero - failing task')
        return 'fail'
```
###How to Work with Global/Remote Assets

In the following section, we'll walk you through how to integrate global/remote assets into your job and plugin.

####Asset Repository Types
GTA-X can retrieve test assets stored in the following types of repositories:

* GTA Global Asset Store (based on Artifactory)
* Quickbuild
* Local directory, file share or HTTP server

Assets used in production testing will be most commonly be hosted on the  **VPG's Global Asset Store** at http://gfx-assets.intel.com (based on Artifactory) and Quickbuild.

####Asset Keys and Properties
For a given job, each test asset must have a unique **key**, and a set of **properties** (key/value pairs) which provide information needed to locate the asset.

Between your job.txt file and plugin, you will define all of the attributes necessary to uniquely identify each of your test assets.  Plugins define asset keys and (optionally) default property values.  Properties can also be specified in a job.  In case of a conflict, job attribute values will override plugin attribute values.

Here is an example dictionary describing a local test asset on a Windows machine.  It specifies an asset with key `gfx_driver`, with a single property (`local_url`) indicating the local path to the asset.
```python
    { "gfx_driver":
	    { "local_url": r'C:\Builds\win64_153614.exe'
	    }
    }
```
Here is an example dictionary for an asset with key "artifactory_asset" in the VPG Global Asset Store (Artifactory).
```python
       "artifactory_asset": {
             "root_url": "gta+http://gfx-assets.intel.com/artifactory",
             "asset_path": "gfx-assets-fm",
             "asset_version": "2.14.3",
             "asset_name": "DUTPrepare"
        },
```        
Note that four attributes can be specified for assets coming from the VPG Global Asset Store.  GTA-X expects different asset properties, depending on the type of source asset repository.   The next section details GTA-X expected asset properties for each type of repository.

#####Required Asset Properties - VPG Global Asset Store
First, we will look at properties for assets stored in the GTA Gobal Asset Store.

For assets in the GTA Global Asset Store (Artifactory), the following properties must be specified:

| Attribute | Description | Examples
| --------- | ----------- | --------
| **root_url** (optional)| Specifies path to and Artifactory server.  This parameter defaults to the global VPG Artifactory instance (http://gfx-assets.intel.com), however the default can be overridden for a specific Artifactory installation. | "gta+http://10.80.188.38:8081/artifactory"
| **asset_path** (required)| Specifies the relative path in the asset repository to the test asset of interest | "gfx-assets-fm"
| **asset_name** (required)| The Artifactory asset name.  Do not confuse this parameter with the asset key, which is used to correlate job parameters with specific assets defined in a plugin.   | "DUTPrepare"
| **asset_version** (required)| Indicates a unique version of the named asset | "2.14.3"
| **target** (optional)| Indicates where the asset will be downloaded. By default it will download the asset to the remote client. If attribute is provided, valid options are: **local** (to download the content locally as if using a local executor), **client_name** (to download the content to a specified client).| "local" or "my_client"
| **auto_download** (optional)| Specifies if the asset will be downloaded before the method `run()` in the plugin or if it will be downloaded manually at a specific point in the plugin. Defaults to True if not provided. See [How to specify manual download of an asset](#specify-manual-download-of-an-asset). | True or False

Note:  for **root_url**, we use a specially formatted URL (prefix is 'gta+http:'), which indicates we are accessing an asset stored on an Artifactory server.

#####Required Asset Properties - Quickbuild
For assets in Quickbuild, the following properties must be specified:

| Attribute | Description | Examples
| --------- | ----------- | --------
| **root_url** (required)| Specifies path to a Quickbuild server. | "qb+http://ubit-gsae.intel.com/"
| **configuration** (required) | Quickbuild configuration string | "ubit/ci/gtax"
| **build_version** (required)| Specifies the Quickbuild build version | "1.0.420"
| **artifact_path** (required)| A regular expression for the artifact file to download | "gtax-*.zip"
| **target** (optional)| Indicates where the asset will be downloaded. By default it will download the asset to the remote client. If attribute is provided, valid options are: **local** (to download the content locally as if using a local executor), **client_name** (to download the content to a specified client).| "local" or "my_client"
| **auto_download** (optional)| Specifies if the asset will be downloaded before the method `run()` in the plugin or if it will be downloaded manually at a specific point in the plugin. Defaults to True if not provided. See [How to specify manual download of an asset](#specify-manual-download-of-an-asset). | True or False

Note:  for **root_url**, we use a specially formatted URL (prefix is 'qb+http:'), which indicates we are accessing an asset stored on a Quickbuild server.

#####Required Asset Properties - HTTP server
For assets residing on an HTTP server, the following properties must be specified:

| Attribute | Description | Examples
| --------- | ----------- | --------
| **root_url** (required)| Specifies the root path to file or directory of interest on a HTTP server.  If "sub_path" attribute is not present, root_url represents the full path to the asset of interest. | "webcache+https://ubitstore.intel.com/webstores"
| **sub_path** (optional)| Specifies a relative path to the file or directory of interest on a HTTP server (this value is appended to root_url base to form a full URL) | "fm/gfxshare/gta"
| **target** (optional)| Indicates where the asset will be downloaded. By default it will download the asset to the remote client. If attribute is provided, valid options are: **local** (to download the content locally as if using a local executor), **client_name** (to download the content to a specified client).| "local" or "my_client"
| **auto_download** (optional)| Specifies if the asset will be downloaded before the method `run()` in the plugin or if it will be downloaded manually at a specific point in the plugin. Defaults to True if not provided. See [How to specify manual download of an asset](#specify-manual-download-of-an-asset). | True or False

Note:  for **root_url**, we use a specially formatted URL (prefix is 'qb+webcache:'), which indicates we are accessing an asset stored on an HTTP server.
Before retrieving the  assets stored at HTTP  server, Open the url mentioned and check if you are authorized user or not.
 
#####Required Asset Properties - Local directory or file share
For assets not stored in Artifactory or Quickbuild, a "local_url" attribute is required:

| Attribute | Description | Examples
| --------- | ----------- | --------
| **local_url** (required)| Specifies path the asset directory to be copied | "\\amr\unc-cache\wlk"<br> "C:\temp\my-test-contents\wlk"
| **target** (optional)| Indicates where the asset will be downloaded. By default it will download the asset to the remote client. If attribute is provided, valid options are: **local** (to download the content locally as if using a local executor), **client_name** (to download the content to a specified client).| "local" or "my_client"
| **auto_download** (optional)| Specifies if the asset will be downloaded before the method `run()` in the plugin or if it will be downloaded manually at a specific point in the plugin. Defaults to True if not provided. See [How to specify manual download of an asset](#specify-manual-download-of-an-asset). | True or False

Note: The entire directory is copied recursively to the target.

**TODO**: Can we specify a single file in this way?

####Plugin Syntax
In order for GTA-X runner to download appropriate assets/test contents for your job, each plugin must provide the required properties for information on how to download the assets.  To do this, your plugin code must provide a new method called `get_assets()`.  This method will have the same parameters as the `run()` method, and it must to return a dictionary containing the asset **key**, and asset **properties** in the form of key/value pairs.

Here is an example of the `get_assets()` method, which specifies 3 assets with the following keys: "artifactory_asset", "qb_gtax", and "local_driver". NOTE: This is not how plugins would typically look, it is simply showing the different types of assets that a plugin can define and the attributes that are associated with each type.

Define the following assets in your sample plugin and try 
```python
    def get_assets(target, line):
     return {
        "artifactory_asset": {
             "root_url": "gta+http://gfx-assets.intel.com/artifactory",
             "asset_path": "gfx-assets-fm",
             "asset_version": "2.14.3",
             "asset_name": "DUTPrepare"
        },
              "qb_gtax": {  # Artifactory asset
                 "root_url": "qb+http://ubit-gsae.intel.com/",
                 "configuration": "ubit/ci/gtax"
                 "artifact_path": "gtax-1.0.677.zip",
            },
            "local_driver": {
                 "local_url": r'C:\tmp\driver'
            }
        }
```
Note: if you receive 'Download failed with return code 1'. Make sure that the artifact is actually present at the url mentioned.

First time users should sign in  to Quickbuild UI  before trying to retrieve the asset from quick build.

####Job File Syntax
In a job.txt file, asset attributes must use the following syntax:
`<plugin_name>.asset.<asset_key>.<asset_property>`

Here is an example job, which specifies **asset_name** and **asset_version** properties for an Artifactory asset referred to by the **enabling_tests** key, to be used in the **test_samp** plugin( Note : test_samp is the sample plugin created).
```python
	# set asset properties, using the following syntax:
	#     <plugin_name>.asset.<asset_key>.<asset_property>
	#
    # Changing the asset_name  to the GfxRegistryManager
    -test_samp.asset.artifactory_asset.asset_name: GfxRegistryManager
      # Changing to version 1.3
	-test_samp.asset.artificatory_asset.asset_version: 1.3

	[tests]
	# invoke plugin, Here plugins is the folder in which my test_samp is created 
	test_samp plugins
```

The above job assumes that that **root_url** and **asset_path** properties for the **artifactory_asset** asset key are defined in the **test_samp** plugin.

Recall that asset attributes values in a job will override identical asset values specified in a plugin.
For example, the following job attribute:

    -test_samp.asset.artifactory_asset.asset_name:
    GfxRegistryManager 

will override the asset_name dictionary value returned by the `get_assets()` method in the `test_samp` plugin:

```python
    { "artifactory_asset":
    	{ 
    	    "asset_name": "DUTPrepare",
             "asset_version":"2.14.3"
    }
```
####Asset Destination Directories
When provisioning test assets on the DUT, GTA-X will place test assets in the following directories:

| Asset Repository Type | Destination directory
| --------------------- | ---------------------
| VPG Global Asset Store (Artifactory)| <*remote_tests_dir*>/<*asset_name*>/<*asset_version*>
| Quickbuild | <*remote_tests_dir*>/<*configuration*>/<*build_version*>
| HTTP server | <*remote_tests_dir*>/<*sub_path*><br>or, if sub_path is not specified:<br><*remote_tests_dir*>
| Local directory, file share, or HTTP server | <*remote_tests_dir*>/<*local_assets*>

Using `runner.get_asset_dest_dir(asset_key)` will return the complete destination directory of the asset independently of the asset repository type.

####Access asset values in the plugin
There are cases where the `run()` or `get_assets()` methods of the plugin will need to use the asset values.
You can do this through the `runner.settings()` call.
Example from the ET test plugin above: `runner.settings('test_et.ET_tool')` will return the dictionary object for the ET_tool.

####Specify manual download of an asset
If `auto_download` is set to false, then during the plugin execution, the asset will need to be downloaded.

An asset could be downloaded manually in two ways:
- By using `runner.download_asset(asset_key)`: This action will perform the download of the specified `asset_key`. If `asset key` is not inside the dictionary pre-defined in `get_assets()`, an exception will be thrown
- By using `runner.download_assets()`: This action will perform the download of all the pending assets to be downloaded that were set as `auto_download = False`. It will return the number of assets downloaded. If no assets were downloaded, it will return 0.

If `runner.get_asset_dest_dir(asset_key)` is called before an asset is currently downloaded, an exception will be thrown

###How to Call Another Plugin

If your plugin needs to call another plugin, it is relatively simple to do this using the `runner.load_plugin` function.

Here is an example plugin, which calls the cmd.py plugin to display a "Hello World" message box on a Windows DUT:
```python
	def run(runner, line):

	    plugin_name = "cmd"
	    plugin_args = "msg * Hello World"
	    plugin = runner.load_plugin(plugin_name)
	    status = plugin.run(runner, plugin_args)
	    return status
```
###How to Specify Timeout for Runner Calls in a Plugin
The following section, we'll walk through how to set a timeout value on a specific runner.r* method call.

In your plugin code, for each runner.r* method, you can specify an optional "timeout" parameter. This timeout will be used to monitor the execution of the operation and terminate it with an exception if the operation's execution time exceeds the specified timeout. The timeout value format is in string type (numeric follows by a character represents time unit, no space), example: '10s', '10m', or '10h'.  

The following example shows how to specify timeout for a specific runner.r* operation and how to optionally handle the timeout event.  Note that if the timeout event didn't get handled by the plugin, then it will be handled in the Runner.  If the timeout event handled by the Runner, the task's status will be set to 'fail', and then moves on to the next task in the job.

```python
	def run(runner, line)
		cmd = 'cmd /c cleanup.bat'
		try:
			runner.rexecute(cmd, timeout='10s')
		except TimeoutError as te:
			runner.add_result('timeout', true)
			runner.add_error('cmd="{0}" timed out'.format(cmd))

		# reboot the system
		try:
			runner.rreboot(timeout='300s')
		except TimeoutError as te:
			runner.add_result('timeout', true)
			runner.add_error('system failed to come back from a reboot')
			return 'fail'

		# execute another command, but not handle timeout event, let the Runner core handle the timeout event
		# if timed out here, runner will catch it, and fail the task
		cmd = 'cmd /c Tests.exe -logclean ' + line + ' > "' + log_file + '"'
		exit_code = runner.rexecute(cmd, timeout='10s').exit_code
		runner.add_result('exit_code', exit_code)

		return 'pass'
```

###How to Perform Operations after Task is Complete

Note: This section describes an optional functionality to implement a `post_task_execution method`. You can use this method to perform any post-execution operations you'd like, e.g pushing crash dumps to Artifactory

if the post_task_execution() method is implemented in the plugin, it will be run after the task is completed, or after the machine is successfully recovered.


###Runner Helper Functions

This section documents the many helper functions exposed by the runner object to be used in the plugin.

####Functions

#####`.add_error(msg)`
Adds an error message to the results.txt file.

Example usage:

```python
if not os.path.exists(log_output_file_path):
    runner.add_error('missing ' + output_file_name)
    return 'fail'
```
---

#####`.add_result(name, value=None)`
Adds test result name/value pairs to the results.txt file.

Example usage:

```python
runner.add_result('test_count', {
    'total': total,
    'passing': passing,
    'failing': failing,
    'skipped': skipping
})
```
---

#####`.add_warning(msg)`
Adds a warning message to the `results.txt` file.

Example usage:

```python
runner.add_warning("Failed to copy DXGLogger.xslt to {0}.".format(r_log_dir))
```
---

#####`.clear_results()`
Clears existing results by removing the `results.txt` file and the `logs` directory.

Example usage:

```python
runner.clear_results()
runner.add_result("results_cleared_at", datetime.now())
```
---

#####`.client_setting(key=None, value=None, default_value=None, override_exist=True)`
When called with no arguments, this method will return all of the client settings.  If called with only a key, it will return the value of that key, or the `default_value`, if supplied.  If called with both a key and a value, the pair will be added to the client settings.  In this case if the key already exists, it will be overwritten, unless you set the `override_exist` flag to `False`.

Example usage:

```python
json_settings = runner.client_setting()

thin_client_url = runner.client_setting(key='url')
```
---

#####`.client_properties(key=None, value=None, default_value=None, override_exist=True)`
When called with no arguments, this method will return all of the client properties data.  If called with only a key, it will return the value of that key, or the `default_value`, if supplied.  If called with both a key and a value, the pair will be added to the client properties.  In this case if the key already exists, it will be overwritten, unless you set the `override_exist flag to `False`.

Example usage:

```python
runner.client_properties(key='monitor_' + args.vm_name, value='no')
```
---

#####`.get_seconds(timestr, default_sec=0)`
Evaluates a time string and returns the number of seconds represented by that time value.

Example usage:

```python
# sleep for 300 sec
sleep(runner.get_seconds("5m"))
```
---

#####`.load_plugin(plugin_name)`
Provides the ability to call another plugin from your plugin.

Example usage:

```python
plugin_name = "cmd"
plugin = runner.load_plugin(plugin_name)
```
---
----
#####`.log_msg(message)`
logs a message to the `results.txt` file

Example usage:

```python
# logs message 
runner.log_msg('Return code is not zero - failing task')
```
----
#####`.log_comment(msg)`
Logs a comment to the `results.txt` file.

Example usage:

```python
r_test_dir = runner.rtests_dir() + '/' + runner.client_setting('deqp_dir') + 'gles3'
runner.log_comment('test directory is %s' % r_test_dir)
```
---

#####`.log_except(msg=None)`
Logs an a formatted exception, including exception type, value, traceback, and an optional message, to the `results.txt` file.

Example usage:

```python
try:
    runner.add_result(s, runner.client_setting(s))
except:
    runner.log_except('invalid setting "%s"' % (s))
```
---

#####`.rabspath(path)`
Returns a normalized absolutized version of the pathname `path`. If the target parameter is supplied, the full path on the target machine is returned.

Example usage:

```python
sys32_path = runner.rabspath(os.path.join('C:\\', 'Windows', 'System32'))
wow64_path = runner.rabspath(os.path.join('C:\\', 'Windows', 'SysWOW64'))
```
---

#####`.rconfigs_dir(timeout='0s')`
Returns the absolute path to the remote configuration cache directory on the default client.

Example usage:

```python
# print path of DUT configs directory
print(runner.rconfigs_dir())
```

----
#####`.download_assets()`
This downloads all the pending assets to be downloaded that were set as  auto_download = False. It returns the number of assets downloaded. If no assets were downloaded, it returns 0.


Example usage:

```python
runner.download_assets()
```
----
#####`.download_asset(asset_key)`
This performs the download of the specified  asset key . If  asset key  is not inside the dictionary pre-defined in  get_assets() , an exception will be thrown.

Example usage:

```python
runner.download_asset("artifactory_asset")
```
----
#####`.renv(name, value-None,timeout='0s')`
Returns the value of the named environment variable, or a default value (if supplied) if the environment variable doesn't exist.  

Example usage:

```python
program_files = runner.renv('Programfiles')
```
---

#####`.rexecute(*args, **kwargs)`
Executes a command on the test system.
It returns an object containing the properties exit_code, stdout and stderr

Example usage:

```python
proc = runner.rexecute(cmd, cwd=test_dir)
runner.add_result('exit_code', proc.exit_code)
runner.add_result('stdout', proc.stdout)
runner.add_result('stderr', proc.stderr)
```
---

#####`.rexists(path, timeout='0s')`
Returns whether or not the provided `path` exists on the test machine.

Example usage:

```python
fulsim_path = '{0}/has/fulsim/{1}/{2}/'.format(runner.rtools_dir(), args.platform, args.fulsim)
if not runner.rexists(fulsim_path):
    runner.add_error('Unable to find remote fulsim path ' + fulsim_path)
    return 'fail'
```
---

#####`.risdir(path, timeout='0s')`
Returns `True` if the given `path` on the test  is an existing directory. Otherwise returns `False`.

Example usage:

```python
if runner.risdir(vnc_path):
    vnc_exe = os.path.join(runner.rtools_dir(), vnc_path, 'UltraVNC_1.0.9.6.2_x86_Setup.exe')
```
---

#####`.rmakedirs(path, timeout='0s')`
This method is a recursive directory creation function. It makes all intermediate-level directories needed to contain the leaf directory and returns the absolute path.  

Example usage:

```python
if runner.rexists(remote_path):
    runner.rremove(remote_path)
remote_path = runner.rmakedirs(remote_path)
```
---

#####`.rpull(src, dest, timeout='0s')`
Pulls files from the source to the destination path. 
Example usage:

```python
if not runner.rpull(stdout_file, runner.path('logs_dir')):
    runner.add_error('Cannot pull log file %s' % (stdout_file))
    return 'fail'
```
---

#####`.rpush(src, dest, timeout='0s')`
Pushes files from the controller to the test system. It only pushes files that are different so the first time it may take a while but all other calls will be quick.

Example usage:

```python
if not runner.rpush(test_dir, test_dir):
    runner.add_error('Cannot find push test folder ' + test_dir)
    return 'fail'

runner.rpush(local_scripts, remote_scripts, target='VM_HOST')
```
---

#####`.rreboot(timeout='0s')`
Reboots the test machine.

Example usage:

```python
if install_object['reboot']:
    runner.rreboot()
```
---

#####`.rremove(path,timeout='0s')`
Removes the specified directory tree or file path from controller or test machine. 

Example usage:

```python
runner.rremove(output_file_path)
```
---

#####`.rcopy(src, dest)`
Copies src file or directory to dest file or directory.

Supported usages:

```python
runner.rcopy('some-dir/some-file.txt', 'some-other-existing-dir/some-file.txt')
runner.rcopy('some-dir/some-file.txt', 'some-other-existing-dir')
runner.rcopy('some-dir', 'some-other-existing-dir/some-NON-existing-dir')
```
---

#####`.rexecute(cmd, cwd='.', expect_disconnect=False, timeout='0s', shell=True)`
Executes a command via the shell. 

Example usage:

```python
# Shutdown the client system
runner.rexecute("shutdown /r /t 1", shell=True)
```
---

#####`.rtemp_logs_dir(target=None, timeout='0s')`
Returns the absolute path to the remote temporary logs directory on the default client.

Example usage:

```python
# print path of DUT temp logs directory
print(runner.rtemp_logs_dir())
```
---

#####`.rtests_dir(timeout='0s')`
Returns the absolute path to the remote tests directory on the default client.

Example usage:

```python
# print path of DUT tests directory
print(runner.rtests_dir())
```
---

#####`.rtools_dir(timeout='0s')`
Returns the absolute path to the remote tools directory on the default client.

Example usage:

```python
# print path of DUT tools directory
print(runner.rtools_dir())
```
---

#####`.rupload(path, dest,timeout='0s')`
Uploads local files to the remote destination.

Example usage:

```python
runner.rupload(job_dir_fulsim)
```
---

#####`.set_status(status)`
Adds a status to the `results.txt` file.

Example usage:

```python
if status == 'pass' and args.reboot:
    runner.set_status('pass')
    runner.rreboot()
```
---

#####`.setting(name, value=None)`
Returns the job setting or a default value (if supplied) if the setting doesn't exist. 

Example usage:

```python
task_id = runner.setting('task_id')

timeout = int(runner.setting('timeout', 0))
```
---
