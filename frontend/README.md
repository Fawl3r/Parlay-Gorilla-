# Parlay Gorilla Frontend

Next.js frontend for the Parlay Gorilla application.

## Quick Start

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (copy `.env.example` to `.env.local`):
   - `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)
   - `NEXT_PUBLIC_SITE_URL`: Public site URL (used for absolute sitemap URLs)
   - `PG_BACKEND_URL`: Optional server-side backend URL (used by sitemap generation when rewrites aren’t available)

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

### Authentication
- **Backend JWT Auth**: Login/register via the FastAPI backend (`/api/auth/*`)
- **Protected Routes**: Automatic redirect for unauthenticated users
- **Session Management**: Stores JWT in `localStorage` as `auth_token`
- **Password Reset**: Email-based reset flow via backend endpoints

### Social Features
- **Share Parlays**: Share your parlays with unique links
- **Social Feed**: Browse shared parlays from other users
- **Leaderboard**: See top-performing parlay creators
- **Like/Comment**: Engage with shared parlays

### Advanced Parlay Builders
- **Same-Game Parlays**: Build parlays from a single game
- **Round-Robin**: Create multiple parlay combinations
- **Teasers**: Adjust point spreads for better odds

### Core Features
- **Multi-Sport Support**: NFL, NBA, NHL, MLB, Soccer, and more
- **AI Parlay Generation**: 1-20 leg parlays with confidence scores
- **Custom Builder**: Build your own parlays with AI analysis
- **Analytics Dashboard**: Track your parlay performance

## Project Structure

```
frontend/
├── app/                      # Next.js app directory
│   ├── auth/                 # Authentication pages
│   │   ├── login/           # Login page
│   │   ├── signup/          # Signup page
│   │   ├── forgot-password/ # Password reset
│   │   └── verify-email/    # Email verification
│   ├── social/              # Social features
│   │   └── page.tsx        # Social feed
│   ├── share/               # Shared parlay pages
│   │   └── [token]/        # Shared parlay detail
│   ├── parlays/             # Advanced parlay builders
│   │   ├── same-game/      # Same-game parlays
│   │   ├── round-robin/     # Round-robin builder
│   │   └── teasers/        # Teaser builder
│   ├── app/                 # Main dashboard
│   └── layout.tsx          # Root layout
├── components/               # React components
│   ├── ui/                 # shadcn/ui components
│   ├── social/             # Social feature components
│   └── parlay/             # Advanced parlay components
├── lib/                     # Utilities
│   ├── api.ts              # API client
│   ├── auth-context.tsx    # Auth context provider
│   └── social-api.ts       # Social API client
└── package.json
```

## Development

The frontend uses Next.js 15+ with the App Router, TypeScript, Tailwind CSS, and shadcn/ui components.

### Key Technologies
- **Next.js 14+**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Animations and transitions
- **shadcn/ui**: Component library

## Environment Variables

See `.env.example` for all required variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_ADSENSE_CLIENT_ID`: Google AdSense (optional)
- `NEXT_PUBLIC_SPORTSBOOK_AFFILIATE_ADS_ENABLED`: Enable sportsbook affiliate ads in ad slots (optional)
- `NEXT_PUBLIC_GEOIP_FALLBACK_IPAPI`: Optional geo fallback (client-side request to ipapi.co)
- `NEXT_PUBLIC_ONLINE_SPORTS_BETTING_STATES`: Optional override list of US states (codes) where online betting is enabled
- `NEXT_PUBLIC_*_AFFILIATE_URL`: Your sportsbook affiliate tracking URLs (BetMGM/Caesars/bet365/FanDuel/Fanatics/DraftKings/BetRivers)
- `NEXT_PUBLIC_SPORTSBOOK_ALLOWED_STATES_JSON`: Optional JSON map to restrict each sportsbook to specific US states

## Troubleshooting

### `Cannot find module './####.js'` from `.next/server/webpack-runtime.js`

This indicates the Next.js server webpack runtime is trying to load a chunk from the wrong path.

- **Fix**:
  - Run `npm run clean:next`
  - Rebuild: `npm run build`
  - Optional smoke check: `npm run test:server-bundle` (or `npm run test:smoke:build`)

