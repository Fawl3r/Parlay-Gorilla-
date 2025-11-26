# F3 Parlay AI Frontend

Next.js frontend for the F3 Parlay AI application.

## Quick Start

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (copy `.env.example` to `.env.local`)

3. Run the development server:
```bash
npm run dev
```

## Project Structure

```
frontend/
├── app/                      # Next.js app directory
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Homepage
│   └── globals.css           # Global styles
├── components/                # React components
│   ├── ui/                   # shadcn/ui components
│   ├── GameCard.tsx          # Game display component
│   └── OddsDisplay.tsx       # Odds display component
├── lib/                      # Utilities
│   ├── api.ts                # API client
│   └── utils.ts              # Helper functions
└── package.json
```

## Development

The frontend uses Next.js 14+ with the App Router, TypeScript, Tailwind CSS, and shadcn/ui components.

