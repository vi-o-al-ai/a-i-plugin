# Claude Code plugin packaging format — research notes

Researched 2026-10-01 against the live docs at code.claude.com and the locally installed CLI
(`claude --version` → `2.1.286 (Claude Code)`, binary at `/opt/node22/bin/claude`; `uv 0.8.17`
at `/root/.local/bin/uv`).

Goal: package one Python MCP server (launched with `uv`), several skills and several
slash commands as a single plugin that lives at the **root** of the GitHub repo
`vi-o-al-ai/a-i-plugin`, installable with `/plugin marketplace add vi-o-al-ai/a-i-plugin`.

Legend: **VERIFIED** = quoted from official docs and/or reproduced locally.
**UNVERIFIED** = not found in the docs fetched and not reproduced; treat as a guess.

The docs have been reorganised since older guides: the single `/docs/en/plugins` page is now an
overview that fans out into `/docs/en/plugins/create`, `/plugins/components`,
`/plugins/manifest-reference`, `/plugins/marketplace-reference`, `/plugins/create-marketplace`,
`/plugins/host-marketplace`, `/plugins/publish`, `/plugins/install`, `/plugins/loading`,
`/plugins/cli-reference` and `/plugins/troubleshooting`. `/docs/en/plugins-reference` now redirects
to the manifest reference; `/docs/en/plugin-marketplaces` redirects to "Create a marketplace";
`/docs/en/slash-commands` redirects to the skills page.

---

## TL;DR for this project

| Question | Answer |
| :- | :- |
| Can the repo root be the plugin *and* host its own marketplace? | **Yes (VERIFIED).** Put `plugin.json` and `marketplace.json` side by side in `.claude-plugin/`; the single marketplace entry uses `"source": "./"`. Confirmed by the publish docs and by `claude plugin validate` locally. |
| Install commands for users | `/plugin marketplace add vi-o-al-ai/a-i-plugin` then `/plugin install ableton-live@a-i-plugin` (opens the details pane; pick a scope). One-step: `/plugin install ableton-live --marketplace vi-o-al-ai/a-i-plugin` (v2.1.275+). Shell: `claude plugin marketplace add vi-o-al-ai/a-i-plugin && claude plugin install ableton-live@a-i-plugin`. |
| Updates | `claude plugin update ableton-live@a-i-plugin` (refreshes the marketplace first) or `/plugin marketplace update a-i-plugin`. Auto-update is **off** by default for third-party marketplaces. A `version` in `plugin.json` pins users until you change it. |
| Commands vs skills | Converged. "Custom commands have been merged into skills." `commands/*.md` still works, but docs say "Prefer `skills/` for new plugins". A "slash command" is just a skill with `disable-model-invocation: true`. |
| MCP server config | `.mcp.json` at plugin root, `mcpServers` map, `type: "stdio"`, `command`/`args`/`env`. `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` substitute in `command`, `args`, `env` and are also exported to the server process. No `cwd` field. |
| Tool names | `mcp__plugin_<plugin>_<server>__<tool>` e.g. `mcp__plugin_ableton-live_live__get_status`. Server registers as `plugin:ableton-live:live`. |
| Approval | Plugin MCP servers start automatically when the plugin is enabled; no per-server approval prompt (unlike a project `.mcp.json`). Installing the plugin is the trust step. |
| Where to write history files | **`${CLAUDE_PLUGIN_DATA}`** = `~/.claude/plugins/data/<plugin-id>/` (survives updates; deleted on uninstall unless `--keep-data`). Never write under `${CLAUDE_PLUGIN_ROOT}` (versioned cache dir, orphaned on update). Fall back to XDG when the env var is absent. |
| Python deps | Claude Code auto-installs **only** Node deps (package.json + npm/bun lockfile). "Python dependencies" are explicitly listed as something you must install yourself, ideally into `${CLAUDE_PLUGIN_DATA}` from a hook. `uv run --frozen` handles it lazily; set `UV_PROJECT_ENVIRONMENT=${CLAUDE_PLUGIN_DATA}/venv` so the venv is not created inside the plugin cache. |
| Local dev | `claude --plugin-dir /path/to/repo` (works even with `marketplace.json` present, as long as `plugin.json` is there — VERIFIED locally). Edit, then `/reload-plugins`. `claude plugin validate ./.claude-plugin/plugin.json` checks the manifest **and** `.mcp.json`; `claude plugin validate .` at the repo root only validates the marketplace file. |
| SessionStart hook to point Claude at a journal | Yes. Plain stdout of a `SessionStart` hook is added to Claude's context; the hook process receives `CLAUDE_PLUGIN_DATA`. Phrase it as facts, not system commands. |

---

## 1. `.claude-plugin/plugin.json` — schema

Source: https://code.claude.com/docs/en/plugins/manifest-reference (VERIFIED)

> "A plugin manifest is the `plugin.json` file in a plugin's `.claude-plugin/` directory."
> "The manifest is optional. Without it, Claude Code loads the components it finds in the standard layout. The plugin name then comes from the marketplace entry, or from the directory name when you load the plugin with `--plugin-dir`."
> "Save the manifest at `.claude-plugin/plugin.json` under the plugin root. Put every other plugin file at the plugin root, not inside `.claude-plugin/`. That includes `skills/`, `commands/`, and `hooks/`."

### Fields (verbatim table from the manifest reference)

> "`name` is the only required key."

| Field | Type | Description |
| :- | :- | :- |
| `$schema` | String | JSON Schema URL for editor autocomplete. Claude Code ignores it at load time |
| `name` | String | Plugin identifier, required. Use kebab-case. Every component is namespaced under it |
| `displayName` | String | Name shown in UI in place of `name` |
| `version` | String | Version string. Setting it keeps users on that version until you change it |
| `description` | String | Short explanation of what the plugin provides |
| `author` | Object | `name`, which is required, plus optional `email` and `url` |
| `homepage` | String | Documentation URL. Must parse as a URL, or the plugin fails to load |
| `repository` | String | Source repository URL. Not validated |
| `license` | String | SPDX identifier such as `MIT` or `Apache-2.0` |
| `keywords` | Array of strings | Discovery tags |
| `metadata` | Object | Free-form object for your own data. Claude Code doesn't read it |
| `defaultEnabled` | Boolean | Whether the plugin starts enabled when the user hasn't set it. Defaults to `true` |
| `dependencies` | Array of strings or objects | Plugins that must be enabled for this one to work |
| `settings` | Object | Settings Claude Code applies while the plugin is enabled. Only `agent` and `subagentStatusLine` take effect |
| `userConfig` | Object | Values Claude Code prompts the user for when the plugin is enabled |
| `channels` | Array of objects | Message channels the plugin provides, each bound to one of its MCP servers |
| `skills` | Path, or array of paths | Directories to scan for skills, each a directory of `<name>/SKILL.md` folders or one folder holding `SKILL.md` directly. `"."` names the plugin root. **Adds to** the default `skills/` scan |
| `commands` | Path, array of paths, or object | Flat `.md` command files, directories of them, or an object map of command name to `source` or `content`. **Replaces** the default `commands/` scan |
| `agents` | Path, or array of paths | Agent `.md` files. Directories aren't accepted. Replaces the default `agents/` scan |
| `hooks` | Path, object, or array of either | `.json` hook files or inline hook config. Loaded together with `hooks/hooks.json` |
| `mcpServers` | Path, object, or array of either | `.json` MCP config files, `.mcpb` or `.dxt` bundles, or inline server configs keyed by name. Loaded together with `.mcp.json`; a server name declared later replaces an earlier one |
| `lspServers` | Path, object, or array of either | `.json` LSP config files or inline server configs keyed by name |
| `outputStyles` | Path, or array of paths | Output style files or directories. Replaces the default `output-styles/` scan |
| `workflows` | Path, or array of paths | Workflow `.js` files or directories |
| `experimental` | Object | Container for `themes`, `monitors`, and `evals` |

