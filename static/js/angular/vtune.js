// Copyright (c) 2014, Los Alamos National Security, LLC
// All rights reserved.
// 
// Copyright 2014. Los Alamos National Security, LLC. This software was 
// produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos
// National Laboratory (LANL), which is operated by Los Alamos National 
// Security, LLC for the U.S. Department of Energy. The U.S. Government has 
// rights to use, reproduce, and distribute this software.  NEITHER THE 
// GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY, EXPRESS
// OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If 
// software is modified to produce derivative works, such modified software 
// should be clearly marked, so as not to confuse it with the version available
// from LANL.
// 
// Additionally, redistribution and use in source and binary forms, with or
// without modification, are permitted provided that the following conditions
// are met:
// · Redistributions of source code must retain the above copyright notice,
//   this list of conditions and the following disclaimer.
// · Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
// · Neither the name of Los Alamos National Security, LLC, Los Alamos National
//   Laboratory, LANL, the U.S. Government, nor the names of its contributors
//   may be used to endorse or promote products derived from this software
//   without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND
// CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
// NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
// PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL 
// SECURITY, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
// OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
// OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
// ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

function vTuneCtrl($scope, $http) {
	
	$scope.templates = [];
	$scope.selectedTemplate = false;
	
	$scope.runs = [];

	$scope.columnIDs = [0];
	$scope.selectedRuns = {};
	$scope.data = [];

	$scope.addColumn = function() {
		$scope.columnIDs.push($scope.columnIDs.length);
	};

	$scope.$watch(function () { return $scope.selectedTemplate; }, function () {
		// get the runs for this template
		$http.get("/api/data/" + $scope.selectedTemplate.name).success(function(d, s) {
			$scope.runs = d;
		});
	});
	
	$scope.$watchCollection('selectedRuns', function() {
		// first, calculate the deltas between functions in multiple runs
		for (var i = 1; i < $scope.columnIDs.length; i++) {
			if (!($scope.columnIDs[i] in $scope.selectedRuns))
				continue;

			$scope.selectedRuns[$scope.columnIDs[i]].hotspots.forEach(function (e, idx) {
				var funcname = e['function'];

				// find this function in the previous run
				var prevIdx = $scope.selectedRuns[$scope.columnIDs[i-1]].hotspots.findIndex(function (j) {
					return (j['function'] == funcname);
				});

				if (prevIdx == -1) {
					e.delta = "danger";
					e.idxIcon = "glyphicon glyphicon-arrow-up";
					return;
				}

				var prev = $scope.selectedRuns[$scope.columnIDs[i-1]].hotspots[prevIdx];

				var diff = e.percent - prev.percent;
				if (diff < 2.0 && diff > -2.0) {
					e.delta = ""; // about as fast
				} else if (diff < 2.0) {
					e.delta = "success"; // faster
				} else {
					e.delta = "danger"; // slower
				}

				diff = idx - prevIdx;
				if (diff == 0) {
					e.idxIcon = "glyphicon glyphicon-minus";
				} else if (diff > 0) {
					e.idxIcon = "glyphicon glyphicon-arrow-down";
				} else if (diff < 0) {
					e.idxIcon = "glyphicon glyphicon-arrow-up";
				}
				
					
			});
		}


		$scope.data = [];
		// essentially transpose the selected hotspot lists
		var currRow = 0;
		while (true) {
			var transposedRow = [];
			var columnDict = {};
			for (var i = 0; i < $scope.columnIDs.length; i++) {
				var job = $scope.selectedRuns[$scope.columnIDs[i]];
				if (!job) {
					transposedRow.push("");
					return;
				}
				if (job.hotspots.length > currRow) {
					transposedRow.push(job.hotspots[currRow]);
				}
			}
			currRow++;
			if (transposedRow.length == 0) 
				break;
			
			$scope.data.push(transposedRow);
		}
	});
	
	
	
	$http.get("/api/benchmarks").success(function(data, status) {

		$scope.templates = data;
	});
}
