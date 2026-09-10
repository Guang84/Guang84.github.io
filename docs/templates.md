# Content templates

Use `python3 scripts/new_content.py article "Your title"` or `python3 scripts/new_content.py project "Your project"`. This creates a draft in `data/drafts/articles/` or `data/drafts/projects/` with today's date/year and a working editor schema link.

The templates in `data/templates/` are valid examples, with meaningful required fields and sample sections. Replace the sample text. Delete optional fields you do not need; do not leave empty guide, architecture, or validation objects. `sections` accept `paragraphs`, `points`, `items`, `content`, and `links` (objects containing `label` and `url`). Text is rendered as plain text, not HTML or Markdown. URLs must be HTTPS/HTTP links, root-relative site paths, or fragments. Repository documentation links must include the repository's full `blob/<branch>/...` URL.

To publish:

1. Move the completed file to `data/articles/` or `data/projects/`.
2. Change `$schema` to `../schemas/article.schema.json` or `../schemas/project.schema.json`.
3. Set `publicationStatus` to `published`; make sure `id` matches the filename without `.json`.
4. Set `featured: true` to prioritize the item on the homepage. Use ISO dates (`YYYY-MM-DD`), an integer project year, and string arrays for tags and lists.
5. Run `python3 scripts/release_check.py` and push to `main`.

`--publish` creates a starter directly in the source folder; finish its sample text before committing. Dates are editorial metadata, not scheduling instructions. Keep future releases as drafts until ready.

Project templates include an optional getting-started guide; remove the whole `guide` object if unnecessary. Record and nested field names are checked, so misspelled fields fail the build instead of silently disappearing. Sections must contain content, and `updated` must be an ISO date. Multiple prose/list fields in a section are all rendered. Details automatically include section navigation.

Both record types accept optional `colors: ["#5465db", "#30b8aa"]`. Omit this to get an automatic category-based palette. Articles may include `readTime` and `updated`; omit `updated` if there is no revision. Projects may include `repository`, `demoUrl`, `architecture`, `guide`, and `validation`. See existing project records for complete examples. Shared JSON Schema validation checks source records and templates before build output is written.
