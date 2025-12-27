# Parlay Gorilla - Comprehensive Summary for F3 AI Labs Website

**Purpose:** Complete overview of Parlay Gorilla for AI developer building the F3 AI Labs company website  
**Audience:** AI developer / web developer  
**Date:** December 2025

---

## Executive Summary

**Parlay Gorilla** is an AI-powered sports betting assistant web application that helps users build smarter, data-driven parlay bets (1-20 legs) across multiple sports. Unlike traditional tipster services that provide vague predictions, Parlay Gorilla uses proprietary AI technology to analyze games and generate parlays with transparent win probabilities, confidence scores, and detailed explanations.

**Key Value Proposition:** "Professional-grade sports betting analytics made accessible to everyone."

**Website:** https://www.parlaygorilla.com  
**Company:** F3 AI Labs LLC  
**Product Status:** Live in production

---

## What Parlay Gorilla Does

### Core Functionality

Parlay Gorilla is a web-based platform that:

1. **Generates AI-Powered Parlay Picks**
   - Analyzes upcoming games across multiple sports
   - Generates ready-to-bet parlays (1-20 legs) with three risk profiles:
     - **Safe**: High probability, lower payout
     - **Balanced**: Moderate risk/reward
     - **Degen**: High risk, high reward
   - Provides win probabilities, confidence scores, and expected value for each parlay

2. **Custom Parlay Builder**
   - Users can build their own parlays by selecting games and picks
   - AI analyzes the custom parlay and provides:
     - Combined win probability
     - Expected value calculation
     - Risk assessment
     - Detailed explanations for each leg
   - **Upset Finder**: Generates a "counter ticket" that flips picks where the model sees the best edge

3. **Game Analysis Hub**
   - Detailed matchup analysis for individual games
   - Model win probabilities
   - ATS (Against The Spread) trends
   - Over/Under insights
   - Injury reports and team news
   - AI-generated narrative analysis

4. **Real-Time Odds Integration**
   - Aggregates live odds from major sportsbooks (FanDuel, DraftKings, BetMGM, etc.)
   - Helps users find the best value across different books
   - Updates in real-time as odds change

5. **On-Chain Proof Anchoring** (Blockchain Integration)
   - Custom parlays saved by users are anchored on Solana blockchain via IQ Labs
   - Provides timestamped, tamper-evident proof of parlay creation
   - Users can verify their saved parlays on-chain
   - Privacy-focused: Only content hashes are stored on-chain, not personal data

---

## Sports Coverage

Parlay Gorilla supports comprehensive multi-sport coverage:

- **NFL** (National Football League)
- **NBA** (National Basketball Association)
- **NHL** (National Hockey League)
- **MLB** (Major League Baseball)
- **College Football** (NCAA)
- **College Basketball** (NCAA)
- **Soccer** (EPL, MLS, La Liga)
- **UFC** (Mixed Martial Arts)
- **Boxing**

---

## Technology Stack

### Architecture

Parlay Gorilla is a **monorepo** with three main runtime services:

#### 1. **Frontend (Next.js / TypeScript)**
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Deployment:** Render (www.parlaygorilla.com)
- **Key Features:**
  - Server-side rendering for SEO
  - Client-side authentication
  - Real-time odds display
  - Interactive parlay builder
  - Analytics dashboard
  - Social sharing features

#### 2. **Backend API (FastAPI / Python)**
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Database:** PostgreSQL (Render managed)
- **ORM:** SQLAlchemy (async)
- **Authentication:** JWT-based
- **Deployment:** Render (api.parlaygorilla.com)
- **Key Features:**
  - RESTful API endpoints
  - AI parlay generation engine
  - Probability calculations
  - User authentication & authorization
  - Payment processing integration
  - Background job scheduling
  - Webhook handlers (LemonSqueezy, Coinbase Commerce)

