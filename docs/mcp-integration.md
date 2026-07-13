# MCP Integration

FlowPilot uses MCP-style tool clients behind local ports and a registry. The goal is to keep node handlers independent from a specific transport while making mock/real/unavailable modes explicit.

## Registry

`app/mcp/registry.py` is the single mode-selection point for tool clients.

Supported client names:

- `github`
- `filesystem`
- `openai_mcp`

## Client Modes

### GitHub

Default:

```text
GITHUB_MCP_MODE=mock
```

Mock mode supports:

- realistic repository snapshots
- deterministic mock issue creation
- idempotency by issue title/run/node key
- explicit `mode: "mock"` and `mock: true` outputs

Real public GitHub reads use the built-in REST adapter when no MCP server URL is supplied:

```text
GITHUB_MCP_MODE=real
GITHUB_MCP_SERVER_URL=
GITHUB_TOKEN=        # optional for public reads, required for writes
```

The REST adapter validates GitHub URLs, reads metadata, README, and the recursive file tree, maps authentication/rate-limit/not-found failures to controlled errors, and supports missing READMEs. If `GITHUB_MCP_SERVER_URL` is set, the registry uses the external JSON-RPC MCP adapter instead.

Real issue creation always remains behind `human_approval`, requires `GITHUB_TOKEN`, embeds an idempotency marker, reuses an existing matching issue, and returns the real issue URL. Only test this against a safe repository you own.

### Filesystem

Default:

```text
FILESYSTEM_MCP_MODE=mock
```

Real mode should be scoped:

```text
FILESYSTEM_MCP_MODE=real
FILESYSTEM_MCP_ROOT=/workspace
```

### OpenAI MCP

When `OPENAI_MCP_SERVER_URL` is unset, the OpenAI MCP client starts in explicit unavailable mode. It does not silently fake tool results.

Real mode requires:

```text
OPENAI_MCP_SERVER_URL=...
OPENAI_API_KEY=...
```

## Health Labels

Health responses expose user-facing mode labels:

- `Mock MCP`
- `Real MCP`
- `OpenAI not configured`
- `Fake agent mode`
- `Memory mode`

The UI uses `blocking` flags to avoid showing non-blocking demo configuration as a fatal error.

## Testing

MCP tests verify:

- GitHub mock snapshot behavior
- GitHub mock issue idempotency
- built-in GitHub REST URL parsing, snapshot contract, missing README, auth/rate-limit handling, token requirements, and write idempotency
- filesystem mock reads
- OpenAI MCP unavailable mode
- handshake and tool listing against a local fake MCP server
- registry mode selection
- client port compatibility

No test requires a real external MCP server.

## Limitations

- The project does not ship a production MCP deployment.
- Built-in real GitHub reads do not require an MCP server; authenticated writes require a token.
- Real OpenAI MCP use still needs credentials and an MCP server URL.
- Default demo behavior is mock/unavailable by design.
