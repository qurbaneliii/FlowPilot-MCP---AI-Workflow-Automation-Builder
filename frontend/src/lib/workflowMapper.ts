import type { Edge, Node } from "reactflow";
import type {
  GitHubAudit,
  AuditFinding,
  IssueDraft,
  LinkedInDraft,
  RiskFlag
} from "@/types/artifact";
import type { Run, RunNode } from "@/types/run";
import type {
  BackendNodeDisplay,
  GeneratedWorkflow,
  WorkflowGraph,
  WorkflowNode,
  WorkflowSummary
} from "@/types/workflow";
import { summarizeUnknown, titleCase } from "./formatters";

export interface FlowNodeData {
  workflowNode: WorkflowNode;
  runNode?: RunNode;
  display?: BackendNodeDisplay;
  status: string;
  outputSummary: string;
}

export function getWorkflowSummary(
  graph?: WorkflowGraph | null,
  workflow?: GeneratedWorkflow | null
): WorkflowSummary {
  if (workflow?.summary) {
    return {
      name: workflow.summary.name,
      description: workflow.summary.description,
      nodeCount: workflow.summary.node_count,
      riskyActionCount: workflow.summary.risky_action_count,
      approvalRequired: workflow.summary.approval_required,
      estimatedStages: workflow.summary.estimated_stages,
      repoUrl: workflow.summary.repo_url,
      mode: workflow.summary.mode,
      statusLabel: workflow.summary.status_label
    };
  }
  const nodes = graph?.nodes ?? [];
  const approvalRequired = nodes.some((node) => node.type === "human_approval");
  const riskyActionCount = nodes.filter((node) =>
    ["github_issue_creator", "filesystem_writer", "deployment"].some((type) =>
      node.type.includes(type)
    )
  ).length;
  return {
    name: nodes.length ? "GitHub Repository Audit" : "No workflow generated",
    description: nodes.length
      ? "Audit a repository, draft guarded GitHub issues, and produce demo-ready artifacts."
      : "Generate a workflow to see the executable graph.",
    nodeCount: nodes.length,
    riskyActionCount,
    approvalRequired,
    estimatedStages: calculateDepth(nodes)
  };
}

export function mapWorkflowToReactFlow(
  graph?: WorkflowGraph | null,
  run?: Run | null,
  workflow?: GeneratedWorkflow | null
): { nodes: Node<FlowNodeData>[]; edges: Edge[] } {
  const workflowNodes = graph?.nodes ?? [];
  const runNodes = new Map((run?.nodes ?? []).map((node) => [node.node_id, node]));
  const displayById = new Map(
    (workflow?.node_display ?? []).map((node) => [node.id, node])
  );
  const depthMap = getDepthMap(workflowNodes);
  const columns = new Map<number, WorkflowNode[]>();
  workflowNodes.forEach((node) => {
    const depth = depthMap.get(node.id) ?? 0;
    columns.set(depth, [...(columns.get(depth) ?? []), node]);
  });
  const nodes: Node<FlowNodeData>[] = workflowNodes.map((node) => {
    const depth = depthMap.get(node.id) ?? 0;
    const siblings = columns.get(depth) ?? [node];
    const siblingIndex = siblings.findIndex((sibling) => sibling.id === node.id);
    const centeredOffset = siblingIndex - (siblings.length - 1) / 2;
    const runNode = runNodes.get(node.id);
    const display = displayById.get(node.id);
    return {
      id: node.id,
      type: "flowpilotNode",
      position: {
        x: centeredOffset * 360,
        y: depth * 172
      },
      data: {
        workflowNode: node,
        runNode,
        display,
        status: runNode?.status ?? "pending",
        outputSummary:
          runNode?.display?.summary ??
          runNode?.output_summary?.summary ??
          summarizeUnknown(runNode?.output)
      }
    };
  });
  const edges: Edge[] = workflowNodes.flatMap((node) =>
    node.dependencies.map((dependency) => ({
      id: `${dependency}-${node.id}`,
      source: dependency,
      target: node.id,
      animated: runNodes.get(node.id)?.status === "running",
      className: "flowpilot-edge",
      type: "smoothstep",
      style: { strokeWidth: 1.6 }
    }))
  );
  return { nodes, edges };
}

export function getNodeOrder(graph?: WorkflowGraph | null): string[] {
  const nodes = graph?.nodes ?? [];
  const ordered: string[] = [];
  const visited = new Set<string>();
  const byId = new Map(nodes.map((node) => [node.id, node]));
  function visit(node: WorkflowNode) {
    if (visited.has(node.id)) return;
    node.dependencies.forEach((id) => {
      const dependency = byId.get(id);
      if (dependency) visit(dependency);
    });
    visited.add(node.id);
    ordered.push(node.id);
  }
  nodes.forEach(visit);
  return ordered;
}

