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
        color_range: ['#aaa'],
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
        color_range: ['#aaa'],
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
        color_range: ['#aaa'],
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
        color_range: ['#aaa'],
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
        color_range: ['#aaa'],
        x_accessor: 'date',
        y_accessor: 'pull_requests',
        target: '#pulls-over-time'
      });
    });
	
	//Our code begins here!!! 
	//Distribution of Work

	this.api.dist_work().then(function (dist_work) {
	   MG.data_graphic({
    	  title: "Commits/Project",
    	  data: MG.convert.date(dist_work, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
    	  chart_type: 'point',
    	  least_squares: true,
    	  full_width: true,
           height: 300,
    	  color_range: ['#aaa'],
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
      color_range: ['#aaa'],
      x_accessor: 'date',
      y_accessor: 'reopenedissues',
      target: '#reopenedissues-over-time'
    });
  });
    
    
       
	//Community Activity
	this.api.communityActivity().then(function (community_activity) {
      console.log(communityActivity);
	  
	  MG.data_graphic({
        title: "Community Activity/Week",
        data: MG.convert.date(communityActivity, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['#aaa'],
        x_accessor: 'date',
        y_accessor: 'activity',
        target: '#communityActivity-over-time'
      });
    });

	
	// Contributor Breadth
	this.api.contributorBreadth().then(function (Contributor_Breadth) {
			console.log(contributorBreadth);
		MG.data_graphic({
        title: "Core/Non-Core Contributors",
			  data: MG.convert.date(contributorBreadth, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
			  chart_type: 'point',
			  least_squares: true,
			  full_width: true,
			  height: 300,
			  color_range: ['#aaa'],
			  x_accessor: 'date',
			  y_accessor: 'watchers',
			  target: '#Contributors-over-time'
	  });
    });

	//Contributor Diversity
	this.api.contributor_diversity().then(function (contributor_diversity) {
            console.log(contributor_diversity);
        MG.data_graphic({
        title: "Contributory Diversity",
              data: MG.convert.date(contributor_diversity, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
              chart_type: 'point',
              least_squares: true,
              full_width: true,
              height: 300,
              color_range: ['#aaa'],
              x_accessor: 'date',
              y_accessor: 'num_organizations',
              target: '#contributorDiversity-over-time'
      });
    });

	  	//transparency
	this.api.transparency().then(function (transparency) {
	console.log(transparency);
	MG.data_graphic({
        title: "Number of comments per issue",
        data: MG.convert.date(transparency, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['#aaa'],
        x_accessor: 'date',
        y_accessor: 'activity',
        target: '#Number-of-comments-per-issue'
      });
    });

	  	//bus_factor
	this.api.bus_factor().then(function (bus_factor) {
      console.log(bus_factor);

	  MG.data_graphic({
        title: "Bus Factor.",
        data: MG.convert.date(bus_factor, 'date', '%Y-%m-%dT%H:%M:%S.%LZ'),
        chart_type: 'point',
        least_squares: true,
        full_width: true,
        height: 300,
        color_range: ['#aaa'],
        x_accessor: 'date',
        y_accessor: 'activity',
        target: '#bus_factor'
      });
    });


  }
};

var client = new GHDataReport();
