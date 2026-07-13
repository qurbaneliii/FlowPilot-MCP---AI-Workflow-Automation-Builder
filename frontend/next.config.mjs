/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === "true";
const repositoryName =
  process.env.GITHUB_REPOSITORY?.split("/")[1] ??
  "FlowPilot-MCP--AI-Workflow-Automation-Builder";
const githubPagesBasePath = `/${repositoryName}`;

const nextConfig = {
  reactStrictMode: true,
  ...(isGithubPages
    ? {
        output: "export",
        basePath: githubPagesBasePath,
        assetPrefix: githubPagesBasePath,
        images: {
          unoptimized: true
        },
        trailingSlash: true
      }
    : {}),
  turbopack: {
    root: import.meta.dirname
  }
};

export default nextConfig;
