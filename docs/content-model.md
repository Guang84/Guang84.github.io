# GLab data model

The canonical sources are individual records under `data/projects/` and `data/articles/`. Each file has a `$schema` link and one unique URL-safe `id`; the filename must exactly match that ID. The build writes `index.json` inside each folder so the browser can discover the record files on a static host.

Projects support narrative `sections`, `architecture`, an embedded `guide`, `validation`, repository/demo links, tags, and accent colors. Articles support publication metadata, tags, and ordered narrative `sections`.

Every record also requires `publicationStatus` (`draft` or `published`) and boolean `featured`. Only published records reach the rendered lists, detail routes, search, and RSS. Section prose may use `paragraphs` or a single `content` string; lists may use `points` or `items`.

Create a draft with `python3 scripts/new_content.py project "New project"` or `python3 scripts/new_content.py article "New article"`. Complete it under `data/drafts/`, move it into the matching source directory, change `publicationStatus` to `published`, then run `python3 scripts/build.py` and `python3 scripts/validate.py`. The optional `--publish` flag creates a source record directly, but replace the sample text before committing; schema validation cannot verify editorial completeness. No content HTML is generated.
