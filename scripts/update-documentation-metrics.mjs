import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const metricsPath = path.join(repoRoot, "DOCUMENTATION_METRICS.md");

const today = new Date().toISOString().slice(0, 10);

const run = (command, { allowFailure = false } = {}) => {
  try {
    return execSync(command, { encoding: "utf8" }).trim();
  } catch (error) {
    if (allowFailure) {
      return "";
    }
    throw error;
  }
};

const listMarkdownFiles = () => {
  const output = run(
    'rg --files -g "*.md" -g "!node_modules/**" -g "!docs/archive/**" -g "!.git/**"',
  );
  return output ? output.split("\n").filter(Boolean) : [];
};

const getTodoCount = () => {
  const output = run(
    'rg -c "TODO" -g "*.md" -g "!node_modules/**" -g "!docs/archive/**"',
    { allowFailure: true },
  );
  if (!output) {
    return 0;
  }
  return output
    .split("\n")
    .map((line) => Number(line.split(":").pop() ?? 0))
    .reduce((sum, value) => sum + (Number.isNaN(value) ? 0 : value), 0);
};

const getAverageDocAgeDays = (files) => {
  const nowSeconds = Math.floor(Date.now() / 1000);
  const ages = files.map((file) => {
    try {
      const timestamp = Number(run(`git log -1 --format=%ct -- "${file}"`));
      if (!Number.isNaN(timestamp) && timestamp > 0) {
        return (nowSeconds - timestamp) / 86400;
      }
    } catch {
      // Fall through to filesystem timestamp.
    }

    const stats = fs.statSync(path.join(repoRoot, file));
    return (nowSeconds - Math.floor(stats.mtimeMs / 1000)) / 86400;
  });

  if (!ages.length) {
    return "0 days";
  }

  const average = ages.reduce((sum, value) => sum + value, 0) / ages.length;
  return `${average.toFixed(1)} days`;
};

const getGitHubMetrics = async () => {
  const repository = process.env.GITHUB_REPOSITORY;
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!repository || !token) {
    return {};
  }

  const headers = {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
  };

  const monthStart = new Date();
  monthStart.setUTCDate(1);
  monthStart.setUTCHours(0, 0, 0, 0);
  const monthStartIso = monthStart.toISOString();

  const search = async (query) => {
    const url = new URL("https://api.github.com/search/issues");
    url.searchParams.set("q", query);
    url.searchParams.set("per_page", "100");
    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }
    return response.json();
  };

  try {
    const opened = await search(
      `repo:${repository} label:documentation type:issue created:>=${monthStartIso}`,
    );
    const closed = await search(
      `repo:${repository} label:documentation type:issue closed:>=${monthStartIso}`,
    );

    const closedItems = closed.items ?? [];
    const resolutionTimes = closedItems
      .map((issue) => {
        if (!issue.created_at || !issue.closed_at) {
          return null;
        }
        const created = Date.parse(issue.created_at);
        const closedAt = Date.parse(issue.closed_at);
        if (Number.isNaN(created) || Number.isNaN(closedAt)) {
          return null;
        }
        return (closedAt - created) / 86400000;
      })
      .filter((value) => value !== null);

    const averageResolution = resolutionTimes.length
      ? `${(
          resolutionTimes.reduce((sum, value) => sum + value, 0) /
          resolutionTimes.length
        ).toFixed(1)} days`
      : "N/A";

    return {
      "Issues opened": String(opened.total_count ?? 0),
      "Issues closed": String(closed.total_count ?? 0),
      "Average resolution time": averageResolution,
    };
  } catch (error) {
    console.warn(`Unable to fetch GitHub metrics: ${error.message}`);
    return {};
  }
};

const getWorkflowMetrics = async () => {
  const repository = process.env.GITHUB_REPOSITORY;
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!repository || !token) {
    return {};
  }

  const headers = {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
  };

  try {
    const runsUrl = new URL(
      `https://api.github.com/repos/${repository}/actions/workflows/docs-quality.yml/runs`,
    );
    runsUrl.searchParams.set("per_page", "20");
    const runsResponse = await fetch(runsUrl, { headers });
    if (!runsResponse.ok) {
      throw new Error(`Workflow runs fetch failed: ${runsResponse.status}`);
    }

    const runsData = await runsResponse.json();
    const runs = runsData.workflow_runs ?? [];
    const totalRuns = runs.length;
    const successfulRuns = runs.filter(
      (run) => run.conclusion === "success",
    ).length;
    const ciPassRate = totalRuns
      ? `${((successfulRuns / totalRuns) * 100).toFixed(1)}%`
      : "N/A";

    let brokenLinks = "TBD";
    const latestRun = runs[0];
    if (latestRun?.id) {
      const jobsUrl = new URL(
        `https://api.github.com/repos/${repository}/actions/runs/${latestRun.id}/jobs`,
      );
      jobsUrl.searchParams.set("per_page", "100");
      const jobsResponse = await fetch(jobsUrl, { headers });
      if (jobsResponse.ok) {
        const jobsData = await jobsResponse.json();
        const jobs = jobsData.jobs ?? [];
        const linkJob = jobs.find((job) => job.name === "link-check");
        if (linkJob?.conclusion === "success") {
          brokenLinks = "0";
        } else if (linkJob?.conclusion) {
          brokenLinks = "Failing";
        }
      }
    }

    return {
      "CI pass rate": ciPassRate,
      "Broken links": brokenLinks,
    };
  } catch (error) {
    console.warn(`Unable to fetch workflow metrics: ${error.message}`);
    return {};
  }
};

const updateMetricsFile = async () => {
  const files = listMarkdownFiles();
  const metrics = {
    "Active docs": String(files.length),
    "Average doc age": getAverageDocAgeDays(files),
    "TODO count": String(getTodoCount()),
  };

  const githubMetrics = await getGitHubMetrics();
  Object.assign(metrics, githubMetrics);

  const workflowMetrics = await getWorkflowMetrics();
  Object.assign(metrics, workflowMetrics);

  const raw = fs.readFileSync(metricsPath, "utf8");
  const lines = raw.split("\n");

  const updatedLines = lines.map((line) => {
    if (line.startsWith("**Last updated:**")) {
      return `**Last updated:** ${today}`;
    }

    if (!line.startsWith("|")) {
      return line;
    }

    const columns = line.split("|");
    if (columns.length < 6) {
      return line;
    }

    const metricName = columns[1].trim();
    if (!metrics[metricName]) {
      return line;
    }

    columns[4] = ` ${metrics[metricName]} `;
    return columns.join("|");
  });

  fs.writeFileSync(metricsPath, updatedLines.join("\n"));
};

await updateMetricsFile();
