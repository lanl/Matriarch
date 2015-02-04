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

import matriarch
from bottle import route, run, static_file, view, request, redirect, auth_basic
import os
import json


def check(user, password):
    return user == "admin" and password == "admin"


import argparse

parser = argparse.ArgumentParser("Run a web frontend for Matriarch")
parser.add_argument('--port', metavar='P', type=int, help="The port to listen on (defaults to 8081)", default=8081)

args = parser.parse_args()

with matriarch.MatriarchBackend() as mb:

    @route("/")
    @view('index')
    @auth_basic(check, realm="This system may contain controlled data. Do not access this system without a NTK.")
    def index():
        return {'jobs': mb.get_jobs()}

    @route("/submit")
    @view('submit')
    @auth_basic(check, realm="This system may contain controlled data. Do not access this system without a NTK.")
    def submit():
        return

    @route("/analysis")
    @view('analysis')
    @auth_basic(check, realm="This system may contain controlled data. Do not access this system without a NTK.")
    def analysis():
        return


    @route("/job/<jobid>")
    @view('job')
    @auth_basic(check, realm="This system may contain controlled data. Do not access this system without a NTK.")
    def job_by_id(jobid):
        j = mb.get_job_by_id(int(jobid))
        return {'job': j}


    @route("/api/machines")
    def api_machines():
        # return a JSON object containing a list of machines that we can run on
        return json.dumps(mb.get_machines())

    @route("/api/benchmarks")
    def api_benchmarks():
        # return a JSON object containing all the needed information about the
        # available benchmarks
        toR = []
        for template in mb.get_templates():
            toAppend = dict()
            toAppend['name'] = template.get_name()
            toAppend['vars'] = []
            for var in sorted(list(template.get_variables())):
                toAppend['vars'].append({'name': var, 
                                         'desc': template.get_variable_description(var)})
            toR.append(toAppend)

        return json.dumps(toR)


    @route("/api/delete/<jobid>")
    def api_delete(jobid):
        mb.delete_job_by_id(jobid)
        redirect("/")

    @route("/api/submit", method='POST')
    def api_submit():
        tmpl = request.json['template']
        deps = request.json['depends'] if 'depends' in request.json else []
        if 'machine' in request.json:
            mb.submit_job(tmpl, request.json['NAME'], request.json, depends_on=deps, machine=request.json['machine'])
        else:
            mb.submit_job(tmpl, request.json['NAME'], request.json, depends_on=deps)
        return "Job submitted"

    @route("/api/data/<template>")
    def api_data(template):
        jobs = mb.get_jobs_for_template(template)
        jobs = filter(lambda x: x.is_complete() and not x.has_error(), jobs)

        def get_job_data(job):
            toR = dict()
            for k, v in job.get_params().items():
                toR[k] = v

            toR['DURATION'] = job.get_duration()
            toR['jobid'] = job.get_id();
            return toR

        jobs = map(get_job_data, jobs)
        return json.dumps(jobs)

            

    @route('/static/<filepath:path>')
    def static(filepath):
        path = os.path.realpath(__file__)
        path = os.path.split(path)[0]
        path = os.path.join(path, "static/")
        return static_file(filepath, root=path)


    run(host='localhost', port=args.port)

