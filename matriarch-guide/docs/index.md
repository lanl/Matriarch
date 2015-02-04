# Matriarch User's Guide
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" href="http://purl.org/dc/dcmitype/Text" property="dct:title" rel="dct:type">Matriarch User's Guide</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="http://rmarcus.info" property="cc:attributionName" rel="cc:attributionURL">Ryan Marcus</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.


>The performance of a particular HPC code depends on a multitude of variables, including compiler selection, optimization flags, OpenMP pool size, file system load, memory usage, MPI configuration, etc. As a result of this complexity, current predictive models have limited applicability, especially at scale. 
> 
>We present Matriarch, a tool designed to aid developers in building accurate predictive models of complex HPC codes. Matriarch provides a framework for repeatedly compiling, scheduling, monitoring, and analyzing codes on modern HPC systems like those found at Los Alamos. We have used Matriarch to quickly perform weak scaling studies, strong scaling studies, hotspot profiling, MPI tracing, and performance regression analysis on LANL's xRage, a hydrodynamics code. 
> 
>As a result, we have identified scalability issues within hotspots, located MPI communication imbalances (due to AMR and domain decomposition biasing), and developed models that accurately predict xRage's performance at scale. 
> 
>These insights provide valuable guidance for software developers seeking to optimize their codes, as well as for HPC engineers seeking to better understand a system's bottlenecks and resource limitations.


