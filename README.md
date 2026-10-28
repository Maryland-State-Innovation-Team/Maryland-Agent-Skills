# Maryland Agent Skills

A collection of [Agent Skills](https://agentskills.io/) that teach AI coding assistants how to work with Maryland state government systems correctly. Maintained by the Maryland State Innovation Team.

## What's an Agent Skill?

[Agent Skills](https://agentskills.io/) are an open format for packaging specialized knowledge into reusable folders an AI agent can load on demand. Each skill is a directory with a `SKILL.md` file (frontmatter + instructions) plus optional `scripts/`, `references/`, and `assets/` subdirectories. The agent reads only the frontmatter at startup; when a user's prompt matches the skill's description, it loads the full instructions and bundled files into context.

The format is supported by Claude Code, OpenAI Codex, GitHub Copilot in VS Code, and other agentic clients — see the [Agent Skills client showcase](https://agentskills.io/clients) for the current list.

## What's in this repo

Four skills, each self-contained and installable independently:

| Skill | What it enables |
|---|---|
| [`mdwds/`](mdwds/) | Build Maryland.gov pages with the Maryland Web Design System — correct markup for every component, the right page shell, the required statewide banner, and template recipes for common page types. Pinned to MDWDS `0.51.1`. |
| [`maryland-imap/`](maryland-imap/) | Query Maryland's official geospatial services (`mdgeodata.md.gov`) — boundary layers for counties, municipalities, legislative districts, and ZIP codes, plus the geocoder. |
| [`socrata-api/`](socrata-api/) | Query any Socrata-powered open-data portal (`opendata.maryland.gov`, `data.cdc.gov`, and hundreds more) with correct SoQL, authentication, and pagination patterns. |
| [`pdf-accessibility/`](pdf-accessibility/) | Scan and remediate PDFs end-to-end against PDF/UA-1 (ISO 14289-1) using a self-contained open-source pipeline. Battle-tested on real reports. |

Without a skill, an agent asked to "build a Maryland.gov agency page" will hallucinate class names, miss the statewide banner requirement, or wrap the page in inline `<style>` to patch over not knowing MDWDS's design tokens. With a skill, it reads the component references first and produces correct, auditable markup on the first try. Same story for geospatial, open-data, and PDF-accessibility work — all three domains have enough state-specific or format-specific gotchas that a general-purpose agent gets them wrong without guidance.

## Installing a skill

Each top-level directory is a complete, independent Agent Skill. Pick one and either copy or symlink it into whatever skills directory your agent product watches. For Claude Code, that's `.claude/skills/` (per-project) or `~/.claude/skills/` (per-user):

```bash
# Project-scoped — available only in sessions inside this project
cp -r mdwds /path/to/your/project/.claude/skills/

# User-scoped — available in every Claude Code project
cp -r mdwds ~/.claude/skills/

# Symlink keeps the installed copy in sync with this repo as you pull updates
ln -s "$(pwd)/mdwds" ~/.claude/skills/mdwds
```

For other clients, consult that product's docs for where it loads skills from. The format is the same; only the directory differs.

Once installed, your agent auto-loads the skill the moment a prompt matches its `description` frontmatter. You don't need to invoke it manually.

## Example prompts

```
# mdwds/
Build me a Maryland state agency homepage with a hero, three feature cards,
and a news listing. The agency is the Department of Natural Resources.

# maryland-imap/
Use the attached context to create a map of Maryland legislative districts.
When I click a district I want to see the legislators' names.

# socrata-api/
Build me a dashboard using this context and this data URL:
https://opendata.maryland.gov/resource/9qyj-bhez.json

# pdf-accessibility/
Remediate all the PDFs in ./pdfs/ using the OSS pipeline — auto-tag, fix
metadata, generate alt text, and verify they pass PDF/UA-1.
```

## Skill structure at a glance

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
<skill-name>/
├── SKILL.md          # Required: frontmatter + top-level instructions
├── references/       # Optional: detailed docs the agent loads on demand
├── scripts/          # Optional: executable code the agent can run
└── assets/           # Optional: templates, images, data files
```

`SKILL.md`'s frontmatter has a `name` (must match the directory name) and a `description` that tells the agent when to activate the skill. Everything else is Markdown instructions the agent reads once activated. Reference files inside `references/` are loaded lazily — the agent follows a link from `SKILL.md` only when a given task calls for that file.

## Updating a skill

The `mdwds/` skill is pinned to a specific MDWDS release. When MDWDS ships a new stable version, update:

1. `mdwds/SKILL.md` — the pinned version string in the header
2. `mdwds/references/setup.md` — the CDN URLs and version note
3. `mdwds/references/components/*.md` and `recipes/*.md` — any markup, class names, or props that changed in the new release

Confirm the current stable version on [designsystem.maryland.gov](https://designsystem.maryland.gov/?path=/docs/getting-started-for-engineers--docs) before shipping an update.

The other three skills follow upstream APIs rather than versioned releases — update their reference files whenever the underlying API or dataset structure changes.

## Contributing

Pull requests welcome. For a new skill, follow the [Agent Skills specification](https://agentskills.io/specification): a top-level directory containing `SKILL.md` with valid frontmatter (`name` matching the directory, a specific `description` that mentions the keywords an agent should trigger on), plus whatever `references/` / `scripts/` / `assets/` subdirectories you need. Keep `SKILL.md` under ~500 lines — put details in `references/` so they load on demand.

## License

See [LICENSE](LICENSE) for details.
