# GitHub Issue: isGatewayMessageChannel intermittently rejects valid third-party channel plugins

**目标仓库**: openclaw/openclaw
**标题**: isGatewayMessageChannel intermittently rejects valid third-party channel plugins (openclaw-weixin, qqbot)

---

## Bug: `isGatewayMessageChannel` intermittently rejects valid third-party channel plugins

**Version:** OpenClaw 2026.4.2 (d74a122)
**Severity:** High — blocks `sessions_spawn` from third-party channel sessions
**Channels affected:** `openclaw-weixin`, `qqbot` (likely all non-bundled channel plugins)

### Symptoms

When a user sends a message via a third-party channel plugin (e.g. `openclaw-weixin`), `sessions_spawn` intermittently fails with:

```
invalid agent params: unknown channel: openclaw-weixin
```

The error is **intermittent** — it starts occurring without any config change and stops on its own. The failure window can last from minutes to hours.

### Evidence from gateway logs

```
# Successful spawn
00:44:47 ⇄ res ✓ agent 63ms runId=announce:v1:agent:research-searcher:subagent:...

# First failure — 18 seconds later, same gateway process, no config changes
00:45:05 ⇄ res ✗ agent 1ms errorCode=INVALID_REQUEST errorMessage=invalid agent params: unknown channel: openclaw-weixin

# Also affects qqbot
19:02:51 ⇄ res ✗ agent 1ms errorCode=INVALID_REQUEST errorMessage=invalid agent params: unknown channel: qqbot
```

### Root cause analysis

#### The channel validation chain

1. Gateway's `agent` handler validates `request.channel` via `isGatewayMessageChannel()` (`gateway-cli-CWpalJNJ.js`)
2. `isGatewayMessageChannel()` → `listGatewayMessageChannels()` → `listDeliverableMessageChannels()` → `listPluginChannelIds()`
3. `listPluginChannelIds()` → `listRegisteredChannelPluginEntries()` → `getActivePluginRegistry()?.channels`

#### The problem: mutable registry vs pinned registry

The plugin system has a **pinned channel surface** mechanism designed to prevent channel plugins from being evicted:

- `getActivePluginChannelRegistry()` → returns the **pinned** channel registry (stable after startup)
- `getActivePluginRegistry()` → returns the **mutable** `state.activeRegistry` (can be overwritten at runtime)

`listRegisteredChannelPluginEntries()` in `registry-DTO_OK4F.js` uses `getActivePluginRegistry()` **instead of** `getActivePluginChannelRegistry()`. This means channel validation depends on a **mutable global state** that can change during runtime.

#### Why bundled channels always work

Bundled channels (telegram, discord, whatsapp, etc.) are in the hardcoded `CHANNEL_IDS` array. They pass validation via `CHANNEL_IDS.includes(value)` and never hit the plugin registry path.

#### Why third-party channels fail intermittently

Third-party channel plugins are loaded via the plugin system. Their presence in `getActivePluginRegistry()?.channels` depends on the runtime state of `state.activeRegistry`, which is a `Symbol.for("openclaw.pluginRegistryState")` global shared across the entire V8 isolate.

#### Startup pin gap

`loadGatewayStartupPlugins()` calls `prepareGatewayPluginLoad()` **without** `beforePrimeRegistry`, meaning the channel registry is **not pinned** during initial startup:

```javascript
function loadGatewayStartupPlugins(params) {
    return prepareGatewayPluginLoad(params);  // no beforePrimeRegistry!
}

function reloadDeferredGatewayPlugins(params) {
    return prepareGatewayPluginLoad({
        ...params,
        beforePrimeRegistry: pinActivePluginChannelRegistry  // pinned here
    });
}
```

Only `reloadDeferredGatewayPlugins` pins the channel registry.

### Suggested fixes

#### Fix 1: Use pinned channel registry for channel validation (preferred)

In `src/channels/registry.ts`, change `listRegisteredChannelPluginEntries()` to use the pinned channel registry:

```typescript
// Before:
function listRegisteredChannelPluginEntries() {
    return getActivePluginRegistry()?.channels ?? [];
}

// After:
function listRegisteredChannelPluginEntries() {
    return getActivePluginChannelRegistry()?.channels ?? getActivePluginRegistry()?.channels ?? [];
}
```

#### Fix 2: Pin channel registry during initial startup

In the gateway startup code, ensure `loadGatewayStartupPlugins` also pins the channel registry:

```typescript
function loadGatewayStartupPlugins(params) {
    return prepareGatewayPluginLoad({
        ...params,
        beforePrimeRegistry: pinActivePluginChannelRegistry
    });
}
```

Both fixes should be applied together for defense in depth.

### Reproduction

1. Configure a third-party channel plugin (e.g. `openclaw-weixin`)
2. Send a message from that channel to main agent
3. Main agent spawns a subagent (depth 1) — usually succeeds
4. Subagent spawns a child (depth 2+) — intermittently fails with `unknown channel: <plugin-id>`

### Environment

- OS: Ubuntu Linux 6.8.0-101-generic (x64)
- Node: v22.22.2
- OpenClaw: 2026.4.2 (d74a122) via pnpm global install
- Affected plugins: `openclaw-weixin`, `qqbot`