#### 3. **Inscriptions Worker (Node.js / TypeScript)**
- **Purpose:** Background service for blockchain operations
- **Technology:** Node.js, IQ Labs SDK
- **Function:** Anchors custom parlay proofs on Solana blockchain
- **Deployment:** Render worker service

### Data Storage

- **PostgreSQL:** Primary database for users, games, odds, saved parlays, analytics
- **Redis:** Distributed cache, background job queue, scheduler coordination

### External Integrations

- **The Odds API:** Live sports odds from major sportsbooks
- **OpenAI API:** Natural language explanations and game analysis
- **SportsRadar API:** Schedules, stats, injuries, team data
- **ESPN Scraper:** HTML scraping for matchup context and power rankings
- **LemonSqueezy:** Payment processing (subscriptions, credit packs)
- **Coinbase Commerce:** Crypto payment processing
- **IQ Labs / Solana:** Blockchain proof anchoring
- **Resend:** Transactional emails (verification, password reset)

---

## Key Features & Capabilities

### For Users

1. **AI Parlay Generation**
   - Generate 1-20 leg parlays with AI analysis
   - Three risk profiles (Safe/Balanced/Degen)
   - Win probabilities and confidence scores
   - Plain-English explanations

2. **Custom Parlay Builder**
   - Build your own parlays
   - Get AI analysis on custom picks
   - Upset finder (counter ticket generator)
   - Save and track parlays

3. **Game Analysis**
   - Detailed matchup breakdowns
   - Model probabilities
   - ATS trends
   - Injury reports
   - AI-generated narratives

4. **Real-Time Odds**
   - Compare odds across sportsbooks
   - Find best value
   - Live updates

5. **Analytics Dashboard**
   - Track parlay performance
   - Win/loss statistics
   - ROI calculations
   - Historical data

6. **Social Features**
   - Share parlays with unique links
   - Public parlay gallery
   - User profiles

7. **On-Chain Verification**
   - Blockchain-anchored proof of custom parlays
   - Verifiable timestamps
   - Tamper-evident records

### For Administrators

1. **Admin Dashboard**
   - User analytics
   - Revenue tracking
   - Subscription management
   - System health monitoring
   - Payment event logs

2. **Analytics**
   - User growth metrics
   - Feature usage statistics
   - Revenue breakdown
   - Conversion funnels

---

## Business Model

### Freemium SaaS Platform

**Free Tier:**
- Limited AI parlay generation
- Basic game analysis
- Custom parlay builder (limited)

**Premium Subscriptions:**
- **Monthly:** $39.99/month
- **Annual:** $399.99/year (save ~17%)
- **Lifetime:** $500 one-time payment

**Premium Features:**
- 200 AI parlays per 30-day period
- Unlimited custom parlay builder access
- Upset finder tools
- Comprehensive analytics
- Priority support

**Credit Packs (Pay-Per-Use):**
- 10 credits: $9.99
- 25 credits: $24.99
- 50 credits: $44.99
- 100 credits: $59.99

**Revenue Streams:**
1. Premium subscriptions (recurring)
2. Credit pack purchases (one-time)
3. Lifetime access plans
4. Future: Affiliate commissions (planned)

---

## Target Market

### Primary Users

1. **Casual Sports Bettors**
   - Want to improve success rate
   - Value data-driven insights
   - Prefer transparency over vague tips

2. **Serious Analysts**
   - Need professional-grade tools
   - Want detailed probability analysis
   - Track performance over time

3. **Fantasy Sports Players**
   - Use insights for fantasy decisions
   - Value matchup analysis
   - Want edge identification

### Market Opportunity

- **Sports Betting Market:** Projected $203B by 2030 (CAGR 10.2%)
- **US Market:** 40M+ sports bettors
- **Growing Demand:** Data-driven betting tools
- **Underserved:** Transparent, AI-powered analytics

---

## Key Differentiators

### What Makes Parlay Gorilla Unique

1. **Transparency**
   - Shows actual win probabilities (not vague predictions)
   - Expected value calculations
   - Clear confidence scores
   - Detailed explanations for every pick

