---
inclusion: always
---
# Token-efficient tool usage
-
Prefer RTK for supported terminal commands.
- Use `rtk git status` instead of `git status`.
- Use `rtk git diff` instead of `git diff`.
- Use `rtk grep` instead of raw grep or rg.
- Use compact test output where supported.
- Never dump entire directories or large files.
- Read only relevant files and line ranges.
- Request full output only when necessary.
- Preserve exact error messages and diagnostic details.
- Use `rtk bypass` when compressed output is insufficient.