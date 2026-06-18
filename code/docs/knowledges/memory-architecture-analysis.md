# Memory Architecture Analysis for Privacy Router

> Research conducted 2026-06-08. Sources: Strands Agents SDK (GitHub), MCP specification (modelcontextprotocol.io), MCP Memory Server (official), LangGraph memory concepts, Anthropic agent building guidance, Wikipedia blackboard pattern.

---

## 1. Strands Agents Framework Memory

**What it does:** Model-driven SDK (Python/TypeScript) for building AI agents. Lightweight agent loop with native MCP support, multi-provider LLM integration, and `@tool` decorators. Core loop is intentionally stateless.

**Session persistence:** No built-in session manager. Three patterns available:
- Custom history management (external DB/file)
- Model context window as implicit memory (200K+ token contexts)
- Custom state objects wrapping agent with session store

Developer controls all persistence — no accidental retention in the framework.

**MCP integration:** First-class via `MCPClient` wrapper. MCP tools treated identically to `@tool` decorators. Supports stdio and SSE transports. Lifecycle managed via context managers.

| Aspect | Assessment |
|--------|-----------|
| Privacy safety | High — no telemetry, no built-in data retention |
| Session support | None — must build from scratch |
| MCP fit | Excellent — `process()` tool integrates naturally |
| Complexity | Low — library, not framework |

**Pros for Privacy Router:**
- Stateless core = no accidental data retention in framework
- MCP tools integrate naturally
- Developer controls all persistence — can enforce privacy at storage layer
- No telemetry or data phoning home

**Cons for Privacy Router:**
- No session memory out-of-box — must build own
- Context-window-as-memory sends all history to LLM — privacy risk
- No masking contract propagation across turns
- MCP stdio servers run in-process — malicious tool could access agent state

---

## 2. MCP Server Memory Implementation (Official Memory Server)

**What it does:** Knowledge graph pattern with three primitives: entities (nodes), relations (directed edges), observations (atomic facts). JSONL persistence. Eight mutation tools (`create_entities`, `create_relations`, `add_observations`, `delete_entities`, `delete_observations`, `delete_relations`, `read_graph`, `search_nodes`).

**Session persistence:** JSONL file on disk (configurable `MEMORY_FILE_PATH`). Mutations are idempotent (deduplication built in). Entity deletion cascades to relations. No TTL or session scoping — flat knowledge graph.

**MCP integration:** Standard tool-based pattern. LLM decides when to call memory tools (model-controlled). Supports `readOnlyHint` and `destructiveHint` behavioral annotations.

| Aspect | Assessment |
|--------|-----------|
| Privacy safety | Low — LLM-controlled writes could store raw PII |
| Session support | None — flat graph, no scoping |
| MCP fit | Good — tool-based memory aligns with MCP pattern |
| Complexity | Medium — knowledge graph for simple KV needs |

**Pros for Privacy Router:**
- Tool-based memory aligns with MCP `process()` tool
- Deduplication prevents duplicate masking entries
- JSONL is auditable
- Entity/relation model could represent masking contracts

**Cons for Privacy Router:**
- Knowledge graph overkill for masking contract persistence
- No session scoping — cross-session leakage risk
- LLM-controlled memory = privacy risk (model decides what to remember)
- No encryption or access control
- No TTL/expiration for sensitive data

---

## 3. Agent Session Memory Architecture Patterns

### LangGraph Model

**What it does:** Splits memory into two scopes:
- **Short-term (thread-scoped):** Conversation-local, checkpointed per thread ID
- **Long-term (namespace-scoped):** Cross-session, shared per user/org

Three memory types from cognitive science:
- **Semantic** (facts) — profile (single doc) or collection (many small docs)
- **Episodic** (experiences) — few-shot examples
- **Procedural** (instructions) — system prompt, reflection-derived rules

**Session persistence:** Checkpointer pattern — graph state persisted at each step. Store pattern uses `(namespace, key)` tuples with semantic search.

| Aspect | Assessment |
|--------|-----------|
| Privacy safety | High — thread isolation, namespace scoping |
| Session support | Excellent — built-in checkpointing |
| MCP fit | Indirect — patterns map to MCP resources/tools |
| Complexity | High — adds LangGraph dependency |

**Pros:**
- Thread-scoped isolation prevents cross-conversation leakage
- Collection-based semantic memory has lower cross-contamination than monolithic profiles
- Background memory writing avoids latency impact
- Namespace isolation enforces per-user boundaries architecturally

**Cons:**
- Adds framework dependency (LangGraph/LangChain)
- Checkpointer checkpoints everything — needs filtering for sensitive spans
- Over-engineered for single `process()` tool scenario

### Anthropic's Guidance

**Core principle:** "Simple, composable patterns over complex frameworks."

Key findings:
- Tool definition is more critical than prompt optimization (SWE-bench data)
- Avoid over-abstraction — frameworks hide prompts, making debugging harder
- Validate behavior empirically rather than assuming framework behavior
- Augmented LLM = base unit with retrieval + tools + memory

---

## 4. Blackboard Pattern

**What it does:** Architectural pattern where specialist agents coordinate via a central shared workspace. Each specialist watches for matching conditions, contributes partial solutions. Solution emerges from combined contributions.

**Components:**
1. **Blackboard** — central data structure (shared workspace)
2. **Knowledge Sources** — specialist modules triggered by constraints
3. **Control Mechanism** — decides which agents to trigger

**Session persistence:** Blackboard IS the session state. Persists for problem-solving session duration. No built-in cross-session persistence.

