# GLab content model

GLab v7 intentionally has only three public content pillars.

## `content/projects/*.json`

One JSON file represents one project. A project record contains:

- identity: `id`, `title`, `category`, `year`, `status`, `summary`
- source: `repository`, `url`, optional `demoUrl`
- discovery: `tags`, `colors`
- main narrative: `sections`
- architecture: `architecture`
- testing/release evidence: `validation`
- related procedural page: `guideId`

The generated project HTML combines all of this, plus its guide content, into **one complete project case-study page**.

## `content/articles/*.json`

Every essay, technical article, blog-style note, or field note belongs here. Use `kind` to distinguish `Article` from `Field note`. The public site does not create a separate Blogs section.

## `content/guides/*.json`

A guide contains a single practical workflow:

- `summary`
- `audience`
- `prerequisites`
- `steps`
- optional `command`
- `verification`
- `troubleshooting`
- optional `projectId`

Each guide is generated as one detailed page.

## Build

After changing JSON:

```bash
python scripts/build.py
python scripts/validate.py
```
