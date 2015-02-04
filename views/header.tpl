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

<!DOCTYPE html>
<html lang="en" ng-app>
  <head>
    <link rel="stylesheet" type="text/css" href="/static/css/bootstrap.min.css" />
    <script type="text/javascript" src="/static/js/polyfill.js"></script>
    <script type="text/javascript" src="/static/js/d3.min.js"></script>
    <script type="text/javascript" src="/static/js/jquery.min.js"></script>
    <script type="text/javascript" src="/static/js/bootstrap.min.js"></script>
    <script type="text/javascript" src="/static/js/moment.min.js"></script>

    <script type="text/javascript" src="/static/js/timeTransform.js"></script>

    <script type="text/javascript" src="/static/js/angular.min.js"></script>
    <script type="text/javascript" src="/static/js/angular/submit.js"></script>
    <script type="text/javascript" src="/static/js/angular/analysis.js"></script>
    <script type="text/javascript" src="/static/js/angular/vtune.js"></script>
    <title>Matriarch</title>
  </head>
  
  <body>
    <div class="navbar navbar-inverse">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="/">Matriarch</a>
        </div>
        <div class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
            <li><a href="/">Home</a></li>
            <li><a href="/submit">Submit Job</a></li>
	    <li><a href="/analysis">Analysis</a></li>
            <li><a href="/help">Help</a></li>
        </div><!--/.nav-collapse -->
      </div>
    </div>


    <div class="container">
      <div class="row">
