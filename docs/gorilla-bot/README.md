# Gorilla Bot Knowledgebase

This folder contains user-facing knowledgebase articles that Gorilla Bot indexes for in-app answers.

## Structure

- `kb/` contains Markdown articles that are safe to show users.
- Only add product-facing content here (avoid internal ops docs).

## Indexing

After editing or adding KB docs, reindex:

```bash
cd backend
python scripts/gorilla_bot_index_kb.py
```

To force a full reindex:

```bash
python scripts/gorilla_bot_index_kb.py --force
```

## Tips

- Keep docs concise and factual.
- Avoid sensitive or internal-only details.
- Use clear headings so Gorilla Bot can summarize quickly.
