RONGMEI HYMNAL — PER-SON JSON STRUCTURE (SCHEMA 2.1)

STRUCTURE
  <book-id>/
    book.json
    songs/
      <number>-<title-slug>/
        song.json

Each song.json contains one song record. Multiple language versions belong
inside song.languages. Each language has its own title, credits, contentStatus,
and content object.

CONTENT RULES
- "structured" content preserves existing verse/chorus sections when the
  source already supplied them.
- "source-lines" preserves the original flat line sequence and blank lines.
  No verse/chorus boundaries were guessed from flat text.
- "title_only" means a language title exists in the source, but lyrics for
  that language were not present in the supplied export. Its content is null.
- Chorus sections are optional. Repeated sections can use repeatOf, but no
  repeat relationships were invented during this migration.
- The default language is the language with available lyric content.

PRESERVATION
- Original collection JSON exports are retained in _source-originals/.
- Original lyric text, line order, blank lines, section data, and source
  verification metadata are preserved.
- Legacy title variants and other legacy metadata are retained under
  song.sourceMetadata where applicable.
- Missing values remain null or absent; no translations, authorship,
  permissions, or editorial approvals have been invented.

RIGHTS
All rights are marked unknown in the new rights structure. This is not a
legal determination. Verify rights separately for each language, translation,
arrangement, recording, and intended use before publishing or distributing.

INDEX
book.json is a lightweight index. Applications can load book.json first,
then fetch only the selected song.json.
