# Workspace Agent Directives

## Bootstrap Protocol
- On session initialization:
  1. Verify Git hook configuration by checking if `.git/hooks/pre-commit` exists. If missing, execute `.agent/setup.ps1` (or `.agent/setup.sh` on POSIX, or verify that `.agent/.registry` is present).
  2. Check if the local `.agents/skills/` directory contains active domain skills.
  3. Automatically detect the application stack from repository manifest files (`pyproject.toml`, `package.json`, `go.mod`, etc.) and synchronize skills silently without pausing to ask the user for confirmation to analyze.
  4. Once skills are linked, strictly enforce their constraints during all subsequent code generation and review tasks.
  5. Note: Global skills (`code-review`, `doc-sync`, `error-discipline`, `git-release`, `incident-triaging`, `intent-discipline`, `repo-wiki`, `script-optimization`, `security-auditor`, `strategic-reconnaissance`, `test-discipline`, `workspace-initializer`) are pre-loaded at the machine level (`~/.gemini/config/skills/`). Do not attempt to symlink them into `.agents/skills/`.
  6. Repository Knowledge Graph: Check for `wiki/`. When architectural decisions, design contracts, or runbooks change, maintain atomic records using the `repo-wiki` protocol (`[[wikilinks]]`, YAML frontmatter). Use `.agent/wiki.ps1 query <topic>` (or `.agent/wiki.sh`) to slice context on demand without bloating the prompt window.

## General Constraints
- The `.agent/` and `.agents/` directories (including `.agent/.registry`) are internal registry, hook, and customization storage. NEVER treat them as application source code, and NEVER allow internal registry files to trigger skills.
- **Strict Zero-Legacy-Skills Invariant:** Antigravity IDE discovers workspace skills exclusively from `.agents/skills/` (plural). The legacy directory `.agent/skills/` (singular) is permanently DEPRECATED and PROHIBITED. Agents and scripts MUST NEVER create, link, or reference `.agent/skills/`. All active domain skills and local customizations MUST reside strictly in `.agents/skills/`.
- Do not add or remove third-party dependencies without explicit user confirmation.
- Keep the context window lean: do not load files into context unless actively modifying them.

## Self-Upgrading Pipeline & Gated Execution
- When resolving issues, authoring fixes, or proposing pull requests, adhere strictly to the 4-stage pipeline codified in `ops/self-upgrading-pipeline`:
  1. **Context Bootstrapper:** Verify maintainer taste and conventions (local rules in `.agents/rules/maintainer-taste.md` or global cache `~/.gemini/config/repo-tastes/`).
  2. **Dual-Mode Stage 2 (Defect Remediation vs. Feature Creation):**
     - *Mode A (Defect Fix):* Modifying implementation logic before authoring and executing an isolated failing reproduction test (`TestIssueXXXXX`) is STRICTLY FORBIDDEN.
     - *Mode B (Feature Creation & Greenfield):* Creating new files and scaffolding interfaces follows contract-and-specification-first flow; agents are not blocked by defect reproducer tripwires.
  3. **Adversarial Pre-Flight Filter:** Audit diffs for zero formatting noise (<= 5% pure whitespace churn), ensure concurrency sanitizers (`-race`) pass, and eliminate extraneous debug statements.
  4. **Recursive Distiller:** Capture trajectory deltas and record generalizable architectural invariants.
- **Repository Mode Boundary:** External OSS maintainer restrictions, upstream PR taste mimicry, diff noise ceilings, and mandatory red-test reproducer gates are strictly confined to external open-source repositories (`mode == "oss"`). Personal repositories (`mode == "personal"`, identified via `detect_mode.py`, username namespaces like `awesome06`, or explicit `.agents/mode`) are completely exempt from upstream OSS gatekeeping; the user's personal development harness, rapid prototyping, and custom engineering flows govern without interference.
- **Mental Anti-Slop Scrubber Invariant:** All pull request titles, summaries, commit messages, and review comments across all repositories MUST pass the Repo-Agnostic Mental Anti-Slop Scrubber. Corporate jargon (`holistic`, `comprehensive`, `robust`, `seamless`, `surgical`), self-congratulatory boilerplate (`adheres to enterprise standards`), AI hallmarks (`delve`, `tapestry`), and raw terminal log dumps are strictly prohibited.
- **Compile-Signal Upstream Parity Invariant:** During upstream dependency upgrades, compiler errors (unhandled enum variants, new trait methods, restructured fields) MUST be treated as hard diagnostic signals of expanded upstream surface. Suppressing warnings or stubbing dummy returns is strictly forbidden; agents must audit and expose matching capabilities in client-facing APIs.
- **CI Reality & Execution Parity Transparency:** Authoring tests for runtimes or subsystems that compile locally but are omitted from active continuous integration workflows (`.github/workflows/*.yml`) is STRICTLY FORBIDDEN. Agents must verify CI workflow commands before writing tests; unexecuted tests in CI are dead weight that rot silently.
- **One Canonical Home Per Claim & Docstring Mirror Testing:** Technical claims live in exactly one location: callable contracts in docstrings, shared semantics in type docs, and architectural trade-offs in narrative guides. Any executable docstring example marked with skip directives (`# doctest: +SKIP`) MUST have a companion live mirror test preventing doc code rot.
- **Enumerate the Family Before Modifying Invariant:** Before extending, modifying, or creating an interface method, trait implementation, FFI capsule getter, or dunder protocol (`__datafusion_*__`, `arrow::compute::*`, `logstorage.*`), agents MUST run a mandatory pre-flight grep enumerating all existing sibling implementations in that family. Modifying one member of a protocol family without verifying signature parity and behavioral harmony across the entire family is STRICTLY FORBIDDEN.
- **Closed PR Non-Reopening Invariant (`mode == "oss"`):** In external open-source repositories, reopening a closed pull request (`gh pr reopen`) is STRICTLY FORBIDDEN. If a PR has been closed (by maintainers, automation bots, or author action), agents MUST NOT unilaterally reopen it or propose reopening it. Maintainer closures signify architectural disagreement, stale design, or maintainer fatigue; reopening forces unwanted notifications and antagonizes maintainers. If the contribution is still viable, contributors MUST either seek maintainer alignment on the linked tracking issue first or submit a fresh, cleanly rebased PR from a new branch with all maintainer feedback resolved. In personal repositories (`mode == "personal"`), reopening PRs is fully permitted.