| Aspect | Assessment |
|--------|-----------|
| Privacy safety | High — specialists isolated, controlled message passing |
| Session support | Inherent — board = session state |
| MCP fit | Indirect — MCP tools as specialists, resources as board |
| Complexity | Medium-High — coordination overhead |

**Pros for Privacy Router:**
- Natural fit — Extractor, Judge, Router, Masker are already isolated specialists
- Each specialist sees only input + board state — privacy by architecture
- Existing Extract→Judge→Mask flow is already a sequential blackboard

**Cons for Privacy Router:**
- Adds coordination overhead for linear pipeline
- Over-engineered for single-agent scenarios
- Assumes concurrent specialists — Privacy Router runs sequentially
- No built-in persistence model

---

## 5. Current State Assessment

Existing `agents/memory/session.py` issues:

| Issue | Severity | Detail |
|-------|----------|--------|
| Stores raw user text | **Critical** | `entry.text` contains original unmasked sensitive data |
| Stores detected spans | **Critical** | `r.get('span')` holds actual PII values |
| In-memory only | High | No persistence across process restarts |
| Not integrated | Medium | `get_memory()` never called from `server/` or `agents/router/` |
| No MaskingContract storage | High | Doesn't track placeholder↔original mappings across turns |

The `get_context()` method formats entries including raw spans into a context string — would be passed to the LLM, violating the privacy guarantee.

---

## 6. Recommended Architecture: Scoped Contract Store

Combine best elements from each pattern:

### 6.1 Privacy-Safe Session Entry

```python
@dataclass
class SessionEntry:
    """Privacy-safe session entry — no raw text or spans stored."""
    input_hash: str          # SHA-256 of original text (16-char prefix)
    categories: list[str]    # ["RESIDENT_REGISTRATION_NUMBER", "MOBILE_PHONE"]
    placeholder_map: dict[str, str]  # {"[RESIDENT_REGISTRATION_NUMBER#1]": hash(original)}
    policy_action: str       # "mask_and_send", "allow", "process_locally"
    timestamp: float
```

Key insight: store **placeholder→hash mappings**, not placeholder→original. MaskingContract (real values) lives only in-process memory for single `process()` call duration.

### 6.2 Deterministic Placeholder IDs

For multi-turn consistency:
```
placeholder_id = f"[{category}#{hash(original_value) % 10000}]"
```

Store mapping in session so subsequent turns reuse same ID. MaskingContract for hydration rebuilt from session's placeholder→hash table + current turn's detected spans.

### 6.3 Implementation Layers

```
┌─ MCP Layer (server/mcp/)
│  └─ process(text, action, model, session_id?)
│     └─ Injects session context into pipeline
│
├─ Memory Layer (agents/memory/)
│  ├─ ContractStore: namespace-scoped, privacy-safe entries
│  ├─ Backend: SQLite (demo) → PostgreSQL (production)
│  └─ TTL: configurable per-session expiration
│
└─ Pipeline Layer (agents/router/)
   ├─ Extractor → detects PII
   ├─ Session lookup → checks for prior mappings
   ├─ Masker → uses session-consistent placeholder IDs
   └─ Hydrator → reconstructs from current contract only
```

### 6.4 Privacy Guarantees

| What | Stored? | Where | Retention |
|------|---------|-------|-----------|
| Original text | **Never** | N/A | N/A |
| Detected spans | **Never persisted** | In-process only | Single `process()` call |
| Placeholder→hash map | Yes | SQLite/PostgreSQL | Session lifetime + TTL |
| Policy decisions | Yes | SQLite/PostgreSQL | Audit log (indefinite) |
| MaskingContract (real values) | **Never persisted** | In-process only | Single `process()` call |

### 6.5 Concrete Next Steps

1. **Replace** `SessionEntry.text` with `input_hash` — never store raw text
2. **Replace** `SessionEntry.records` with `categories` + `placeholder_map` (values are hashes)
3. **Add** `session_id` parameter to `process()` MCP tool
4. **Add** SQLite-backed persistence (swap `defaultdict(deque)` for SQLite)
5. **Add** deterministic placeholder ID generation for cross-turn consistency
6. **Wire** `ContractStore` into Router pipeline between Extractor and Masker

### 6.6 Anti-Patterns to Avoid

| Anti-Pattern | Why |
|--------------|-----|
| Knowledge graph for masking contracts | Overkill, privacy risk from LLM-controlled writes |
| Full LangGraph dependency | Heavy framework for a linear pipeline |
| Blackboard with concurrent specialists | Sequential pipeline doesn't need coordination overhead |
| Storing raw text or spans in any persistent layer | Violates core privacy guarantee |
| LLM-controlled memory writes | Model decides what to remember = privacy footgun |
| Context-window-as-memory | All history sent to LLM, including previously masked data |

---

## 7. Decision Matrix

| Pattern | Privacy | Session Support | MCP Fit | Complexity | Verdict |
|---------|---------|-----------------|---------|------------|---------|
| Strands native | ✅ High | ❌ None | ✅ Excellent | Low | Use as host framework |
| MCP Memory Server | ⚠️ Low | ❌ None | ✅ Good | Medium | Don't adopt as-is |
| LangGraph memory | ✅ High | ✅ Excellent | ⚠️ Indirect | High | Over-engineered |
| Blackboard | ✅ High | ✅ Inherent | ⚠️ Indirect | Medium-High | Borrow isolation concept |
| **Scoped Contract Store** | ✅ High | ✅ Built | ✅ Native | Low | **Recommended** |

---

*Last updated: 2026-06-08*
