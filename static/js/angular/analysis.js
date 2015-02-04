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

function AnalysisCtrl($scope, $http) {
	$scope.templates = [];
	$scope.selectedTemplate = false;


	$scope.unfilteredData = [];
	$scope.filteredData = [];
	$scope.filter = "";
	$scope.filterError = false;

	$scope.series = [{
		'xAxis': "",
		'yAxis': "",
		'xAxisError': true,
		'yAxisError': true,
		'filter': "",
		'filterError': false
	}];

	$scope.xAxis = "";
	$scope.yAxis = "";
	$scope.xAxisError = true;
	$scope.yAxisError = true;

	$scope.xAxisMin = 0;
	$scope.xAxisMax = 0;
	$scope.yAxisMin = 0;
	$scope.yAxisMax = 0;

	$scope.showSLR = false;
	$scope.slrValues = [];

	$scope.plottedData = [];

	$scope.$watch(function () { return $scope.selectedTemplate; }, function() {
		if ((!$scope.selectedTemplate) || !($scope.selectedTemplate.vars))
			return;


		$http.get("/api/data/" + $scope.selectedTemplate.name).success(function(d, s) {
			$scope.unfilteredData = d;
		});
	});


	$scope.addSeries = function() {
		$scope.series.push({
			'xAxis': "",
			'yAxis': "",
			'xAxisError': true,
			'yAxisError': true,
			'filter': "",
			'filterError': false
		});
	};

	$scope.removeSeries = function(i) {
		$scope.series.splice(i, 1);
	};


	$scope.$watch(function () { return $scope.series; }, function() {
		$scope.replot();
	}, true);

	$scope.$watchCollection('unfilteredData', function () {
		$scope.replot();
	});

	$scope.filterData = function(series) {
		return $scope.unfilteredData.filter(function (i) {
			var include = true;
			if (series.filter != "") {
				try {
					series.filterError = false;
					include = evalWithScope(i, series.filter);
				} catch (e) {
					include = false;
					series.filterError = true;
				}
			}
			return include;
		});
	};

	$scope.replot = function() {
		var xAxisMin = Number.MAX_VALUE;
		var xAxisMax = Number.MIN_VALUE;
		var yAxisMin = Number.MAX_VALUE;
		var yAxisMax = Number.MIN_VALUE;

		$scope.slrValues = [];
	
		
		$scope.plottedData = [];
		$scope.Rvals = [];
		$scope.slr = [];
		$scope.series.forEach(function (s) {
			
			var avg_x = 0.0;
			var avg_y = 0.0;
			var n = 0;

			// rescale axis, collect data
			var seriesData = [];
			$scope.filteredData = $scope.filterData(s);
			$scope.filteredData.forEach(function (i) {
				var include = true;
				if (s.filter != "") {
					try {
						s.filterError = false;
						include = evalWithScope(i, s.filter);
					} catch (e) {
						include = false;
						s.filterError = true;
					}
				}

				if (!include)
					return;

			
				try {
					s.xAxisError = false;
					var x = parseFloat(evalWithScope(i, s.xAxis));
				} catch (e) {
					x = 0;
					s.xAxisError = true;
				}

				try {
					s.yAxisError = false;
					var y = parseFloat(evalWithScope(i, s.yAxis));
				} catch (e) {
					y = 0;
					s.yAxisError = true;
				}

				n++;
				avg_x += x;
				avg_y += y;
				
				xAxisMin = Math.min(x, xAxisMin);
				xAxisMax = Math.max(x, xAxisMax);
				yAxisMin = Math.min(y, yAxisMin);
				yAxisMax = Math.max(y, yAxisMax);
				

				seriesData.push({'x': x, 'y': y});
			});

			avg_x /= n;
			avg_y /= n;
			
			var numerator = 0.0;
			var denom1 = 0.0;
			var denom2 = 0.0;

			seriesData.forEach(function (i) {
				numerator += ((i.x - avg_x) * (i.y - avg_y));
				denom1 += Math.pow((i.x - avg_x), 2);
				denom2 += Math.pow((i.y - avg_y), 2);
				//console.log(numerator + ", " + denom1 + ", " + denom2);
			});

			var R = numerator / (Math.sqrt(denom1) * Math.sqrt(denom2));

			var std_x = 0.0;
			var std_y = 0.0;

			std_x = Math.sqrt(((1.0 / seriesData.length) * denom1));
			std_y = Math.sqrt(((1.0 / seriesData.length) * denom2));

			var tbeta = R * (std_y / std_x);
			var talpha = avg_y - tbeta * avg_x;

			$scope.slrValues.push({'beta': tbeta, 'alpha': talpha});

			R = Math.round10(R, -3);
			$scope.Rvals.push(R);
			$scope.plottedData.push(seriesData);
		});

		//xAxisMax *= 1.1;
		//yAxisMax *= 1.1;
		//xAxisMin *= 0.9;
		//yAxisMin *= 0.9;

		

				   
		$scope.xAxisMin = Math.round(xAxisMin);
		$scope.xAxisMax = Math.round(xAxisMax);
		$scope.yAxisMin = Math.round(yAxisMin);
		$scope.yAxisMax = Math.round(yAxisMax);



		// scale data to percentages
		var xAdj = 0.0 - xAxisMin;
		var yAdj = 0.0 - yAxisMin;

		$scope.slr = [];
		$scope.plottedData.forEach(function(s) {
			$scope.slrValues.forEach(function (i) {
				var slr = {};
				slr.x1 = parseFloat(xAxisMin);
				slr.y1 = parseFloat(i.alpha + i.beta * xAxisMin);
				slr.x2 = parseFloat(xAxisMax);
				slr.y2 = parseFloat(i.alpha + i.beta * xAxisMax);

				
				slr.x1 = (5.0 + (((parseFloat(slr.x1) + xAdj) / (xAxisMax + xAdj)) * 90.0));
				slr.x2 = (5.0 + (((parseFloat(slr.x2) + xAdj) / (xAxisMax + xAdj)) * 90.0));
				slr.y1 = 100.0 - (5.0 + (((parseFloat(slr.y1) + yAdj) / (yAxisMax + yAdj)) * 90.0));
				slr.y2 = 100.0 - (5.0 + (((parseFloat(slr.y2) + yAdj) / (yAxisMax + yAdj)) * 90.0));
				
				$scope.slr.push(slr);
			});
			
			s.forEach(function(i) {
				i.x = (5.0 + (((parseFloat(i.x) + xAdj) / (xAxisMax + xAdj)) * 90.0));
				i.y = 100.0 - (5.0 + (((parseFloat(i.y) + yAdj) / (yAxisMax + yAdj)) * 90.0));
			});
		});
	};



	$http.get("/api/benchmarks").success(function(data, status) {
		$scope.templates = data;
	});


}