---

## Chat Output Readability & Anti-LaTeX Invariant

- **Zero-Tolerance for Broken Math Delimiters:** In conversational chat turns and assistant messages, agents MUST prioritize immediate visual clarity and plain-text markdown formatting. The Chat UI renders standard GitHub-Flavored Markdown (GFM) WITHOUT a KaTeX/MathJax engine. Unescaped LaTeX causes broken formatting, raw dollar signs, and syntax noise.
- **Rule A (Zero Dollar Delimiters):** NEVER wrap equations, numbers, units, or variables in single (`$...$`) or double (`$$...$$`) dollar signs. Dollar signs are ONLY allowed in code blocks for shell variables (e.g. `echo $PATH`), shell prompts (`$ command`), or monetary values (`$50`).
- **Rule B (Zero LaTeX Math Commands):** NEVER use LaTeX math macros in chat responses. Always use ASCII / Unicode equivalents (`*` or `x` instead of `\times`, `/` instead of `\div`, `µs` instead of `\mu s`, `O(N)` instead of `\mathcal{O}(N)`, `<=`, `>=`, `!=` instead of `\le`, `\ge`, `\neq`, `A / B` instead of `\frac{A}{B}`, `<->` instead of `\leftrightarrow`).
- **Scope Boundaries:** Formal LaTeX syntax (`$...$`, `$$...$$`, `\begin{equation}`) is STRICTLY RESERVED for `.ipynb` notebook cells, `.tex` documents, and PDF generation templates. Outside of those specific file types, ALL outputs MUST be 100% clean plain-text/Unicode GFM.
- **Pre-Emission Mental Scan Gate:** Before outputting ANY response, the agent MUST run a mandatory verification check:
  - *"Does this response contain any `$` enclosing math or variables?"* -> Strip immediately.
  - *"Does this response contain `\times`, `\div`, `\text{`, `\mu`, or `\mathcal`?"* -> Replace with `*`, `/`, plain text, `µs`, or `O(...)`.

---

## Git Staging & Commit Review Protocol

- **Pre-Staging Verification Gate:** Run active linters and tests via `test-discipline` before staging any changes.
- **Autonomous Staging & Commit Formulation:** Agents are authorized to stage modified files (`git add`) and craft structured commit messages adhering strictly to the `globals/git-release` Conventional Commits standard:
  - **Header:** `<type>(<scope>): <subject>` (maximum 72 characters, imperative mood, lowercase, no trailing period).
  - **Multi-Line Body:** Comprehensive technical description detailing:
    - **Motivation & Intent:** Why the modification or skill addition was made.
    - **Key Changes:** Bullet points identifying exact files, components, or invariants modified.
    - **Verification Evidence:** Proof of local test runs (e.g., `tests passed`).
- **Documentation & Directive Lockstep Gate (`AGENTS.md` <-> `README.md`):** Before staging any change, agents MUST verify that any modification altering directory layouts, tools, scripts, or operational workflows is reflected consistently in both `README.md` and `AGENTS.md`. Committing changes where `README.md` and `AGENTS.md` describe divergent instructions is STRICTLY FORBIDDEN.
- **Review Gate (Not Committed Until Review):** Commits MUST NOT be executed autonomously. Always leave changes staged and present the drafted commit message and diff summary to the user for review. Execute `git commit` ONLY after explicit user review and approval.
- **Strict Zero-Unprompted-Push Guardrail:** NEVER run `git push` without explicit user instruction.