2. **AI-Powered Intelligence**
   - Proprietary algorithms analyze multiple data points
   - Considers team stats, injuries, weather, trends
   - Natural language explanations
   - Continuous learning and improvement

3. **Multi-Sport Coverage**
   - Not just NFL - covers all major sports
   - Comprehensive market coverage
   - Cross-sport parlay building

4. **Real-Time Data**
   - Live odds integration
   - Up-to-the-minute analysis
   - Dynamic updates as information changes

5. **Educational Approach**
   - Teaches WHY picks are strong
   - Helps users become better bettors
   - Not just "what to bet" but "why to bet"

6. **Blockchain Verification**
   - On-chain proof anchoring
   - Tamper-evident records
   - Verifiable timestamps

7. **Professional-Grade Tools**
   - Advanced analytics
   - Performance tracking
   - ROI calculations
   - Historical data analysis

---

## Technical Highlights

### AI & Machine Learning

- **Proprietary Probability Models:** Custom algorithms for win probability calculation
- **Multi-Factor Analysis:** Considers team stats, injuries, weather, trends, matchups
- **Natural Language Processing:** OpenAI integration for plain-English explanations
- **Confidence Scoring:** Proprietary confidence metrics for each pick

### Data Processing

- **Real-Time Odds Aggregation:** Multiple sportsbook integration
- **Game Data Ingestion:** Automated fetching and processing
- **Historical Analysis:** Trend identification and pattern recognition
- **Performance Optimization:** Caching, rate limiting, efficient queries

### Security & Privacy

- **JWT Authentication:** Secure token-based auth
- **Password Hashing:** Bcrypt with 72-byte limit handling
- **Privacy-First Blockchain:** Only content hashes on-chain, no PII
- **Secure Payment Processing:** PCI-compliant payment providers

### Scalability

- **Distributed Architecture:** Separate frontend, backend, and worker services
- **Database Optimization:** PostgreSQL with proper indexing
- **Caching Strategy:** Redis for distributed cache
- **Background Jobs:** Async processing for heavy operations
- **Rate Limiting:** API protection and credit management

---

## User Experience

### Design Philosophy

- **Visual Identity:** Neon cyber-gorilla / sports betting / futuristic AI aesthetic
- **User-Friendly:** Professional-grade tools in an accessible format
- **Mobile-Responsive:** Works on all devices
- **Fast & Responsive:** Optimized for performance
- **Clear Visual Hierarchy:** Easy to understand and navigate

### Key User Flows

1. **Sign Up / Login**
   - Email-based authentication
   - Email verification
   - Password reset flow

2. **Generate AI Parlay**
   - Select sport(s)
   - Choose risk profile
   - Select number of legs (1-20)
   - Review AI-generated parlay with probabilities
   - Save or share parlay

3. **Build Custom Parlay**
   - Select games and picks
   - Get AI analysis
   - View win probability and expected value
   - Save parlay (triggers blockchain anchoring)

4. **View Game Analysis**
   - Browse upcoming games
   - View detailed matchup analysis
   - Read AI-generated narratives
   - Check injury reports and trends

5. **Track Performance**
   - View analytics dashboard
   - See win/loss statistics
   - Track ROI
   - Review historical parlays

---

## Integration Points for F3 AI Labs Website

### What to Highlight

1. **AI Technology**
   - Proprietary AI engine
   - Machine learning algorithms
   - Natural language processing
   - Real-time data analysis

2. **Product Portfolio**
   - Parlay Gorilla as flagship product
   - Demonstrates F3 AI Labs' capabilities
   - Live, production-ready application

3. **Technical Expertise**
   - Full-stack development
   - AI/ML integration
   - Blockchain integration
   - Payment processing
   - Scalable architecture

4. **Business Model**
   - Successful SaaS implementation
   - Multiple revenue streams
   - Freemium model execution

