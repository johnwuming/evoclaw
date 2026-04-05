# Bug: `isGatewayMessageChannel` intermittently rejects valid third-party channel plugins

**Version:** OpenClaw 2026.4.2 (d74a122)
**Severity:** High — blocks nested subagent spawns from third-party channel sessions
**Channel affected:** `openclaw-weixin` (likely affects all non-bundled channel plugins)

## Symptoms

When a user sends a message via `openclaw-weixin` (a third-party channel plugin), the main agent can successfully spawn subagents (depth 1). However, when those subagents attempt to spawn their own children (depth 2+), the gateway rejects the request with:

```
invalid agent params: unknown channel: openclaw-weixin
```

The error appears **intermittently** — it starts occurring after the gateway has been running for some time, and stops on its own without restart.

## Evidence from gateway logs

```
# Last successful request with openclaw-weixin channel
00:44:47 ⇄ res ✓ agent 63ms runId=announce:v1:agent:research-searcher:subagent:... conn=f20bdefd…

# First failure — 18 seconds later, same gateway process, no config changes
00:45:05 ⇄ res ✗ agent 1ms errorCode=INVALID_REQUEST errorMessage=invalid agent params: unknown channel: openclaw-weixin conn=c592bb7c…

# Errors continue for ~11 minutes, then stop
00:45:05, 00:45:11, 00:45:49, 00:45:57, 00:46:03, 00:46:23, 00:48:45, 00:55:20, 00:56:20

# After 00:56, requests succeed again (no restart, no config change)
```

## Root cause analysis

### The channel validation chain

1. Gateway's `agent` handler validates `request.channel` via `isGatewayMessageChannel()` (gateway-cli-CWpalJNJ.js:10134)
2. `isGatewayMessageChannel()` → `listGatewayMessageChannels()` → `listDeliverableMessageChannels()` → `listPluginChannelIds()`
3. `listPluginChannelIds()` calls `listRegisteredChannelPluginEntries()` (registry-DTO_OK4F.js:4)
4. `listRegisteredChannelPluginEntries()` reads `getActivePluginRegistry()?.channels` (registry-DTO_OK4F.js:5)

### The problem: `getActivePluginRegistry()` vs `getActivePluginChannelRegistry()`

The plugin registry has a **pinned channel surface** mechanism specifically designed to prevent channel plugins from being evicted:

- `getActivePluginChannelRegistry()` → returns the **pinned** channel registry (stable after startup)
- `getActivePluginRegistry()` → returns the **mutable** `state.activeRegistry` (can be overwritten)

`listRegisteredChannelPluginEntries()` (registry-DTO_OK4F.js:4) uses `getActivePluginRegistry()` instead of `getActivePluginChannelRegistry()`. This means channel validation depends on a **mutable global state** that can change during runtime.

### Why bundled channels always work

Bundled channels (telegram, discord, whatsapp, etc.) are in the hardcoded `CHANNEL_IDS` array (chat-meta-Cdrnv7R-.js:622). They pass validation via `CHANNEL_IDS.includes(value)` and never hit the plugin registry path.

### Why third-party channels fail intermittently

`openclaw-weixin` is loaded via the plugin system. Its presence in `getActivePluginRegistry()?.channels` depends on the runtime state of `state.activeRegistry`, which is a `Symbol.for("openclaw.pluginRegistryState")` global shared across the entire V8 isolate.

### Startup pin gap

Additionally, `loadGatewayStartupPlugins()` (gateway-cli-CWpalJNJ.js:19876) calls `prepareGatewayPluginLoad()` **without** `beforePrimeRegistry`, meaning the channel registry is **not pinned** during initial startup:

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

Only `reloadDeferredGatewayPlugins` pins the channel registry. If `state.activeRegistry` is overwritten after startup (e.g., by `requireActivePluginRegistry()` creating an empty registry, or by config schema resolution triggering a plugin reload), the channel list becomes empty for third-party plugins.

## Reproduction

1. Configure `openclaw-weixin` as a channel plugin
2. Send a message from weixin to main agent
3. Main agent spawns a subagent (depth 1) — succeeds
4. Subagent spawns a child (depth 2+) — intermittently fails with `unknown channel: openclaw-weixin`

## Suggested fixes

### Fix 1: Use pinned channel registry for channel validation (preferred)

In `registry-DTO_OK4F.js`, change `listRegisteredChannelPluginEntries()` to use the pinned channel registry:

```javascript
// Before:
import { r as getActivePluginRegistry } from "./runtime-DZz1f0_h.js";
function listRegisteredChannelPluginEntries() {
    return getActivePluginRegistry()?.channels ?? [];
}

// After:
import { r as getActivePluginRegistry, t as getActivePluginChannelRegistry } from "./runtime-DZz1f0_h.js";
function listRegisteredChannelPluginEntries() {
    return getActivePluginChannelRegistry()?.channels ?? getActivePluginRegistry()?.channels ?? [];
}
```

### Fix 2: Pin channel registry during initial startup

In `gateway-cli-CWpalJNJ.js`, ensure `loadGatewayStartupPlugins` also pins the channel registry:

```javascript
function loadGatewayStartupPlugins(params) {
    return prepareGatewayPluginLoad({
        ...params,
        beforePrimeRegistry: pinActivePluginChannelRegistry
    });
}
```

Both fixes should be applied together for defense in depth.

## Environment

- OS: Ubuntu Linux 6.8.0-101-generic (x64)
- Node: v22.22.2
- Plugin: openclaw-weixin (third-party channel plugin)
- Deployed via: pnpm global install
