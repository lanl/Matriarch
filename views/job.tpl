<!--
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
-->

% include('header')
<h3>Job {{ job.get_id() }}</h3>
<a class="btn btn-danger" href="/api/delete/{{ job.get_id() }}">Delete Job</a>

<table class="table">
  <thead>
    <tr><th>MOAB Property</th><th>Value</th></tr>
  </thead>

  <tbody>
    <tr><td>Submission time</td><td class="time" colspan="2">{{ job.get_submission_time() }}</td></tr>
    <tr><td>Start time</td><td class="time" colspan="2">{{ job.get_start_time() }}</td></tr>
    <tr><td>Completion time</td><td class="time" colspan="2">{{ job.get_completion_time() }}</td></tr>
    <tr><td>Duration</td><td class="duration" colspan="2">{{ job.get_duration() }}</td></tr>
    <tr><td>User</td><td colspan="2">{{ job.get_user() }}</td></tr>
    <tr><td>State</td><td colspan="2">{{ job.get_state() }}</td></tr>
    <tr><td>Machine</td><td colspan="2">{{ job.get_hostname() }}</td><tr>
  </tbody>

  <thead>
    <tr><th>Job Property</th><th>Value</th></tr>
  </thead>

  <tbody>
    % for p in job.get_params():
    % if p != 'hotspots' and p != 'MATRIARCH_SET_GLOBALS':
    <tr><td>{{ p }}</td><td colspan="2">{{ job.get_params()[p] }}</td></tr>
    % end
    % end
  </tbody>

% if 'MATRIARCH_SET_GLOBALS' in job.get_params():
  <thead>
    <tr><th>Global</th><th>Set to value</th></tr>
  </thead>
  <tbody>
    % for k,v in job.get_params()['MATRIARCH_SET_GLOBALS'].items():
    <tr><td>{{ k }}</td><td>{{ v }}</td></tr> 
    % end
  </tbody>
% end

% if 'hotspots' in job.get_params():
  <thead>
    <tr><th>Function</th><th>From</th><th>Time</th></tr>
  </thead>
  <tbody>
    % for h in job.get_params()['hotspots']:
    <tr><td>{{ h['function'] }}</td><td>{{ h['lib'] }}</td><td>{{ h['percent'] }}%</td></tr>
    % end
  </tbody>
% end
</table>


% include('footer')
