# Social Bot Commands

## Basic Usage

Run the social bot to generate and post to X:

```bash
python -m social_bot.bot
```

## Optional Flags

### `--print-only`
Generate and print the post without posting to X (useful for testing):

```bash
python -m social_bot.bot --print-only
```

### `--force-type <type>`
Force a specific post type:

```bash
# Edge Explainer
python -m social_bot.bot --force-type edge_explainer

# Trap Alert
python -m social_bot.bot --force-type trap_alert

# Parlay Math
python -m social_bot.bot --force-type parlay_math

# Example Parlay
python -m social_bot.bot --force-type example_parlay
```

### `--seed <number>`
Use a specific seed for reproducible output (useful for testing):

```bash
python -m social_bot.bot --seed 12345
```

## Configuration

**Important:** Make sure `BOT_DRY_RUN=false` in your `.env` file if you want the bot to actually post to X.

- If `BOT_DRY_RUN=true`: Bot will only generate and print the post without posting
- If `BOT_DRY_RUN=false`: Bot will generate and post to X

## Examples

### Test a post without posting:
```bash
python -m social_bot.bot --print-only
```

### Post an edge explainer:
```bash
python -m social_bot.bot --force-type edge_explainer
```

### Post with a specific seed (for debugging):
```bash
python -m social_bot.bot --seed 42
```