### Suggested Website Sections

1. **Product Showcase**
   - Parlay Gorilla as featured product
   - Key features and capabilities
   - Live demo or screenshots
   - Link to parlaygorilla.com

2. **Technology Stack**
   - AI/ML capabilities
   - Full-stack expertise
   - Modern tech stack
   - Scalable architecture

3. **Case Study / Portfolio**
   - Parlay Gorilla as case study
   - Technical challenges solved
   - Business outcomes
   - User testimonials (if available)

4. **Company Capabilities**
   - AI development
   - Web application development
   - Payment integration
   - Blockchain integration
   - Data analytics

---

## Current Status

### Production Status

- **Live:** Yes, fully operational
- **Domain:** https://www.parlaygorilla.com
- **Backend API:** https://api.parlaygorilla.com
- **Deployment:** Render (managed infrastructure)
- **Database:** Render PostgreSQL
- **Status:** Actively maintained and developed

### Recent Updates

- Password validation improvements (72-byte bcrypt limit handling)
- Production webhook configuration
- Environment variable documentation
- Payment provider integration (LemonSqueezy, Coinbase Commerce)
- Blockchain proof anchoring (IQ Labs / Solana)

---

## Key Metrics to Highlight (If Available)

- User base size
- Revenue metrics
- Growth rate
- Feature adoption
- User engagement
- Performance metrics

---

## Branding & Messaging

### Taglines

- "AI-Powered Parlay Builder for Smarter Sports Betting"
- "Stop Guessing. Start Winning."
- "Data-Driven Parlays. Better Results."
- "Professional Analytics. Accessible to Everyone."

### Key Messages

- **Transparency:** Show actual probabilities, not vague predictions
- **Intelligence:** AI-powered analysis, not random picks
- **Accessibility:** Professional tools for everyone
- **Education:** Learn WHY picks are strong, not just WHAT to bet

---

## Contact & Resources

- **Website:** https://www.parlaygorilla.com
- **Support:** contact@f3ai.dev
- **Company:** F3 AI Labs LLC
- **Product:** Parlay Gorilla™

---

## Additional Notes for Developer

### Technical Details to Include

1. **Architecture Diagram** (if creating one)
   - Frontend (Next.js)
   - Backend API (FastAPI)
   - Worker Service (Node.js)
   - Database (PostgreSQL)
   - Cache (Redis)
   - External APIs
   - Blockchain (Solana)

2. **Technology Stack**
   - Frontend: Next.js, TypeScript, Tailwind CSS
   - Backend: FastAPI, Python, PostgreSQL
   - Worker: Node.js, TypeScript
   - Infrastructure: Render
   - Blockchain: Solana, IQ Labs

3. **Key Integrations**
   - Payment: LemonSqueezy, Coinbase Commerce
   - Data: The Odds API, SportsRadar, ESPN
   - AI: OpenAI
   - Blockchain: IQ Labs / Solana
   - Email: Resend

### Design Considerations

- Modern, professional aesthetic
- Highlight AI/technology capabilities
- Showcase product features
- Include call-to-action to visit parlaygorilla.com
- Mobile-responsive design
- Fast loading times
- SEO-optimized

---

## Summary for Quick Reference

**Parlay Gorilla** is F3 AI Labs' flagship product - an AI-powered sports betting assistant that helps users build smarter parlay bets through data-driven insights. It combines proprietary AI technology, real-time odds integration, and blockchain verification to provide professional-grade analytics in an accessible web application. The platform serves both casual bettors and serious analysts, operating on a freemium SaaS model with premium subscriptions and credit packs. Built on modern tech stack (Next.js, FastAPI, PostgreSQL) and deployed on Render, Parlay Gorilla demonstrates F3 AI Labs' capabilities in AI/ML development, full-stack engineering, and scalable SaaS architecture.

---

**Last Updated:** December 2025  
**Document Version:** 1.0  
**For:** F3 AI Labs Website Development

