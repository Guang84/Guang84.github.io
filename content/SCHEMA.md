# GLab content model

GLab v12 has two source collections and no standalone guide collection.

## `content/projects/*.json`

One JSON file is the complete source for one project page. It contains:

- identity: `id`, `title`, `category`, `year`, `status`, and `summary`
- source links: `repository`, `url`, and optional `demoUrl`
- discovery and presentation: `tags` and `colors`
- narrative: `sections`
- system description: `architecture`
- practical instructions: embedded `guide`
- testing/release evidence: `validation`
- page context: `pageNote`

The embedded `guide` object contains `title`, `summary`, `audience`, `url`, `prerequisites`, `steps`, optional `command`, `verification`, and `troubleshooting`. It is rendered as the `#guide` section of the project page and indexed as a searchable project-guide result.

## `content/articles/*.json`

Every essay, technical article, blog-style note, or field note belongs here. Use `kind` to distinguish an `Article` from a `Field note`. Each record contains metadata plus its ordered `sections`.

## Templates

Reusable starter records live in the root `templates/` directory. Create a draft with:

```bash
python scripts/new_content.py project "new project"
python scripts/new_content.py article "new article"
python scripts/new_content.py page "custom page"
```

Project and article drafts are created under `content/drafts/`. After review, move them into the matching source collection and rebuild.

## Build

After changing source JSON:

```bash
python scripts/build.py
python scripts/validate.py
```

The builder writes public HTML to `projects/`, `articles/`, and the repository root for GitHub Pages.