export function extractAudit(run?: Run | null): GitHubAudit | null {
  const output = findNodeOutput(run, "ai_repo_analyzer");
  if (!output) return null;
  const analysis = asRecord(output.analysis) ?? output;
  const findings = Array.isArray(analysis.findings) ? analysis.findings : [];
  const riskFlags = Array.isArray(analysis.risk_flags) ? analysis.risk_flags : [];
  return {
    summary:
      typeof analysis.summary === "string"
        ? analysis.summary
        : "Repository audit completed.",
    findings: findings.map(normalizeFinding),
    risk_flags: riskFlags.map(normalizeRiskFlag)
  };
}

export function extractIssueDrafts(run?: Run | null): IssueDraft[] {
  const approvalDrafts = run?.pending_approval?.issue_drafts;
  if (approvalDrafts?.length) return approvalDrafts.map(normalizeIssueDraft);
  const output = findNodeOutput(run, "issue_draft_generator");
  const candidates = output?.issue_drafts ?? output?.issues;
  return Array.isArray(candidates) ? candidates.map(normalizeIssueDraft) : [];
}

export function extractLinkedInDraft(run?: Run | null): LinkedInDraft | null {
  const output = findNodeOutput(run, "linkedin_draft_generator");
  const draft = asRecord(output?.linkedin_draft) ?? output;
  if (!draft || typeof draft.post_text !== "string") return null;
  return {
    post_text: draft.post_text,
    hashtags: Array.isArray(draft.hashtags)
      ? draft.hashtags.filter((item): item is string => typeof item === "string")
      : [],
    tone: typeof draft.tone === "string" ? draft.tone : "professional"
  };
}

export function findNodeOutput(
  run: Run | null | undefined,
  nodeTypeOrId: string
): Record<string, unknown> | null {
  if (!run) return null;
  const direct = run.node_outputs[nodeTypeOrId];
  if (direct) return direct;
  const node = run.nodes.find((candidate) => candidate.node_id === nodeTypeOrId);
  return node?.output ?? null;
}

export function nodeDisplayName(nodeId: string): string {
  return titleCase(nodeId);
}

function getDepthMap(nodes: WorkflowNode[]): Map<string, number> {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const depthMap = new Map<string, number>();
  function depth(node: WorkflowNode): number {
    const cached = depthMap.get(node.id);
    if (cached !== undefined) return cached;
    if (!node.dependencies.length) {
      depthMap.set(node.id, 0);
      return 0;
    }
    const value =
      1 +
      Math.max(
        ...node.dependencies.map((dependencyId) => {
          const dependency = byId.get(dependencyId);
          return dependency ? depth(dependency) : 0;
        })
      );
    depthMap.set(node.id, value);
    return value;
  }
  nodes.forEach(depth);
  return depthMap;
}

function calculateDepth(nodes: WorkflowNode[]): number {
  if (!nodes.length) return 0;
  const depths = [...getDepthMap(nodes).values()];
  return depths.length ? Math.max(...depths) + 1 : 1;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function normalizeFinding(value: unknown): AuditFinding {
  const record = asRecord(value) ?? {};
  const severity =
    record.severity === "critical" || record.severity === "warning"
      ? record.severity
      : "info";
  return {
    category:
      typeof record.category === "string" ? record.category : "maintainability",
    severity,
    title: typeof record.title === "string" ? record.title : "Untitled finding",
    description:
      typeof record.description === "string"
        ? record.description
        : "No description provided.",
    recommendation:
      typeof record.recommendation === "string"
        ? record.recommendation
        : "Review this finding before taking action.",
    affected_files: Array.isArray(record.affected_files)
      ? record.affected_files.filter(
          (item): item is string => typeof item === "string"
        )
      : [],
    suggested_issue_title:
      typeof record.suggested_issue_title === "string"
        ? record.suggested_issue_title
        : null
  };
}

function normalizeRiskFlag(value: unknown): RiskFlag {
  const record = asRecord(value) ?? {};
  return {
    code: typeof record.code === "string" ? record.code : "RISK_FLAG",
    severity:
      record.severity === "critical" || record.severity === "warning"
        ? record.severity
        : "info",
    description:
      typeof record.description === "string"
        ? record.description
        : "Risk flag requires review."
  };
}

function normalizeIssueDraft(value: unknown): IssueDraft {
  const record = asRecord(value) ?? {};
  return {
    title: typeof record.title === "string" ? record.title : "Untitled issue",
    body: typeof record.body === "string" ? record.body : "",
    labels: Array.isArray(record.labels)
      ? record.labels.filter((item): item is string => typeof item === "string")
      : [],
    priority: typeof record.priority === "string" ? record.priority : "medium",
    acceptance_criteria: Array.isArray(record.acceptance_criteria)
      ? record.acceptance_criteria.filter(
          (item): item is string => typeof item === "string"
        )
      : [],
    created: typeof record.created === "boolean" ? record.created : undefined,
    url: typeof record.url === "string" ? record.url : undefined,
    display_url:
      typeof record.display_url === "string" ? record.display_url : undefined
  };
}
