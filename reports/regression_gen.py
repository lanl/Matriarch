# Copyright (c) 2014, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright 2014. Los Alamos National Security, LLC. This software was 
# produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos
# National Laboratory (LANL), which is operated by Los Alamos National 
# Security, LLC for the U.S. Department of Energy. The U.S. Government has 
# rights to use, reproduce, and distribute this software.  NEITHER THE 
# GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY, EXPRESS
# OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If 
# software is modified to produce derivative works, such modified software 
# should be clearly marked, so as not to confuse it with the version available
# from LANL.
# 
# Additionally, redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
# · Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# · Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# · Neither the name of Los Alamos National Security, LLC, Los Alamos National
#   Laboratory, LANL, the U.S. Government, nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL 
# SECURITY, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import json
import httplib
import sys
import datetime

compile_name = "xrage_compile"
template_name = "sedov"
machine = "wf"

NUM_PROCS = 128
NUM_NODES = 8

tag = "reg_test_wf"


# first, submit compilation requests for the revision from N days ago

N = 28
d = datetime.datetime.today() - datetime.timedelta(N)
epoch = datetime.datetime.fromtimestamp(0)
offset = (d - epoch).total_seconds()

rev_string = "{" + str(d.year) + "-" + str(d.month) + "-" + str(d.day) + "}"

compile_jobs = []
compile_jobs.append({'NAME': tag + "_" + compile_name + "_" + str(d.year) + "-" + str(d.month) + "-" + str(d.day),
                     'REVISION': rev_string,
                     'template': compile_name,
                     'machine': machine,
                     'regression_tag': tag,
                     'offset': offset});



jobs = []
jobs.extend(compile_jobs)
# submit 5 jobs with each revision
for c in compile_jobs:
    for i in range(5):
        new_job = {'NAME': tag + "_" + "run" + str(i) + "_" + c['NAME'], 
                   'template': template_name,
                   'NUM_NODES': NUM_NODES, 
                   'NUM_PROCS': NUM_PROCS, 
                   'machine': machine, 
                   'XRAGE': "@@" + c['NAME'] + "@@",
                   'depends': [c['NAME']],
                   'PROBLEM_SIZE': "1800",
                   'regression_tag': tag,
                   'offset': c['offset']};

        jobs.append(new_job)
    

import submit_batch
submit_batch.submit(jobs)