Matriarch Abstract, [LA-UR-14-25734](http://permalink.lanl.gov/object/tr?what=info:lanl-repo/lareport/LA-UR-14-25734)


## Introduction
### Prerequistes
Matriarch can run on any cluster that supports the `checkjob` command with the `-xml` option, like the one distributed with [MOAB](http://www.adaptivecomputing.com/products/hpc-products/moab-hpc-suite-enterprise-edition/). Support for other clusters and software could easily be added by implementing the `checkjob` command or by modifying Matriarch to use a different command.

### Terminology

- A `cluster` or a `machine` refers to a set of nodes controlled by a resource management system, like MOAB or Slurm.
- A `template` refers to a set of files that tell Matriarch how to run a particular test
- A `job` or `run` is a set a parameters that are passed to a template and submitted to the resource manager

### High-level overview
Matriarch provides a set of tools for automated performance analysis. Users of Matriarch create templates, which are a set of files that Matriarch can deploy and run. The system is extremely flexible, and many of the suggestions in the documentation here only serve to show what Matriarch can do. Once you have a good understanding of how the job monitoring, deployment, and extraction systems work, you can use Matriarch for a wide range of tasks, including:

- Regression testing (both performance and correctness)
- Strong and weak scaling studies
- Hotspot profiling
- Memory bandwidth analysis
- Integrity checking
- and much, much more...

The general Matriarch workflow involves **creating a template**, creating a **batch job** that will be generated via that template, **deploying** that template with each set of parameters, **monitoring** each of the jobs as they are scheduled and completed, ensuring that your template properly **extracts data** from the completed jobs, and then **analyzing** that data.

## Configuration file
On startup, Matriarch looks for the file `~/.matriarchrc.json`, which describes the clusters available to Matriarch and the locations of template files. An example configuration file is shown below.

    {
        "machines": ["blair", "chuck", "dan", "serena"],
        "deployment": { "blair": "/scratch/rmarcus/matriarch_deploy/bl/",
     		            "chuck": "/scratch/rmarcus/matriarch_deploy/ck/",
     		            "dan": "/scratch/rmarcus/matriarch_deploy/dn/",
     		            "serena": "/lscratch1/rmarcus/matriarch_deploy/sr/" },
        "templates": [ "~/hpcg_matriarch", "~/my_cool_templates/" ]
    }

- The `machines` section provides a list of available clusters that Matriarch can access. The name of the machine given must prefix-match the hostname of the machine (for example, `dan` would match `dan-frontend1`, but not `frontend-dan`).

- The `deployment` section tells Matriarch where to store files needed for a given job or run for each machine. You must give a path for each machine used, and each path must be accessible from both the frontend and backend nodes of that machine.

- The `templates` section tells Matriarch where to scan for templates. For more information about templates, read the templates section.

## Templates
A template is a set of files and folders with a very specific structure:

	template_directory/                    # must be listed in the config file
	    my_template/                       # name of your template
            var_desc.json                  # a file containing a description of the variables in your template
			_template/                     # everything in this folder will be included in a deployment
			    deploy                     # a deployment script that must submit a job to a resource management and print out the job id
				extract                    # an extraction script that runs after a job has completed and returns JSON representing job results
				my_input_deck              # any other files needed by your template
	    my_other_template/                 # another template

Templates are best explained by example. Say you have a `MPI`/`OpenMP` code called `HYDRO`, and you want to do some scaling studies on it. First, you'll need to come up with a test problem for `HYRDRO` and a corresponding input deck. Let's call our test problem `cavity`. Generally, in order to run `HYDRO`, you would have an input deck that looked something like this:

    OMP_THREADS = 2
	grid_size_x = 40
	grid_size_y = 40
	boundry_condition = (i,0) -> 1
	boundry_condition = (0,i) -> 0
	boundry_condition = (-1,i) -> 0
	...

And you might run `HYDRO` using a command like this:

    # some command to acquire 4 nodes, each with 16 CPUs
	llogin -n 4
	# the command to run HYDRO
	mpirun -n 64 /path/to/HYDRO input_deck.txt

Now, if you want to perform strong and weak scaling studies, you'd want to vary the problem size (`grid_size_x` and `grid_size_y`), the number of nodes used (`llogin -n 4`), the number of `MPI` ranks (`mpirun -n 64`), and the number of `OpenMP` threads (`OMP_THREADS = 2`). In order to do this, we'll create a template named `cavity_run`, with a `deploy` script like this:

    #! /bin/bash
	# file: deploy
	# Script to deploy run %%NAME%%

	llogin -n %%NODES%%
	mpirun -n %%RANKS%% /path/to/HYDRO input_deck.txt

Note that `llogin` is only being used as an example. Generally, one would want to use a command like `msub` or something else that works from a script.

We then create an `input_deck.txt` file like this:

    # file: input_deck.txt
    OMP_THREADS = %%THREADS%%
	grid_size_x = %%PROBLEM_SIZE%%
	grid_size_y = %%PROBLEM_SIZE%%
	boundry_condition = (i,0) -> 1
	boundry_condition = (0,i) -> 0
	boundry_condition = (-1,i) -> 0
	...

Next, we create an extraction script like this:

    #! /bin/python
	# file: extract
	import json
	toR = dict()
	toR['cycle_time'] = get_cycle_time()
	toR['other_important_stat'] = get_important_stat()
	print(json.dumps(toR))

And finally, we create a `var_desc.json` file like this:

    {
	  "NAME": "The name of this particular run"
	  "NODES": "The number of nodes allocated for this run",
	  "RANKS": "The number of MPI ranks used for this run",
	  "THREADS": "The number of OMP threads to use per rank",
	  "PROBLEM_SIZE": "The X and Y grid size of the problem"
	}

Note that every template must have the `NAME` variable. Next, we start up Matriarch by typing `python frontend.py`, and we should see output like this:

    $ python frontend.py
    INFO:root:Matriarch started on dan
    INFO:root:Using deployment directory /scratch/rmarcus/matriarch_deploy/dn/
    INFO:root:Found template at /users/rmarcus/HYDRO_templates/cavity_run

When our template is deployed, each instance of `%%(.*)%%` will be replaced with a specified value.

## Submitting jobs
There are two ways to submit jobs with Matriarch. For submitting a single job, using the web interface is probably the best way to go. For submitting a large number of jobs, using a batch job script will likely save a lot of time.

### With the web interface
After running Matriarch via `frontend.py`, use a web browser to access `http://localhost:8081`, substituting `8081` for whatever port you picked. Then, click on "Submit Job" in the top bar. From here, you can select a template (in our example, `cavity_run`), and enter values for each variable. After clicking on the "Submit" button, a box will appear stating the job was submitted.

That's it! You can use whatever tools your resource manager provides (commonly `squeue` or `showq`) to see your submitted job, or you can click on "Home" in the top bar to view the job in Matriarch.

You can also manually verify the deployment of the template by examining the deployment directory. Continuing with our example, assuming one had submitted a run with 2 nodes, 32 ranks, 2 threads, and a problem size of 800:

    $ cd /scratch/rmarcus/matriarch_deploy/dn/cavity_run/NAME_OF_MY_RUN
	$ ls
	extract deploy input_deck.txt
	$ cat deploy
	#! /bin/bash
	# file: deploy
	# Script to deploy run NAME_OF_MY_RUN

	llogin -n 2
	mpirun -n 32 /path/to/HYDRO input_deck.txt
	$ cat input_deck.txt
    # file: input_deck.txt
    OMP_THREADS = 2
	grid_size_x = 800
	grid_size_y = 800
	boundry_condition = (i,0) -> 1
	boundry_condition = (0,i) -> 0
	boundry_condition = (-1,i) -> 0
	...

Examining the deployed output can be very useful for debugging. If a run seems to be constantly failing or not even running, trying to manually run the `deploy` script can often give useful output.

### With a batch script
For submitting large numbers of runs, you can create a simple JSON file like this one:

    [ {"NAME": "run1", "machine": "serena", "template": "cavity_flow", "NODES": "1", "RANKS": "16", "PROBLEM_SIZE": "800", "THREADS": "2"},
	  {"NAME": "run2", "machine": "serena", "template": "cavity_flow", "NODES": "2", "RANKS": "32", "PROBLEM_SIZE": "800", "THREADS": "2"},
	  {"NAME": "run3", "machine": "serena", "template": "cavity_flow", "NODES": "3", "RANKS": "48", "PROBLEM_SIZE": "800", "THREADS": "2"},
	  {"NAME": "run4", "machine": "serena", "template": "cavity_flow", "NODES": "4", "RANKS": "64", "PROBLEM_SIZE": "800", "THREADS": "2"} ]

You can submit all four of these runs with the `submit_batch.py` script:

    $ python submit_batch.py ~/batch_jobs/strong.json
    Submitting run1
    Submitting run2
    Submitting run3
    Submitting run4
	$

Note that, in general, you should try to make run names unique.

After submitting these jobs, you can use your resource manager's tools to inspect your jobs, or you can go to the Matriarch homepage.

## Analysis
Matriarch currently supports two types of analysis, line graphs and hotspots.

### Raw data access
You can extract data from Matriarch by using the simple web API or by directly accessing the SQLite3 database (called `matriarch.db` in the same folder as `frontend.py`). This should let you perform your own analysis using your own packages fairly easily. Eventually, we hope to integrate many more analysis types into Matriarch to make this unnecessary.

### Line graph
You can use Matriarch to create plots of data. The "Analysis" link on the top bar will take you to the proper page. There, you can select a template and plot multiple series of data. If you click on the "Options" button, you can enable a simple linear regression for each data series. Note that the fields for the series support JavaScript, so you can set the x-axis to `Math.pow(PROBLEM_SIZE, 2)` or use a filter like `DURATION > 500`.

You can add an additional series by pressing the "Add Series" button, and you can remove a series by pressing the large minus button next to a series. Each series will be plotted in a different color.

At the bottom of the page, all the records that match your filters will be displayed in a table. The line graph is driven by [AngularJS](https://angularjs.org), so you can use [PhantomJS](http://phantomjs.org) or any other headless browser to automatically generate various reports.

### Hotspot
On the same page as the line graph, clicking on the "hotspot" tab will reveal the hotspot visualizer. If your template collects hotspots (see advanced topics), you can compare hotspot profiles here by selecting a run with hotspots. To compare multiple hotspot profiles, click on the plus button and select another template.

# Advanced Usage

## Job Dependencies
For regression analysis and perhaps just to make sure one is always running the most recent version of the code, it can be desirable to make a template for compiling and one's applications from version control. This can be done using the standard templating system fairly easily. However, in order to schedule a job that runs using code compiled by another job, one needs a way to make sure that the jobs using the compiled code do not execute before the code has finished compiling.

When submitting jobs using a batch script, it is possible to specify a list of jobs that must complete before another job runs. This is accomplished by using the special key "depends." For example, if I had a template called `hydro_compile` which produced an executable of `hydro` and put it into some common location, I could then schedule a small strong scaling study to run only after my compilation had complete:

    [ {"NAME": "hydro_head", "machine": "serena", "template": "hydro_compile", "REVISION": "head"},
	  {"NAME": "run1", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "1", "RANKS": "16", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run2", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "2", "RANKS": "32", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run3", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "3", "RANKS": "48", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run4", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "4", "RANKS": "64", "PROBLEM_SIZE": "800", "THREADS": "2"} ]

Note that dependencies are referenced by name. Having multiple jobs with the same name can lead to complications, so you should try to avoid it.

If you make a job depend on a job that does not currently exist (has not been submitted), the job will wait in the queue until a job by the specified name completes.


## Hotspots
In order to take advantage of Matriarch's hotspot comparison tool, you'll have to modify your `extract` script to return a special structure:

	{ "hotspots": [ { "function": "myFunc", "lib": "hydro", "percent": "52.2" },
	                { "function": "mpifunc", "lib": "mpi", "percent": "30" },
					...
					],
	...
	}

Each `function` value is the name of a function, each `lib` value is the library where the function lives (provided by vTune and gprof), and `percent` is the percentage of time that the function took. If your extract script returns a JSON object with a `hotspots` entry, Matriarch will automatically recognize it and will make the data available.

## Global variables
Matriarch allows jobs to set global variables when they complete. These global variables can then be used in batch job scripts. For example, if our compilation template supported compiling an arbitrary revision, we could have it set a global variable with the path to the compiled executable.

In order to set global variables, your `extract` script must return a special structure:
	{ "matriarch_set_globals": [ {"NAME_OF_GLOBAL": "value of global"},
	                             {"ANOTHER_GLOBAL": "value of another global"},
								 ... ]
	...
	}

Note that your execution script gets deployed just like any other file in the `_template` folder, so you can make your script set a global equal to the name of run with:

	{ "matriarch_set_globals": [ {"%%NAME%%": "value of global"},
	                             {"ANOTHER_GLOBAL": "value of another global"},
								 ... ]
	...
	}


You can reference a global variable in a batch script by using `@@GLOBAL_NAME@@`. Assuming one had a compile template that returned a path to the compiled executable in a global with the same name as the run of the template, and assuming that our `hydro` template took the path to the `hydro` code via the parameter `EXEC`, we could build a regression test batch script like this:


    [ {"NAME": "hydro_head", "machine": "serena", "template": "hydro_compile", "REVISION": "head"},
	  {"NAME": "hydro_yesterday", "machine": "serena", "template": "hydro_compile", "REVISION": "{2014-XX-XX}"},
	  {"NAME": "hydro_last_week", "machine": "serena", "template": "hydro_compile", "REVISION": "{2014-XX-XX}"},
	  {"NAME": "run1", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "1", "RANKS": "16", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run2", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "2", "RANKS": "32", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run3", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "3", "RANKS": "48", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run4", "depends": ["hydro_head"], "EXEC": "@@hydro_head@@", "machine": "serena", "template": "cavity_flow", "NODES": "4", "RANKS": "64", "PROBLEM_SIZE": "800", "THREADS": "2"},
	  {"NAME": "run_yesterday1", "depends": ["hydro_yesterday"], "EXEC": "@@hydro_yesterday@@", "machine": "serena", "template": "cavity_flow", "NODES": "1", "RANKS": "16", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run_yesterday2", "depends": ["hydro_yesterday"], "EXEC": "@@hydro_yesterday@@", "machine": "serena", "template": "cavity_flow", "NODES": "2", "RANKS": "32", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run_yesterday3", "depends": ["hydro_yesterday"], "EXEC": "@@hydro_yesterday@@", "machine": "serena", "template": "cavity_flow", "NODES": "3", "RANKS": "48", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run_yesterday4", "depends": ["hydro_yesterday"], "EXEC": "@@hydro_yesterday@@", "machine": "serena", "template": "cavity_flow", "NODES": "4", "RANKS": "64", "PROBLEM_SIZE": "800", "THREADS": "2"},
	  {"NAME": "run_last_week1", "depends": ["hydro_last_week"], "EXEC": "@@hydro_last_week@@", "machine": "serena", "template": "cavity_flow", "NODES": "1", "RANKS": "16", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run_last_week2", "depends": ["hydro_last_week"], "EXEC": "@@hydro_last_week@@", "machine": "serena", "template": "cavity_flow", "NODES": "2", "RANKS": "32", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run_last_week3", "depends": ["hydro_last_week"], "EXEC": "@@hydro_last_week@@", "machine": "serena", "template": "cavity_flow", "NODES": "3", "RANKS": "48", "PROBLEM_SIZE": "800", "THREADS": "2"},
      {"NAME": "run_last_week4", "depends": ["hydro_last_week"], "EXEC": "@@hydro_last_week@@", "machine": "serena", "template": "cavity_flow", "NODES": "4", "RANKS": "64", "PROBLEM_SIZE": "800", "THREADS": "2"}
	]