### Naming rules

> "`name`: The plugin identifier. It must be non-empty, with no spaces, `@`, `:`, path separators, control characters, or bidirectional-formatting characters; use kebab-case. Claude Code namespaces every component under it, so an agent `reviewer` in plugin `deploy-tools` appears as `deploy-tools:reviewer`."

Locally reproduced (`claude plugin validate` on `{"name":"Bad_Name"}`):

```
‼ Found 4 warnings:
  > name: Plugin name "Bad_Name" is not kebab-case. Claude Code accepts it, but the Claude.ai marketplace sync requires kebab-case (lowercase letters, digits, and hyphens only, e.g., "my-plugin").
  > version: No version specified. Consider adding a version following semver (e.g., "1.0.0")
  > description: No description provided. Adding a description helps users understand what your plugin does
  > author: No author information provided. Consider adding author details for plugin attribution
√ Validation passed with warnings
```

So non-kebab-case is a *warning* (fails only under `--strict`), but kebab-case is required for claude.ai sync and strongly recommended. `version`, `description`, `author` are optional but warned about when missing.

### Unknown fields

> "An unrecognized top-level key is stripped, and an unrecognized key inside a `userConfig` option, `channels` entry, `lspServers` config, or `monitors` entry is rejected."

Locally reproduced: `bogusField: Unknown field 'bogusField'. Claude Code ignores it at load time.` (warning; exit 1 with `--strict`).

### Can component paths be customised?

Yes, via the component keys, with these rules (VERIFIED):

> "Every component path in a manifest is relative to the plugin root and must start with `./`. A path such as `commands/foo.md` fails validation."
> "Every component path must resolve inside the plugin root and must exist."
> "**Replaces the default**: `commands`, `agents`, `outputStyles`, `workflows`, `experimental.themes`, `experimental.monitors`. When you set `commands`, the default `commands/` directory isn't scanned. To keep the default and add more, list it explicitly: `"commands": ["./commands/", "./extras/"]`"
> "**Adds to the default**: `skills`. The `skills/` directory is still scanned, and the listed directories load alongside it"
> "**Merges**: `hooks`, `mcpServers`, `lspServers`. The default file loads first, and what the manifest declares merges into it"

For this project: use the default directories and omit every component key. Nothing needs customising.

### `version` semantics (matters for updates)

