# SPDX-License-Identifier: MIT
import pandas as pd
import sqlalchemy as s
import sys
import json
import re


class GHTorrent(object):
    """Uses GHTorrent and other GitHub data sources and returns dataframes with interesting GitHub indicators"""

    def __init__(self, dbstr):
        """
        Connect to GHTorrent
        :param dbstr: The [database string](http://docs.sqlalchemy.org/en/latest/core/engines.html) to connect to the GHTorrent database
        """
        self.DB_STR = dbstr
        self.db = s.create_engine(dbstr)

    def __single_table_count_by_date(self, table, repo_col='project_id'):
        """
        Generates query string to count occurances of rows per date for a given table.
        External input must never be sent to this function, it is for internal use only.
        :param table: The table in GHTorrent to generate the string for
        :param repo_col: The column in that table with the project ids
        :return: Query string
        """
        return """
            SELECT date(created_at) AS "date", COUNT(*) AS "{0}"
            FROM {0}
            WHERE {1} = :repoid
            GROUP BY WEEK(created_at)""".format(table, repo_col)

    def repoid(self, owner, repo):
        """
        Returns a repository's ID as it appears in the GHTorrent projects table
        github.com/[owner]/[project]
        :param owner: The username of a project's owner
        :param repo: The name of the repository
        :return: The repository's ID as it appears in the GHTorrent projects table
        """
        reposql = s.sql.text(
            'SELECT projects.id FROM projects INNER JOIN users ON projects.owner_id = users.id WHERE projects.name = :repo AND users.login = :owner')
        repoid = 0
        result = self.db.execute(reposql, repo=repo, owner=owner)
        for row in result:
            repoid = row[0]
        return repoid

    def userid(self, username):
        """
        Returns the userid given a username
        :param username: GitHub username to be matched against the login table in GHTorrent
        :return: The id from the users table in GHTorrent
        """
        reposql = s.sql.text('SELECT users.id FROM users WHERE users.login = :username')
        userid = 0
        result = self.db.execute(reposql, username=username)
        for row in result:
            userid = row[0]
        return userid

    # Basic timeseries queries
    def stargazers(self, repoid, start=None, end=None):
        """
        Timeseries of when people starred a repo
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with stargazers/day
        """
        stargazersSQL = s.sql.text(self.__single_table_count_by_date('watchers', 'repo_id'))
        return pd.read_sql(stargazersSQL, self.db, params={"repoid": str(repoid)})

    def commits(self, repoid):
        """
        Timeseries of all the commits on a repo
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with commits/day
        """
        commitsSQL = s.sql.text(self.__single_table_count_by_date('commits'))
        return pd.read_sql(commitsSQL, self.db, params={"repoid": str(repoid)})

    def forks(self, repoid):
        """
        Timeseries of when a repo's forks were created
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with forks/day
        """
        forksSQL = s.sql.text(self.__single_table_count_by_date('projects', 'forked_from'))
        return pd.read_sql(forksSQL, self.db, params={"repoid": str(repoid)}).drop(0)

    def issues(self, repoid):
        """
        Timeseries of when people starred a repo
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with issues/day
        """
        issuesSQL = s.sql.text(self.__single_table_count_by_date('issues', 'repo_id'))
        return pd.read_sql(issuesSQL, self.db, params={"repoid": str(repoid)})

    def issues_with_close(self, repoid):
        """
        How long on average each week it takes to close an issue
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with issues/day
        """
        issuesSQL = s.sql.text("""
            SELECT issues.id as "id",
                   issues.created_at as "date",
                   DATEDIFF(closed.created_at, issues.created_at)  AS "days_to_close"
            FROM issues
           JOIN
                (SELECT * FROM issue_events
                 WHERE issue_events.action = "closed") closed
            ON issues.id = closed.issue_id
            WHERE issues.repo_id = :repoid""")
        return pd.read_sql(issuesSQL, self.db, params={"repoid": str(repoid)})

    def pulls(self, repoid):
        """
        Timeseries of pull requests creation, also gives their associated activity
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with pull requests by day
        """
        pullsSQL = s.sql.text("""
            SELECT date(pull_request_history.created_at) AS "date",
            (COUNT(pull_requests.id)) AS "pull_requests",
            (SELECT COUNT(*) FROM pull_request_comments
            WHERE pull_request_comments.pull_request_id = pull_request_history.pull_request_id) AS "comments"
            FROM pull_request_history
            INNER JOIN pull_requests
            ON pull_request_history.pull_request_id = pull_requests.id
            WHERE pull_requests.head_repo_id = :repoid
            AND pull_request_history.action = "merged"
            GROUP BY WEEK(pull_request_history.created_at)
        """)
        return pd.read_sql(pullsSQL, self.db, params={"repoid": str(repoid)})

    def contributors(self, repoid):
        """
        All the contributors to a project and the counts of their contributions
        :param repoid: The id of the project in the projects table. Use repoid() to get this.
        :return: DataFrame with users id, users login, and their contributions by type
        """
        contributorsSQL = s.sql.text("""
            SELECT * FROM
               (
               SELECT   users.id        as "user_id",
                        users.login     as "login",
                        users.location  as "location",
                        com.count       as "commits",
                        pulls.count     as "pull_requests",
                        iss.count       as "issues",
                        comcoms.count   as "commit_comments",
                        pullscoms.count as "pull_request_comments",
                        isscoms.count   as "issue_comments",
                        com.count + pulls.count + iss.count + comcoms.count + pullscoms.count + isscoms.count as "total"
               FROM users
               LEFT JOIN (SELECT committer_id AS id, COUNT(*) AS count FROM commits INNER JOIN project_commits ON project_commits.commit_id = commits.id WHERE project_commits.project_id = :repoid GROUP BY commits.committer_id) AS com
               ON com.id = users.id
               LEFT JOIN (SELECT pull_request_history.actor_id AS id, COUNT(*) AS count FROM pull_request_history JOIN pull_requests ON pull_requests.id = pull_request_history.pull_request_id WHERE pull_requests.base_repo_id = :repoid AND pull_request_history.action = 'merged' GROUP BY pull_request_history.actor_id) AS pulls
               ON pulls.id = users.id
               LEFT JOIN (SELECT reporter_id AS id, COUNT(*) AS count FROM issues WHERE issues.repo_id = :repoid GROUP BY issues.reporter_id) AS iss
               ON iss.id = users.id
               LEFT JOIN (SELECT commit_comments.user_id AS id, COUNT(*) AS count FROM commit_comments JOIN project_commits ON project_commits.commit_id = commit_comments.commit_id WHERE project_commits.project_id = :repoid GROUP BY commit_comments.user_id) AS comcoms
               ON comcoms.id = users.id
               LEFT JOIN (SELECT pull_request_comments.user_id AS id, COUNT(*) AS count FROM pull_request_comments JOIN pull_requests ON pull_request_comments.pull_request_id = pull_requests.id WHERE pull_requests.base_repo_id = :repoid GROUP BY pull_request_comments.user_id) AS pullscoms
               ON pullscoms.id = users.id
               LEFT JOIN (SELECT issue_comments.user_id AS id, COUNT(*) AS count FROM issue_comments JOIN issues ON issue_comments.issue_id = issues.id WHERE issues.repo_id = :repoid GROUP BY issue_comments.user_id) AS isscoms
               ON isscoms.id = users.id
               GROUP BY users.id
               ORDER BY com.count DESC
               ) user_activity
            WHERE commits IS NOT NULL
            OR    pull_requests IS NOT NULL
            OR    issues IS NOT NULL
            OR    commit_comments IS NOT NULL
            OR    pull_request_comments IS NOT NULL
            OR    issue_comments IS NOT NULL;
        """)
        return pd.read_sql(contributorsSQL, self.db, index_col=['user_id'], params={"repoid": str(repoid)})

    def contributions(self, repoid, userid=None):
        """
        Timeseries of all the contributions to a project, optionally limited to a specific user
        :param repoid: The id of the project in the projects table.
        :param userid: The id of user if you want to limit the contributions to a specific user.
        :return: DataFrame with all of the contributions seperated by day.
        """
        rawContributionsSQL = """
            SELECT  DATE(coms.created_at) as "date",
                    coms.count            as "commits",
                    pulls.count           as "pull_requests",
                    iss.count             as "issues",
                    comcoms.count         as "commit_comments",
                    pullscoms.count       as "pull_request_comments",
                    isscoms.count         as "issue_comments",
                    coms.count + pulls.count + iss.count + comcoms.count + pullscoms.count + isscoms.count as "total"
            FROM (SELECT created_at AS created_at, COUNT(*) AS count FROM commits INNER JOIN project_commits ON project_commits.commit_id = commits.id WHERE project_commits.project_id = :repoid[[ AND commits.author_id = :userid]] GROUP BY DATE(created_at)) coms
            LEFT JOIN (SELECT pull_request_history.created_at AS created_at, COUNT(*) AS count FROM pull_request_history JOIN pull_requests ON pull_requests.id = pull_request_history.pull_request_id WHERE pull_requests.base_repo_id = :repoid AND pull_request_history.action = 'merged'[[ AND pull_request_history.actor_id = :userid]] GROUP BY DATE(created_at)) AS pulls
            ON DATE(pulls.created_at) = DATE(coms.created_at)
            LEFT JOIN (SELECT issues.created_at AS created_at, COUNT(*) AS count FROM issues WHERE issues.repo_id = :repoid[[ AND issues.reporter_id = :userid]] GROUP BY DATE(created_at)) AS iss
            ON DATE(iss.created_at) = DATE(coms.created_at)
            LEFT JOIN (SELECT commit_comments.created_at AS created_at, COUNT(*) AS count FROM commit_comments JOIN project_commits ON project_commits.commit_id = commit_comments.commit_id WHERE project_commits.project_id = :repoid[[ AND commit_comments.user_id = :userid]] GROUP BY DATE(commit_comments.created_at)) AS comcoms
            ON DATE(comcoms.created_at) = DATE(coms.created_at)
            LEFT JOIN (SELECT pull_request_comments.created_at AS created_at, COUNT(*) AS count FROM pull_request_comments JOIN pull_requests ON pull_request_comments.pull_request_id = pull_requests.id WHERE pull_requests.base_repo_id = :repoid[[ AND pull_request_comments.user_id = :userid]] GROUP BY DATE(pull_request_comments.created_at)) AS pullscoms
            ON DATE(pullscoms.created_at) = DATE(coms.created_at)
            LEFT JOIN (SELECT issue_comments.created_at AS created_at, COUNT(*) AS count FROM issue_comments JOIN issues ON issue_comments.issue_id = issues.id WHERE issues.repo_id = :repoid[[ AND issue_comments.user_id = :userid]] GROUP BY DATE(issue_comments.created_at)) AS isscoms
            ON DATE(isscoms.created_at) = DATE(coms.created_at)
            ORDER BY DATE(coms.created_at)
        """

        if (userid is not None and len(userid) > 0):
            rawContributionsSQL = rawContributionsSQL.replace('[[', '')
            rawContributionsSQL = rawContributionsSQL.replace(']]', '')
            parameterized = s.sql.text(rawContributionsSQL)
            return pd.read_sql(parameterized, self.db, params={"repoid": str(repoid), "userid": str(userid)})
        else:
            rawContributionsSQL = re.sub(r'\[\[.+?\]\]', '', rawContributionsSQL)
            parameterized = s.sql.text(rawContributionsSQL)
            return pd.read_sql(parameterized, self.db, params={"repoid": str(repoid)})

    def committer_locations(self, repoid):
        """
        Return committers and their locations
        @todo: Group by country code instead of users, needs the new schema
        :param repoid: The id of the project in the projects table.
        :return: DataFrame with users and locations sorted by commtis
        """
        rawContributionsSQL = s.sql.text("""
            SELECT users.login, users.location, COUNT(*) AS "commits"
            FROM commits
            JOIN project_commits
            ON commits.id = project_commits.commit_id
            JOIN users
            ON users.id = commits.author_id
            WHERE project_commits.project_id = :repoid
            AND LENGTH(users.location) > 1
            GROUP BY users.id
            ORDER BY commits DESC
        """)
        return pd.read_sql(rawContributionsSQL, self.db, params={"repoid": str(repoid)})

    def issue_response_time(self, repoid):
        """
        How long it takes for issues to be responded to by people who have commits associate with the project
        :param repoid: The id of the project in the projects table.
        :return: DataFrame with the issues' id the date it was
                 opened, and the date it was first responded to
        """
        issuesSQL = s.sql.text("""
            SELECT issues.created_at               AS "created_at",
                   MIN(issue_comments.created_at)  AS "responded_at"
            FROM issues
            JOIN issue_comments
            ON issue_comments.issue_id = issues.id
            WHERE issue_comments.user_id IN
                (SELECT users.id
                FROM users
                JOIN commits
                WHERE commits.author_id = users.id
                AND commits.project_id = :repoid)
            AND issues.repo_id = :repoid
            GROUP BY issues.id
        """)
        return pd.read_sql(issuesSQL, self.db, params={"repoid": str(repoid)})

    def pull_acceptance_rate(self, repoid):
        """
        Timeseries of pull request acceptance rate (Number of pull requests merged on a date over Number of pull requests opened on a date)
        :param repoid: The id of the project in the projects table.
        :return: DataFrame with the pull acceptance rate and the dates
        """

        pullAcceptanceSQL = s.sql.text("""
        SELECT DATE(date_created) AS "date", CAST(num_approved AS DECIMAL)/CAST(num_open AS DECIMAL) AS "rate"
        FROM
            (SELECT COUNT(DISTINCT pull_request_id) AS num_approved, DATE(pull_request_history.created_at) AS accepted_on
            FROM pull_request_history
            JOIN pull_requests ON pull_request_history.pull_request_id = pull_requests.id
            WHERE action = 'merged' AND pull_requests.base_repo_id = :repoid
            GROUP BY accepted_on) accepted
        JOIN
            (SELECT count(distinct pull_request_id) AS num_open, DATE(pull_request_history.created_at) AS date_created
            FROM pull_request_history
            JOIN pull_requests ON pull_request_history.pull_request_id = pull_requests.id
            WHERE action = 'opened'
            AND pull_requests.base_repo_id = :repoid
            GROUP BY date_created) opened
        ON opened.date_created = accepted.accepted_on
        """)

        return pd.read_sql(pullAcceptanceSQL, self.db, params={"repoid": str(repoid)})

    # Zandria's metrics dist_work and reopened_issues
    def dist_work(self, repoid):
        distWorkSQL = s.sql.text("""
        SELECT avg(num_users) AS "average_num_users", project_name AS "project name", url, numcommits AS "commits"
        FROM
    	    (SELECT projects.id as project_id, projects.name as project_name,
    		projects.url as url, commits.id as commit_id, count(commits.id) as numcommits,
    		count(users.id) as num_users
    		FROM commits
    		join project_commits on commits.id = project_commits.project_id
    		join projects on projects.id = project_commits.project_id
    		join users on commits.author_id = users.id
    	    group by projects.id, commits.author_id
    	    ) as user_count
        GROUP BY project_id
        """)

        return pd.read_sql(distWorkSQL, self.db, params={"repoid": str(repoid)})

    def reopened_issues(self, repoid):
        reOpenedIssuesSQL = s.sql.text("""
        SELECT date(issue_events.created_at) AS "date", issue_events.issue_id AS "reopenedissues", action AS "action"
        FROM issue_events
        WHERE issue_events.action= "reopened"
	GROUP BY MONTH(date)
        """)

        return pd.read_sql(reOpenedIssuesSQL, self.db, params={"repoid": str(repoid)})

    def community_activity(self, repoid):
        """
            Tallies up different forms of participation or engagement
        """

        communityActivitySQL = s.sql.text("""
        SELECT project_commits.project_id as project_id, commits.author_id
        as author_id, count(project_commits.commit_id) as num_commits
	    from commits
        join project_commits on commits.id = project_commits.commit_id
        join projects on projects.id = project_commits.project_id
        group by project_id, author_id
        """)

        return pd.read_sql(communityActivitySQL, self.db, params={"repoid": str(repoid)})

    def Contributor_Breadth(self, repoid):
        """
        Determines Number of Non-Project Member commits
        """
        contributorBreadthSQL = s.sql.text("""
	SELECT count(commits.id) as num_commits, projects.name as project_name, projects.url as url
	from
	commits
	join projects on commits.project_id = projects.id
	join users on users.id = commits.author_id
	where (projects.id, users.id) not in
	(select repo_id, user_id from project_members)
	group by projects.id
	""")
        return pd.read_sql(contributerBreadthSQL, self.db, params={"repoid": str(repoid)})

    # Adam's Metric for SPRINT 2
    def contributor_diversity(self, repoid):
        contributorDiversitySQL = s.sql.text("""
        SELECT count(distinct org_id) as num_organizations, projects.name as project_name, url
        From
	    organization_members
        join users on organization_members.user_id = users.id
        join pull_request_history on pull_request_history.actor_id = users.id
        join pull_requests on pull_request_history.pull_request_id = pull_requests.id
        join projects on pull_requests.base_repo_id = projects.id
        where pull_request_history.action = 'opened'
        group by projects.id
        """)
        return pd.read_sql(contributorDiversitySQL, self.db, params={"repoid": str(repoid)})

    # Jack's Metric for Sprint 2
    def contribution_acceptance(self, repoid):
        contributionAcceptanceSQL = s.sql.text("""
        SELECT projects.name AS project_name, DATE(date_created), CAST(num_approved AS DECIMAL)/CAST(num_open AS DECIMAL) AS approved_over_opened
        FROM (SELECT COUNT(DISTINCT pull_request_id) AS num_approved, projects.name AS project_name, DATE(pull_request_history.created_at) AS accepted_on
            FROM pull_request_history
                JOIN pull_requests ON pull_request_history.pull_request_id = pull_request_id
                JOIN projects ON pull_requests.base_repo_id = projects.id
            WHERE action = 'merged'
            GROUP BY projects.id, accepted_on) accepted
        JOIN (SELECT COUNT(distinct pull_request_id) AS num_open, projects.id AS repo_id, DATE(pull_request_history.created_at) AS date_created
            FROM pull_request_history
                JOIN pull_requests ON pull_request_history.pull_request_id = pull_requests.id
                JOIN projects ON pull_requests.base_repo_id = projects.id
                WHERE pull_request_id IN
                (SELECT pull_request_id FROM pull_request_history WHERE action = 'opened')
                    GROUP BY projects.id, date_created) opened ON opened.date_created = accepted.accepted_on
           JOIN projects ON repo_id = projects.id
        """)
        return pd.read_sql(contributionAcceptanceSQL, self.db, params={"repoid": str(repoid)})

    def bus_factor(self, repoid):
        busFactorSQL = s.sql.text("""
            
        """)
        return pd.read_sql(busFactorSQL, self.db, params={"repoid": str(repoid)})
