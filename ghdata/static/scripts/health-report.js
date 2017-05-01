/* SPDX-License-Identifier: MIT */

function GHDataReport(apiUrl) {
  apiUrl = apiUrl || '/';
  var owner = this.getParameterByName('owner');
  var repo = this.getParameterByName('repo');
  this.api = new GHDataAPIClient(apiUrl, owner, repo);
  this.buildReport();
}


GHDataReport.prototype.getParameterByName = function(name, url) {
    if (!url) {
      url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
};

GHDataReport.prototype.buildReport = function () {
  if (this.api.owner && this.api.repo) {
    document.getElementById('repo-label').innerHTML = this.api.owner + ' / ' + this.api.repo;
    // Commits
    this.api.commitsByWeek().then(function (commits) {
      MG.data_graphic({
        title: "Commits/Week",
        data: MG.convert.date(commits, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color: 'blue',
        x_accessor: 'date',
        y_accessor: 'commits',
        target: '#commits-over-time'
      });
    });

    // Stargazers
    this.api.stargazersByWeek().then(function (stargazers) {
      MG.data_graphic({
        title: "Stars/Week",
        data: MG.convert.date(stargazers, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['blue'],
        x_accessor: 'date',
        y_accessor: 'watchers',
        target: '#stargazers-over-time'
      });
    });

    // Forks
    this.api.forksByWeek().then(function (forks) {
      MG.data_graphic({
        title: "Forks/Week",
        data: MG.convert.date(forks, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['blue'],
        x_accessor: 'date',
        y_accessor: 'projects',
        target: '#forks-over-time'
      });
    });

    // Issues
    this.api.issuesByWeek().then(function (issues) {
      MG.data_graphic({
        title: "Issues/Week",
        data: MG.convert.date(issues, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['blue'],
        x_accessor: 'date',
        y_accessor: 'issues',
        target: '#issues-over-time'
      });
    });

    // Pull Requests
    this.api.pullRequestsByWeek().then(function (pulls) {
      MG.data_graphic({
        title: "Pull Requests/Week",
        data: MG.convert.date(pulls, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        
        x_accessor: 'date',
        y_accessor: 'pull_requests',
        target: '#pulls-over-time'
      });
    });
	
	//Our code begins here!!! 

	this.api.dist_work().then(function (dist_work) {
	   MG.data_graphic({
    	  title: "Distribution Of Work/Year",
    	  data: MG.convert.date(dist_work, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
    	  chart_type: 'line',
    	  least_squares: true,
    	  full_width: true,
           height: 300,
    	  
    	  x_accessor: 'date',
    	  y_accessor: 'numcommits',
    	  target: '#distribution-over-time'
     });
   });
    
   this.api.reopened_issues().then(function (reopened_issues) {
     MG.data_graphic({
      title: "Reopened Issues/Month",
      data: MG.convert.date(reopened_issues, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
      chart_type: 'line',
      least_squares: true,
      full_width: true,
      height: 300,
      
      x_accessor: 'date',
      y_accessor: 'reopenedissues',
      target: '#reopenedissues-over-time'
    });
  });
       
	//Community Activity
	this.api.community_activity().then(function (community_activity) {
	  MG.data_graphic({
        title: "Community Activity/Month",
        data: MG.convert.date(community_activity, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'line',
        least_squares: true,
        full_width: true,
        height: 300,
       
        x_accessor: 'date',
        y_accessor: 'activity',
        target: '#communityActivity-over-time'
      });
    });
	
	// Contributor Breadth
	this.api.contr_bre().then(function (contr_bre) {
	MG.data_graphic({
        	title: "Non-Core Contributors/Project",
		data: contr_bre,
		chart_type: 'bar',
		least_squares: true,
		full_width: true,
		height: 300,
		width: 490,
		
		x_accessor: 'project_name',
		y_accessor: 'num_commits',
		target: '#cont-over-time'
	  });
    });

	//Contributor Diversity
	this.api.contributor_diversity().then(function (contributor_diversity) {
		MG.data_graphic({
              title: "Contributor Diversity/Project",
              data: contributor_diversity,
              chart_type: 'bar',
              least_squares: true,
              full_width: true,
              height: 300,
	      width: 490,
             
              x_accessor: 'project_name',
              y_accessor: 'num_organizations',
              target: '#contributorDiversity-over-time'
      });
    });

	  	//transparency
	this.api.transparency().then(function (transparency) {
	console.log(transparency);
	MG.data_graphic({
        title: "Transparency",
        data: MG.convert.date(transparency, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['blue', 'red'],
        x_accessor: 'date',
        y_accessor: 'avg_comments',
        target: '#Number-of-comments-per-issue'
      });
    });

	  	//bus_factor
	this.api.bus_factor().then(function (bus_factor) {
	  MG.data_graphic({
        title: "Bus Factor",
        data: [{'date': new Date(), 'value': bus_factor[0].bus_factor}],
        least_squares: true,
        full_width: true,
        height: 200,
	width: 400,
	point_size: 5,
        target: '#bus_factor'
      });
	
    });


  }
};

var client = new GHDataReport();