> "A version string, not checked against semver. Setting it pins the plugin to that version until you change it".
> "Because the manifest comes first, a manifest that pins `"version": "1.0.0"` keeps every user on the cached copy until its author changes the string, however many commits they push. To let users track commits instead, leave `version` out of both the manifest and the entry." (https://code.claude.com/docs/en/plugins/loading#versions-and-updates)

---

## 2. Directory layout conventions

Source: manifest reference "Standard layout" (VERIFIED)

| Component | Default location | Contents |
| :- | :- | :- |
| Manifest | `.claude-plugin/plugin.json` | Plugin metadata and configuration. Optional |
| Skills | `skills/` | One `<name>/SKILL.md` per skill. A plugin with `SKILL.md` at its root, no `skills/`, and no `skills` key loads as a single skill |
| Commands | `commands/` | Flat Markdown command files. **Prefer `skills/` for new plugins** |
| Agents | `agents/` | Agent Markdown files. Subfolders are part of the agent name |
| Hooks | `hooks/hooks.json` | Hook configuration |
| MCP servers | `.mcp.json` | MCP server definitions |
| LSP servers | `.lsp.json` | LSP server configurations |
| Output styles | `output-styles/` | |
| Workflows | `workflows/` | |
| Themes | `themes/` | |
| Monitors | `monitors/monitors.json` | |
| Executables | `bin/` | Files here are on the Bash tool's `PATH` while the plugin is enabled. **claude.ai and Cowork don't install a plugin that has this directory** |
| Settings | `settings.json` | `agent` and `subagentStatusLine` defaults |

Only `plugin.json` (and, for a self-hosting repo, `marketplace.json`) go inside `.claude-plugin/`:

> "Only `plugin.json` goes inside `.claude-plugin/`. Components saved there don't load. The plugin root is the plugin's own directory, not `~/.claude/` itself." (https://code.claude.com/docs/en/plugins/create)

> "A `CLAUDE.md` at the plugin root isn't loaded as context, and `claude plugin validate` warns when it finds one. To include instructions that load into Claude's context, put them in a skill."

A `README.md` at the plugin root is recommended by the publish page ("add a `README.md` at the plugin root").

Proposed layout for this repo (plugin root = repo root):

```text
a-i-plugin/
├── .claude-plugin/
│   ├── plugin.json          # the plugin manifest
│   └── marketplace.json     # one entry, source "./"
├── .mcp.json                # launches the Python server with uv
├── skills/
│   ├── live-basics/SKILL.md        # knowledge skill (Claude-invocable)
│   ├── live-journal/SKILL.md       # knowledge skill pointing at ${CLAUDE_PLUGIN_DATA}/journal.md
│   ├── status/SKILL.md             # "slash command": disable-model-invocation: true
│   └── ...
├── hooks/
│   └── hooks.json           # optional SessionStart hook (see §10)
├── server/                  # the Python project: pyproject.toml, uv.lock, src/…
├── docs/
└── README.md
```

Note on the `server/` directory name: avoid naming it `bin/` (reserved meaning above), and avoid putting the Python package at the repo root with a `SKILL.md` beside it (a root `SKILL.md` would make the whole plugin load as a single skill when `skills/` is absent).

---

## 3. `.mcp.json` inside a plugin

Sources: https://code.claude.com/docs/en/mcp#plugin-provided-mcp-servers, https://code.claude.com/docs/en/plugins/components#mcp-servers, manifest reference "Environment variables" (all VERIFIED)

### Format

> "Declare it in `.mcp.json` at the plugin root, in the same shape as a project `.mcp.json`."
> "You can also omit the `mcpServers` wrapper and put `db` at the top level of the file."

```json
{
  "mcpServers": {
    "database-tools": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_URL": "${DB_URL}"
      }
    }
  }
}
```

Fields for stdio (from the MCP page): `type` (`stdio` | `http` | `sse` | `ws`; `stdio` is implied when `command` is present), `command`, `args`, `env`, plus optional `timeout` (per-server tool-execution timeout in ms, min 1000). There is **no `cwd` field** in the documented schema — use `uv run --directory` / `--project` instead of relying on a working directory.

The `mcpServers` manifest key is an alternative/addition: "Claude Code loads `.mcp.json` at the plugin root first, then each declared shape in order. A server name declared later replaces an earlier one."

### `${CLAUDE_PLUGIN_ROOT}` substitution — which fields

Verbatim table (manifest reference, "Where each variable resolves"):

| Plugin component | Fields where `${...}` resolves | Exported to the process |
| :- | :- | :- |
| Hook commands | Anywhere in `command` and `args` | `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `CLAUDE_PROJECT_DIR`, and `CLAUDE_PLUGIN_OPTION_<KEY>` |
| MCP `stdio` servers | `command`, `args`, `env` | `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` |
| MCP `http`, `sse`, `ws` servers | `url`, `headers`, `headersHelper` | Not applicable |
| Skill, command, and agent content | Anywhere in the Markdown body | Not applicable |

> "**Substitution**: `${CLAUDE_PLUGIN_ROOT}` and the other path variables are substituted in `command`, `args`, and `env`. No quoting is needed in `args`, because each element is passed as one argument"

So: yes in `args`, yes in `env`, yes in `command`; no `cwd` exists. The server process also receives `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` as environment variables even if you don't reference them.

Ordinary `${VAR}` references are also expanded (the general MCP page: "Expands in: `command`, `args`, `env`, `url`, `headers`"; `${VAR:-default}` syntax exists for project `.mcp.json`). For plugins, a missing variable shows as `Invalid MCP server config for "<server>": Missing environment variables: <names>` in the `/plugin` Errors tab (troubleshooting page). Whether `${VAR:-default}` works inside a *plugin* `.mcp.json` is **UNVERIFIED** (documented for `.mcp.json` generally, not tested here).

### `${CLAUDE_PLUGIN_DATA}` — yes, it exists

Verbatim table (manifest reference):

| Variable | Resolves to | Use it for |
| :- | :- | :- |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path of the plugin's installed version | Scripts, binaries, and config files bundled with the plugin |
| `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/<id>/`, created on first reference and kept across plugin updates. `<id>` is the plugin identifier with every character other than a letter, digit, `_`, or `-` replaced by `-` | Installed dependencies such as `node_modules`, generated code, and caches |
| `${CLAUDE_PROJECT_DIR}` | The project root | Project-local scripts and config files |

> "`${CLAUDE_PLUGIN_ROOT}` changes when the plugin updates, so don't write state there."
> "By default, Claude Code deletes the `${CLAUDE_PLUGIN_DATA}` directory when you uninstall the plugin from the last place it's installed. For `--keep-data` and the other cases where it stays, see plugin uninstall."
> Components page: "`${CLAUDE_PLUGIN_DATA}`: a directory that survives updates, for `node_modules`, virtual environments, and caches. It resolves to `~/.claude/plugins/data/<id>/` and is created when first referenced" and "`my-plugin@my-marketplace` becomes `my-plugin-my-marketplace`."

For this project the id would be `ableton-live@a-i-plugin` → `~/.claude/plugins/data/ableton-live-a-i-plugin/`. For a `--plugin-dir` load the plugin id is `<name>@inline`, so the data dir is presumably `…/data/ableton-live-inline/` (**UNVERIFIED** exact path; follows from the documented rule).

### Tool and server naming (VERIFIED, verbatim from the MCP page)

> "Tools from a plugin-bundled MCP server include both the plugin name and the server key in their callable name. The full form is `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`, where any character outside `A-Z`, `a-z`, `0-9`, `_`, and `-` is replaced with `_`. For the `database-tools` server bundled in a plugin named `my-plugin`, a `query` tool is callable as: `mcp__plugin_my-plugin_database-tools__query`"
> "Use this full name when referencing the tool in permission rules, a skill's `allowed-tools` list, a subagent's `tools` field, or a hook matcher. A hook matcher written against the bare server key, such as `mcp__database-tools__.*`, never fires for a plugin-bundled server."
> "The server itself registers under the scoped name `plugin:<plugin-name>:<server-name>`, such as `plugin:my-plugin:database-tools`."

So it is **`mcp__plugin_<plugin>_<server>__<tool>`**, not `mcp__<server>__<tool>`. Keep both the plugin name and the server key short: with plugin `ableton-live` and server `live`, a `get_status` tool is `mcp__plugin_ableton-live_live__get_status`. Hyphens in the plugin name are preserved (only characters outside `[A-Za-z0-9_-]` become `_`).

Locally reproduced: `claude --plugin-dir <scratch> plugin details ableton-live` printed `MCP servers (1)  live  (tool schemas resolved at runtime; not counted)`.

### Validation of `.mcp.json`

> "`claude plugin validate` checks `.mcp.json` and reports a server entry that Claude Code would drop at load time as an error. Requires Claude Code v2.1.281 or later."

Locally reproduced on a deliberately broken file:

```
Validating mcp: …/.mcp.json
× Found 2 errors:
  > mcpServers.no-command.command: Invalid input: expected string, received undefined. The plugin loader silently drops this server at load.
  > mcpServers.userconf.env.T: references ${user_config.missing_key}, which plugin.json does not declare under "userConfig" … Declare the option or fix the key.
```

Important: at load time "A server entry in `.mcp.json` that fails the schema doesn't appear in the **Errors** tab. Claude Code drops that server and records `Invalid MCP server config for <server> in <path>` only in that debug log" (`claude --debug`, log at `~/.claude/debug/<session-id>.txt`). So run the validator in CI.

---

## 4. Skills in plugins

Source: https://code.claude.com/docs/en/skills (VERIFIED), https://code.claude.com/docs/en/plugins/components#skills

### Frontmatter fields (verbatim summary from the skills reference)

All fields are optional; `description` is "Recommended".

| Field | Description |
| :- | :- |
| `name` | Command name shown in `/` menu. Defaults to directory name. |
| `description` | What the skill does and when to use it. Claude uses this to decide when to apply the skill. If omitted, uses the first non-empty line of markdown content. |
| `when_to_use` | Additional context for when Claude should invoke the skill. Appended to `description` in the skill listing. |
| `argument-hint` | Hint shown during autocomplete, e.g., `[issue-number]`. |
| `arguments` | Named positional arguments for `$name` substitution. Space-separated string or YAML list. |
| `disable-model-invocation` | "Set to `true` to prevent Claude from automatically loading this skill. Use for workflows you want to trigger manually with `/name`. Also prevents the skill from being preloaded into subagents." Default `false`. |
| `user-invocable` | "Set to `false` when only Claude should invoke the skill: Claude Code hides it from the `/` menu and doesn't run it when you type `/name`. Use for background knowledge users shouldn't invoke directly." Default `true`. |
| `allowed-tools` | Tools Claude can use without permission during the turn that invokes this skill. Space- or comma-separated string or YAML list. |
| `disallowed-tools` | Tools removed from Claude's pool while the skill is active. |
| `model` | Model to use when skill is active (same values as `/model`, or `inherit`). |
| `effort` | `low` / `medium` / `high` / `xhigh` / `max`. |
| `context` | `fork` to run in a forked subagent context. |
| `agent` | Subagent type when `context: fork`. |
| `background` | With `context: fork`; default `true`. |
| `hooks` | Hooks registered when the skill is invoked. |
| `paths` | Glob patterns limiting when the skill activates. |
| `shell` | `bash` (default) or `powershell` for `` !`cmd` `` blocks. |
| `metadata` | Free-form map. |
| `license`, `compatibility` | Accepted (Agent Skills spec), not acted on. |

Boolean values: `true/false`, plus `yes/no/on/off/1/0` (v2.1.218+).

### Description length and name rules

> "Put the key use case first: the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing to reduce context usage."

No explicit name-length limit is stated on the Claude Code page; the convention is lowercase kebab-case. Reserved names: `synced`, `anthropic-skills` (and `anthropic-skills:*`). The open Agent Skills spec (agentskills.io) is referenced for `license`/`compatibility`; its own stricter name/description limits were **not fetched here (UNVERIFIED)**.

Locally observed: `claude plugin validate` (2.1.286) passed a `SKILL.md` with `name: Bad Skill Name With Spaces`, an empty `description`, an unknown field and `disable-model-invocation: maybe` with **no warnings**, even with `--strict`. Frontmatter validation is lenient in this build; do not rely on it to catch skill mistakes.

### Namespacing

> "**Command name**: `/<plugin>:<directory>`, so `skills/review/SKILL.md` in `my-plugin` is `/my-plugin:review`. If you set `name` in the frontmatter, it replaces the last segment and the plugin prefix stays."
> "The bare `/fancy` also invokes the skill unless another command already uses that name."

So `skills/status/SKILL.md` in plugin `ableton-live` → `/ableton-live:status` (and `/status` if nothing else claims it).

### Progressive disclosure and size

> "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files."
> "When you or Claude invoke a skill, the rendered `SKILL.md` content enters the conversation as a single message and stays there across later turns."

Supporting files live beside `SKILL.md` and are referenced with relative Markdown links:

```text
my-skill/
├── SKILL.md (required - overview and navigation)
├── reference.md (detailed API docs - loaded when needed)
├── examples.md (usage examples - loaded when needed)
└── scripts/
    └── helper.py (utility script - executed, not loaded)
```

Variables usable in the body: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N` (`$0` first), `$name` (with `arguments:`), `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}` ("For plugin skills, the skill's subdirectory, not plugin root"), `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` ("plugin skills only"). This means a skill can literally say "Read `${CLAUDE_PLUGIN_DATA}/journal.md`" and Claude Code substitutes the absolute path when it loads the skill.

### Context cost of a plugin's skills

Overview page: "for each skill, agent, and command that Claude can invoke on its own, the name and description are in Claude's context on every turn … The full text of a skill or agent loads only when it's used." A skill with `disable-model-invocation: true` has "Description not in context, full skill loads when you invoke". `claude plugin details <name>` prints the projected per-skill cost (locally: two tiny skills → "Always-on: ~80 tok").

---

## 5. Slash commands in plugins

Sources: skills page (formerly `/docs/en/slash-commands`), components page "Commands" (VERIFIED)

### Convergence — commands are skills now

> "**Custom commands have been merged into skills.** A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same way. Your existing `.claude/commands/` files keep working. Skills add optional features: a directory for supporting files, frontmatter to control whether you or Claude invokes them, and the ability for Claude to load them automatically when relevant."

> Components page: "Commands are the older format, and skills supersede them for new work. A skill runs by name the same way, and it can also carry supporting files in its directory. Keep `commands/` for files you're moving over from `.claude/commands/`."

Locally confirmed: `claude plugin details` counts a `commands/status.md` file under `Skills (2)  live-basics, status`.

### If you still use `commands/<name>.md`

> "Save a command at `commands/<file>.md` and it becomes `/<plugin>:<file>`. A subdirectory adds a segment, so `commands/db/migrate.md` is `/my-plugin:db:migrate`."
> "Command files take the same frontmatter as skills." / "A command file in `.claude/commands/` accepts the same fields except `name` and `paths`."

Frontmatter therefore: `description`, `argument-hint`, `arguments`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `disable-model-invocation`, `user-invocable`, `context`, `agent`, `hooks`, `shell`, `metadata`.

### Argument substitution and inline bash

| Variable | Description |
| :- | :- |
| `$ARGUMENTS` | All arguments passed when invoking the skill. "If no placeholder receives an argument, Claude Code appends `ARGUMENTS: <value>` to skill content." |
| `$ARGUMENTS[N]` | 0-based index |
| `$N` | Shorthand: `$0` first, `$1` second (note: **0-based**, unlike older docs that used `$1` for the first) |
| `$name` | Named argument declared in `arguments:` |

> "The `` !`<command>` `` syntax runs shell commands before the skill content is sent to Claude. The command output replaces the placeholder, so Claude receives actual data, not the command itself."

Multi-line form: a fenced block whose info string is `!`. Rules: the `!` must be at the start of a line or after whitespace; output is inserted as plain text and not re-scanned. `"disableSkillShellExecution": true` in settings turns it off.

### `@file` references

The skills page no longer has a dedicated "@file" section. It does say (about synced skills): "In any other session on your machine, Claude Code doesn't run `!` commands, doesn't attach the files that `@` references name the way it does for a local skill…" — which implies `@path` references in a local/plugin skill body **are** attached as they are in the prompt. Treat the exact syntax/limits as **UNVERIFIED** from this research; prefer `${CLAUDE_PLUGIN_DATA}/…` paths plus an instruction to Read them, or `` !`cat …` `` to inline content.

### Recommendation

Implement every "slash command" as `skills/<name>/SKILL.md` with `disable-model-invocation: true`. This keeps the command out of Claude's always-on context (zero per-turn cost), still gives `/ableton-live:<name>`, and allows supporting files. Use `commands/` only if you must.

---

## 6. Marketplace

Sources: https://code.claude.com/docs/en/plugins/marketplace-reference, https://code.claude.com/docs/en/plugins/create-marketplace, https://code.claude.com/docs/en/plugins/publish, https://code.claude.com/docs/en/plugins/host-marketplace, https://code.claude.com/docs/en/plugins/install (all VERIFIED)

### `.claude-plugin/marketplace.json` schema

> "Save the marketplace file at `.claude-plugin/marketplace.json` in your marketplace's directory."
> "The directory that contains `.claude-plugin/` is called the marketplace root, and every relative plugin source resolves from it, not from `.claude-plugin/`."

Top-level fields — "`name`, `owner`, and `plugins` are required":

| Field | Type | Description |
| :- | :- | :- |
| `name` | string | Marketplace identifier: letters, digits, `.`, `_`, and `-`, starting with a letter or digit, and no `..`. It forms the half after `@` of every plugin id installed from the marketplace |
| `owner` | object | Maintainer information. `name` is required; `email` and `url` are optional |
| `plugins` | array | Plugin entries. Each entry is validated on its own |
| `$schema` | string | Ignored at load time |
| `description` | string | Marketplace description shown to users. `claude plugin validate` warns when it's missing |
| `version` | string | Marketplace manifest version |
| `metadata.description`, `metadata.version` | string | Alternate location |
| `metadata.pluginRoot` | string | Directory that bare plugin source names resolve under (v2.1.239+) |
| `forceRemoveDeletedPlugins` | boolean | Uninstall removed plugins on users' machines |
| `allowCrossMarketplaceDependenciesOn` | array of strings | |
| `renames` | object | Former name → current name or `null` (v2.1.193+) |

Plugin entry fields — "`name` and `source` are required"; an entry "also accepts every `plugin.json` field":

| Field | Type | Description |
| :- | :- | :- |
| `name` | string | Plugin identifier … Users type it before `@` when they install |
| `source` | string or object | Where to fetch the plugin |
| `description` | string | Shown in `/plugin` listings and details |
| `version` | string | "When `plugin.json` also sets `version`, `plugin.json` takes precedence and `claude plugin validate` warns" |
| `category` | string | Free-form category |
| `tags` | array of strings | Free-form tags |
| `strict` | boolean | Default `true`. Whether `plugin.json` is the definitive source for components |
| `relevance` | object | Suggestion signals |
| `dependencies` | array | |
| `defaultEnabled` | boolean | Entry value takes precedence over `plugin.json` |
| `displayName` | string | |
| `metadata` | object | |
| `headers`, `headersHelper` | | `archive` sources only |

Display-field precedence: "For a field you set on the entry, users see the entry's value, even when `plugin.json` sets a different one." So keep `description`, `author`, etc. in **one** place (plugin.json) and only `name`/`source`/`description`/`category` in the entry, or make them identical.

Reserved marketplace names include `claude-plugins-official`, `claude-code-plugins`, `anthropic-*`, `inline`, `builtin`, `skills-dir`, `synced`, and (v2.1.275+) `npm`, `pip`, `uv`, `cargo`, `github`, `gh` in any casing. `a-i-plugin` is fine.

### Can a repo be BOTH the marketplace and the plugin at its root?

**Yes — VERIFIED in two ways.**

Publish page, "Add the marketplace file to your repository":

> "To publish from the plugin's own repository, save the marketplace file beside `plugin.json` in `.claude-plugin/`, with one entry whose `source` is `"./"`, the repository root. Give the entry the same `name` as `plugin.json`"
> ```json
> {
>   "name": "your-marketplace",
>   "owner": { "name": "Your Name" },
>   "plugins": [
>     { "name": "deploy-helper", "source": "./" }
>   ]
> }
> ```
> "In your shell, run `claude plugin validate .` in the repository to check the file before you push."

Marketplace reference, relative-path source: "Must start with `./` … `"."` on its own means the root itself".

Locally reproduced (2.1.286): a scratch dir with `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (`"source": "./"`) + `.mcp.json` + `skills/` + `commands/`:

- `claude plugin validate <dir>` → `Validating marketplace manifest: …/marketplace.json … √ Validation passed with warnings` (it recursed into `plugin.json`: `plugins[0] plugin.json → bogusField: Unknown field …`).
- `claude --plugin-dir <dir> plugin list` → `ableton-live@inline … Status: √ loaded`; `plugin details` listed 2 skills and 1 MCP server. So the presence of `marketplace.json` does not break `--plugin-dir` as long as `plugin.json` is also there (the "folder of plugins" rule only kicks in when `.claude-plugin/` has **no** `plugin.json`).

Caveats:

- "Keep the entry name and the manifest name the same." Otherwise `Plugin "<manifest-name>" not found in marketplace`.
- "Users install, enable, and configure your plugin by `name@marketplace`, so a renamed plugin is a different plugin to every existing install." Choose both names once.
- The marketplace `name` is what appears after `@`, "not the repository name". Setting `"name": "a-i-plugin"` makes the id `ableton-live@a-i-plugin`.
- Relative-path entries only resolve when Claude Code has the whole repo (github/git/directory marketplace sources). They fail if someone adds the marketplace as a bare raw `marketplace.json` URL. Tell users to add `vi-o-al-ai/a-i-plugin` (GitHub shorthand), not a raw URL.
- Validation from the root checks the marketplace file and `plugin.json`, but **not** `.mcp.json` or skill files: "from a marketplace directory, Claude Code doesn't open the plugins' skill, agent, command, or hook files, or the MCP server files they bundle. To find errors in those files, validate each plugin directory". Locally confirmed: with a broken `.mcp.json`, `claude plugin validate <root>` passed, while `claude plugin validate <root>/.claude-plugin/plugin.json` ran `Validating mcp: …/.mcp.json` and failed. **Run both in CI.**

### Exact user-facing install commands

Host-marketplace page: GitHub → users run `/plugin marketplace add your-org/your-marketplace`; then `/plugin install code-formatter@your-marketplace`.

Install page: "Run `/plugin install` with the plugin's name and marketplace. In a session, this command doesn't install right away: it opens the `/plugin` panel on that plugin's details so you can review it and choose a scope first." Then choose user / project / local scope. Summary ends `Plugin is now active.` or `Run /reload-plugins to activate.`

One-step (v2.1.275+): `/plugin install deploy-helper --marketplace your-org/your-marketplace` — "Give the plugin name by itself, without an `@marketplace` suffix."

Shell equivalents (`claude plugin --help` locally confirms the subcommands):

```bash
claude plugin marketplace add vi-o-al-ai/a-i-plugin        # prints: Successfully added marketplace: a-i-plugin (declared in user settings)
claude plugin install ableton-live@a-i-plugin               # prints: Successfully installed plugin: ableton-live@a-i-plugin (scope: user)
claude plugin install ableton-live@a-i-plugin --scope project   # or local
claude plugin list
claude plugin details ableton-live
```

GitHub shorthand forms: `owner/repo`, `owner/repo#ref`, `owner/repo@ref`. Cloning: "Claude Code probes `ssh -T git@github.com` and clones over SSH when the probe succeeds. If the probe fails, or the SSH clone itself fails, it clones over HTTPS." `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` forces HTTPS. Clone timeout 120 s (`CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS`). A private repo works with the user's existing git credentials (`gh auth login && gh auth setup-git`).

### How plugins update

- Manual: `claude plugin update ableton-live@a-i-plugin` — "Update a plugin to the latest version its marketplace offers. The new version loads in your next session, or after you run `/reload-plugins`." With `name@marketplace` it refreshes "The named marketplace, before the lookup". Prints `<name> is already at the latest version (<version>).` when the computed version is unchanged.
- Marketplace refresh: `/plugin marketplace update a-i-plugin` or `claude plugin marketplace update a-i-plugin` (no name → all).
- Auto-update: "Background auto-update is off for your marketplace by default, and `marketplace.json` has no field to turn it on." Users enable it under `/plugin` → Marketplaces → "Enable auto-update". When on: after the first message, random delay up to 10 min, then `Plugin updated: <name> · Run /reload-plugins to apply`.
- Versioning: "Bump `version` on each release: users stay on their cached copy until the string changes … Omit `version`: users track your commits instead." Don't set it in both places.
- Optional release tag: `claude plugin tag [--push]` creates `{name}--v{version}` (only needed if other plugins declare version ranges on yours).

---

## 7. Local development

Sources: https://code.claude.com/docs/en/plugins/create#develop-without-a-marketplace, https://code.claude.com/docs/en/plugins/cli-reference (VERIFIED); `claude --help` locally.

`claude --help` (2.1.286):

```
--plugin-dir <path>   Load a plugin from a directory or .zip for this session only; a folder of plugins
                      loads each child (repeatable: --plugin-dir A --plugin-dir B.zip) (default: [])
--plugin-url <url>    Fetch a plugin .zip from a URL for this session only (repeatable) (default: [])
```

`claude plugin validate --help`:

```
Usage: claude plugin validate [options] <path>
Validate a plugin or marketplace manifest, or the skills, agents, and commands in a directory
  --json      Output the validation report as JSON (same exit codes)
  --strict    Treat warnings as errors (exit 1). Use in CI to fail on unrecognized fields,
              missing metadata, and other issues that the runtime tolerates.
```

Exit codes: `0` passed (with or without warnings), `1` failed (or warnings under `--strict`), `2` unexpected error.

Directory resolution: "`.claude-plugin/marketplace.json`, when it exists; Otherwise `.claude-plugin/plugin.json`; Otherwise the component files". `/plugin validate <path>` inside a session prints the same report.

Workflow:

1. `claude plugin validate ./.claude-plugin/plugin.json` (manifest + `.mcp.json`) and `claude plugin validate .` (marketplace + plugin.json).
2. `claude --plugin-dir /path/to/a-i-plugin` — "loads a directory … for one session … nothing is written to your settings for it." The plugin loads in place as `ableton-live@inline`; `${CLAUDE_PLUGIN_ROOT}` points at the source dir.
3. After edits: "run `/reload-plugins` to load the changes." It prints `Reloaded: N plugins · N skills · N agents · N hooks · N plugin MCP servers …`. For MCP: "a server whose configuration is unchanged keeps its connection. A server whose configuration changed reconnects". If the reload would add/remove an MCP server it may warn about prompt-cache invalidation → `/reload-plugins --force`.
4. `/mcp` to see `plugin:ableton-live:live` connected; `/plugin` → Installed → details to see components; Errors tab for load failures.
5. `claude --debug` writes `~/.claude/debug/<session-id>.txt` with MCP startup stderr.
6. `claude --plugin-dir <path> plugin list` / `plugin details <name>` work from the shell (locally confirmed).

Alternatives: `claude plugin init <name>` scaffolds under `~/.claude/skills/<name>/` (auto-loads every session as `<name>@skills-dir`); `CLAUDE_CODE_PLUGIN_DIRS=/abs/path` (v2.1.280+) when you can't pass the flag. A session-only plugin shadows a same-named installed plugin ("replaced silently"), which is handy for testing against the installed copy.

Pitfall: "`--plugin-dir` at a marketplace root doesn't load the plugins under `plugins/`" — not our case because the plugin *is* the root.

Pitfall: "Server works with `--plugin-dir` but fails after install … Claude Code copies an installed plugin into its cache, so a path that only works from the source directory breaks. Write paths inside the plugin with `${CLAUDE_PLUGIN_ROOT}`."

---

## 8. Where plugins live on disk — and where to write history

Source: https://code.claude.com/docs/en/plugins/loading#find-plugins-on-disk (VERIFIED)

> "Claude Code keeps plugin files and state records under one plugins root, which is `~/.claude/plugins` unless you set `CLAUDE_CODE_PLUGIN_CACHE_DIR`."

| Path (under the plugins root) | What it holds |
| :- | :- |
| `cache/<marketplace>/<plugin>/<version>/` | "One directory per installed version of a marketplace plugin … `${CLAUDE_PLUGIN_ROOT}` points at this directory" |
| `data/<plugin-id>/` | "The plugin's persistent directory, exposed as `${CLAUDE_PLUGIN_DATA}` … Claude Code creates it when a plugin component first uses it and keeps it across updates. By default, Claude Code deletes it when you uninstall the plugin from its last scope." |
| `marketplaces/<name>/` | "The clone or download of a marketplace added from GitHub…" |
| `installed_plugins.json`, `known_marketplaces.json` | install records |

For this project: `~/.claude/plugins/cache/a-i-plugin/ableton-live/<version>/` (plugin root after install), `~/.claude/plugins/marketplaces/a-i-plugin/` (the repo clone), `~/.claude/plugins/data/ableton-live-a-i-plugin/` (data dir).

> "Because `${CLAUDE_PLUGIN_ROOT}` points at a version directory, a plugin's root path changes with every version. Keep a plugin's durable files in `${CLAUDE_PLUGIN_DATA}` instead."
> "When you update or uninstall a plugin, Claude Code writes an `.orphaned_at` marker into the previous version directory. It removes that directory in a background cleanup 14 days later".
> "**Every other marketplace plugin**: Claude Code copies the plugin into `cache/<marketplace>/<plugin>/<version>/` at install and loads that copy. Files outside the plugin directory aren't copied".

### Recommendation for the server's history / journal files

1. **Primary: `${CLAUDE_PLUGIN_DATA}`**, passed to the server through an explicit env var in `.mcp.json` (e.g. `ABLETON_LIVE_MCP_DATA_DIR=${CLAUDE_PLUGIN_DATA}`), so the server code has no Claude-Code-specific knowledge. Reasons: it is the documented location for exactly this ("generated code, and caches", "survives updates"); it is created on first reference; skills and hooks can refer to the same directory via the same variable, so the SKILL.md that says "read the journal" and the server that writes it agree on the path without hard-coding; uninstall cleans it up (and `claude plugin uninstall --keep-data` preserves it when the user wants to keep the journal). A `--plugin-dir` dev load gets its own data dir (`…-inline`), which keeps dev data separate from the installed copy's data.
2. **Fallback when the variable is unset** (running the server outside Claude Code, in tests, or from Claude Desktop): XDG — `${XDG_DATA_HOME:-~/.local/share}/ableton-live-mcp/`. This is the conventional per-user data location on Linux/macOS and avoids cluttering `$HOME`.
3. `~/.claude-live/` is a reasonable *third* option if you want one stable, discoverable path regardless of how the plugin was loaded, but it adds a dotfile to `$HOME`, is not XDG-compliant, and is not cleaned up on uninstall. Offer it only as an explicit override (`ABLETON_LIVE_MCP_DATA_DIR`).
4. Never write under `${CLAUDE_PLUGIN_ROOT}` (versioned, read-mostly, deleted 14 days after an update). This includes uv's default `.venv` location — see §9.

---

## 9. MCP server startup, first-run installs, approval

Sources: MCP page, loading page "Node.js package dependencies", components page "Install dependencies into the data directory", troubleshooting page (VERIFIED where quoted)

### Approval

> "Plugin MCP servers work identically to user-configured servers." / "When you enable a plugin, Claude Code starts its MCP servers automatically" / "At session startup, Claude Code connects the servers for enabled plugins automatically."

Contrast with project `.mcp.json`: "For security reasons, Claude Code prompts for approval in interactive sessions before using project-scoped servers from `.mcp.json` files." That prompt does **not** apply to a plugin installed from a marketplace; the install (reviewing the "Will install" pane) is the trust step. One exception: a *project-scope skills-directory plugin* (checked into a repo under `.claude/skills/<plugin>/`) — "MCP servers it declares go through the same per-server approval as a project `.mcp.json`". Not relevant to a marketplace install.

Individual tool calls still go through normal permission prompts unless pre-approved (`allowed-tools` in a skill, or permission rules naming `mcp__plugin_ableton-live_live__…`). Users can toggle the server off per project in `/mcp` without uninstalling.

### Startup timeout

> "Configure MCP server startup timeout using the `MCP_TIMEOUT` environment variable (for example, `MCP_TIMEOUT=10000 claude` sets a 10-second timeout)".

The **default value is not stated** in the MCP page or the env-vars page (**UNVERIFIED**; community reports of ~30 s could not be confirmed). Assume startup must complete in tens of seconds, not minutes. Other knobs: `MCP_TOOL_TIMEOUT` (per-tool execution), `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` (default 30 min for stdio), `MAX_MCP_OUTPUT_TOKENS` (default 25 000), `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` (default 2 min).

### First-run dependency installs — Python is on you

> "When Claude Code copies a plugin into the cache, it also installs the plugin's Node.js package dependencies there … The install runs only when the plugin's root directory contains both a `package.json` and a supported lockfile."
> "When the automatic install can't provide a dependency, install it from a hook into the persistent data directory. That includes packages that need their lifecycle scripts to build, **Python dependencies**, and plugins locked with Yarn or pnpm."
> Components page: "`${CLAUDE_PLUGIN_DATA}`: a directory that survives updates, for `node_modules`, **virtual environments**, and caches".

The docs show a `SessionStart` hook that runs `npm install` into `${CLAUDE_PLUGIN_DATA}` on first run. The uv equivalent is below. No official docs mention `uv`/`uvx` for plugin servers (checked MCP, components, loading, troubleshooting pages) — the uv specifics below come from `uv 0.8.17 --help` and a local test, not from Claude Code docs.

Implications for `uv run --directory ${CLAUDE_PLUGIN_ROOT}/server ableton-live-mcp`:

- On the very first launch uv must (a) find or download a CPython matching `requires-python`, (b) create a venv, (c) resolve/install deps. With network this is typically 5–60 s; a Python download can push it past a short `MCP_TIMEOUT`. Mitigate: commit `uv.lock`, pass `--frozen` (locally confirmed flag: "Run without updating the `uv.lock` file"), keep deps minimal, and pre-warm from a `SessionStart` hook (`uv sync --frozen …`, hook default timeout 600 s) so the MCP launch finds the venv ready on later sessions. A SessionStart hook and MCP startup both begin at session start, so the *first* session may still race; document that first launch can be slow and that `/mcp` → Reconnect fixes it.
- By default `uv run --directory X` creates `X/.venv`, i.e. **inside `${CLAUDE_PLUGIN_ROOT}`**. That's writable, but it violates "don't write state there", bloats the cache dir, and is thrown away on every version bump (re-download). Set `UV_PROJECT_ENVIRONMENT=${CLAUDE_PLUGIN_DATA}/venv` in the server's `env`: locally confirmed that uv 0.8.17 honours it (`Creating virtual environment at: customenv`). uv re-syncs the venv when the lockfile changes, so updates still work. Optionally also `UV_CACHE_DIR=${CLAUDE_PLUGIN_DATA}/uv-cache` if you want everything self-contained (otherwise uv uses `~/.cache/uv`, which is fine).
- `uv` must be on the PATH of the process that launched `claude`. If a user installed uv with the standalone installer, it's at `~/.local/bin/uv`, usually on PATH; `~` is not expanded in `command`. Document "install uv first" in README; `claude plugin validate` cannot check for it.
- Alternative `uvx --from ${CLAUDE_PLUGIN_ROOT}/server ableton-live-mcp`: `--from <FROM>` ("Use the given package to provide the command") accepts a local path and installs into uv's tool cache outside the plugin dir, but it re-resolves the path source on each launch and ignores `uv.lock`. `uv run --frozen --directory …` is more deterministic. Prefer `uv run`.
- Node-style auto-install never runs for us (no `package.json`), so nothing in the plugin needs to avoid the 60 s Node install limit.

### Other runtime notes

- "`claude mcp get` prints `Command: stdio`, an empty `Args:` line, and each environment variable as `NAME=[REDACTED]`" for plugin servers — don't expect to debug args via `claude mcp get`; use `claude --debug`.
- Plugin MCP servers reconnect on `/reload-plugins` only when their config changed; in cloud sessions they start on demand.

---

## 10. Hooks: can a `SessionStart` hook point Claude at a journal file?

Source: https://code.claude.com/docs/en/hooks (VERIFIED)

Yes. A plugin declares hooks in `hooks/hooks.json` ("under a top-level `"hooks"` key, in the same shape as the `hooks` object in `settings.json`"), and `SessionStart` supports matchers `startup`, `resume`, `clear`, `compact`, `fork`. For this event, "Claude Code adds stdout it treats as plain text to Claude's context" and "a hook that only loads context can print to stdout directly without building JSON"; alternatively print `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"…"}}`, which "Claude Code wraps … in a system reminder and inserts … at the start of the conversation, before the first prompt". The hook process receives `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` in its environment, so a tiny script can `cat "$CLAUDE_PLUGIN_DATA/journal.md"` (or print a one-line pointer such as `The Ableton Live learning journal is at <path>; read it before working with Live.`) and exit 0. Command hooks default to a 600 s timeout, so cost is not a concern, but keep the injected text short because it lands in context every session. Phrase it as facts, not commands: "Text framed as out-of-band system commands can trigger Claude's prompt-injection defenses, which causes Claude to surface the text to you instead of treating it as context." Use exec form (`command` + `args`) or double-quote `"${CLAUDE_PLUGIN_ROOT}"` in shell form so a path with spaces stays one word (the validator warns otherwise). Remember plugin hooks "don't wait for one of the plugin's skills or commands to be used" — they fire in every session where the plugin is enabled, so match only `startup|resume|clear` (add `compact` if you want the pointer to survive compaction) and consider a knowledge skill (`user-invocable: false`) as the lighter-weight alternative when deterministic injection isn't required.

---

## Recommended manifest set for this project

Names used below are proposals: plugin `ableton-live`, marketplace `a-i-plugin` (matches the repo so users see `ableton-live@a-i-plugin`), MCP server key `live` (short, to keep `mcp__plugin_ableton-live_live__<tool>` readable). Change them once, before first publish — renames break installs.

### `.claude-plugin/plugin.json`

```json
{
  "name": "ableton-live",
  "displayName": "Ableton Live",
  "version": "0.1.0",
  "description": "Control and inspect Ableton Live from Claude Code: bundled MCP server, skills and slash commands.",
  "author": {
    "name": "vi-o-al-ai",
    "url": "https://github.com/vi-o-al-ai"
  },
  "homepage": "https://github.com/vi-o-al-ai/a-i-plugin#readme",
  "repository": "https://github.com/vi-o-al-ai/a-i-plugin",
  "license": "MIT",
  "keywords": ["ableton", "live", "music", "mcp", "daw"]
}
```

Notes: no component keys → default `skills/`, `commands/`, `hooks/hooks.json`, `.mcp.json` are scanned. Bump `version` on every release (or delete the field to let users track commits). `homepage` must parse as a URL. `license` is UNVERIFIED as the project's actual choice — adjust.

### `.claude-plugin/marketplace.json`

```json
{
  "name": "a-i-plugin",
  "description": "Ableton Live tooling for Claude Code by vi-o-al-ai",
  "owner": {
    "name": "vi-o-al-ai",
    "url": "https://github.com/vi-o-al-ai"
  },
  "plugins": [
    {
      "name": "ableton-live",
      "source": "./",
      "description": "Control and inspect Ableton Live from Claude Code: bundled MCP server, skills and slash commands.",
      "category": "music",
      "tags": ["ableton", "live", "mcp"]
    }
  ]
}
```

Notes: entry `name` must equal `plugin.json` `name`. Do **not** put `version` here (plugin.json wins and the validator warns). `"source": "./"` is the documented self-hosting form; `"."` is equivalent on v2.1.221+. Users add it with `/plugin marketplace add vi-o-al-ai/a-i-plugin` (GitHub shorthand → full clone, so the relative source resolves).

### `.mcp.json`

```json
{
  "mcpServers": {
    "live": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--frozen",
        "--directory", "${CLAUDE_PLUGIN_ROOT}/server",
        "ableton-live-mcp"
      ],
      "env": {
        "UV_PROJECT_ENVIRONMENT": "${CLAUDE_PLUGIN_DATA}/venv",
        "ABLETON_LIVE_MCP_DATA_DIR": "${CLAUDE_PLUGIN_DATA}"
      }
    }
  }
}
```

Notes: requires `server/pyproject.toml` with a `[project.scripts] ableton-live-mcp = "…:main"` entry and a committed `server/uv.lock` (`--frozen` refuses to rewrite it, which also avoids writing into the cache dir). `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` substitution in `args` and `env` is documented; no quoting needed in `args`. The server should read `ABLETON_LIVE_MCP_DATA_DIR`, falling back to `$XDG_DATA_HOME/ableton-live-mcp` → `~/.local/share/ableton-live-mcp`. Resulting tool names: `mcp__plugin_ableton-live_live__<tool>`; server shows in `/mcp` as `plugin:ableton-live:live`. `uv` must be on PATH (UNVERIFIED whether `"command": "${UV_BIN:-uv}"` default-expansion works in a plugin `.mcp.json`; plain `uv` is the safe choice). Validate with `claude plugin validate ./.claude-plugin/plugin.json`.

Optional pre-warm hook, `hooks/hooks.json` (exec form; only needed if first-launch time is a problem):

```json
{
  "description": "Pre-build the Python environment for the Ableton Live MCP server and surface the learning journal",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "uv",
            "args": ["sync", "--frozen", "--directory", "${CLAUDE_PLUGIN_ROOT}/server"],
            "timeout": 300
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/journal-pointer.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

UNVERIFIED detail: whether `env` can be set per hook (the hook schema fetched here shows `command`, `args`, `timeout`, `shell`, `async`, no `env`), so the `uv sync` hook would need `UV_PROJECT_ENVIRONMENT` exported by a wrapper script (`scripts/sync-venv.sh` reading `$CLAUDE_PLUGIN_DATA`) rather than inline. `journal-pointer.sh` would be e.g. `[ -f "$CLAUDE_PLUGIN_DATA/journal.md" ] && echo "The Ableton Live learning journal (notes from earlier sessions) is at $CLAUDE_PLUGIN_DATA/journal.md."`.

### One skill — `skills/live-journal/SKILL.md` (knowledge skill, Claude-invoked)

```markdown
---
name: live-journal
description: Notes Claude has learned about this user's Ableton Live setup and habits, kept in a journal that persists across sessions. Use at the start of any Ableton Live task, and whenever a Live tool call fails or the user corrects a Live-related assumption.
user-invocable: false
allowed-tools: Read, mcp__plugin_ableton-live_live__get_status
---

The journal lives at `${CLAUDE_PLUGIN_DATA}/journal.md` (created by the `live` MCP server).

1. Read it before changing anything in Live.
2. ...
```

Notes: `user-invocable: false` hides it from the `/` menu; its description stays in context so Claude can load it when relevant — keep the description under the 1 536-char cap and put the key use case first. `${CLAUDE_PLUGIN_DATA}` is substituted in the Markdown body for plugin skills. Keep the file under 500 lines; put long reference material in sibling files linked relatively.

### One "slash command" — `skills/status/SKILL.md` (user-invoked only)

```markdown
---
name: status
description: Show whether Ableton Live is reachable and summarise the open set (tracks, tempo, playing state).
argument-hint: "[verbose]"
disable-model-invocation: true
allowed-tools: mcp__plugin_ableton-live_live__get_status, mcp__plugin_ableton-live_live__get_session_info
---

Call the `live` server's status tool, then summarise. If `$ARGUMENTS` contains `verbose`, include every track.
```

Invoke as `/ableton-live:status` (or `/status` when unambiguous). `disable-model-invocation: true` keeps it out of the always-on context. If you prefer the legacy layout, the identical frontmatter minus `name` works in `commands/status.md` and yields the same `/ableton-live:status`.

### CI / release checklist

```bash
claude plugin validate --strict .                              # marketplace.json + plugin.json
claude plugin validate --strict ./.claude-plugin/plugin.json   # plugin.json + .mcp.json
claude --plugin-dir . plugin details ableton-live              # component inventory + token cost
# then, in a session started with: claude --plugin-dir .
#   /mcp            → plugin:ableton-live:live connected
#   /ableton-live:status
```

Release: bump `version` in `plugin.json`, push to the default branch; users run `claude plugin update ableton-live@a-i-plugin` (or enable auto-update for the `a-i-plugin` marketplace). Optionally `claude plugin tag --push`.

---

## Sources

- Overview: https://code.claude.com/docs/en/plugins
- Create a plugin (dev loop, `--plugin-dir`, `/reload-plugins`): https://code.claude.com/docs/en/plugins/create
- Components (skills, commands, hooks, MCP, data dir): https://code.claude.com/docs/en/plugins/components
- Manifest reference (plugin.json, path rules, env vars, standard layout): https://code.claude.com/docs/en/plugins/manifest-reference (also reached via https://code.claude.com/docs/en/plugins-reference)
- Marketplace reference (marketplace.json, sources, reserved names): https://code.claude.com/docs/en/plugins/marketplace-reference
- Create a marketplace: https://code.claude.com/docs/en/plugins/create-marketplace (also reached via https://code.claude.com/docs/en/plugin-marketplaces)
- Host and maintain a marketplace (updates, auto-update, renames): https://code.claude.com/docs/en/plugins/host-marketplace
- Publish (self-hosting marketplace with `source: "./"`): https://code.claude.com/docs/en/plugins/publish
- Install and manage plugins (user commands, scopes): https://code.claude.com/docs/en/plugins/install
- Loading reference (disk layout, versions, Node dep install): https://code.claude.com/docs/en/plugins/loading
- CLI reference (`claude plugin …`, `/plugin`, `/reload-plugins`, one-session flags): https://code.claude.com/docs/en/plugins/cli-reference
- Troubleshooting (MCP servers that don't start, `--plugin-dir` pitfalls): https://code.claude.com/docs/en/plugins/troubleshooting
- Skills (frontmatter, substitution, commands merged into skills): https://code.claude.com/docs/en/skills (also reached via https://code.claude.com/docs/en/slash-commands)
- MCP (plugin-provided servers, tool naming, approval, timeouts): https://code.claude.com/docs/en/mcp
- Hooks (SessionStart, exec/shell form, additionalContext): https://code.claude.com/docs/en/hooks
- Environment variables (`CLAUDE_CODE_PLUGIN_CACHE_DIR`, `CLAUDE_CODE_PLUGIN_DIRS`, …): https://code.claude.com/docs/en/env-vars
- Local CLI: `claude --help`, `claude plugin --help`, `claude plugin validate --help`, `claude plugin <sub> --help` on Claude Code 2.1.286; `uv run --help` on uv 0.8.17.
