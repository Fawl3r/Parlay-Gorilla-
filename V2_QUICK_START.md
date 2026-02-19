# PARLAY GORILLA V2 - QUICK START GUIDE

## 🚀 GET STARTED IN 3 STEPS

### Step 1: Start Dev Server
```bash
cd frontend
npm run dev
```

### Step 2: Open V2 in Browser
```
http://localhost:3000/v2
```

### Step 3: Explore V2 UI
- Click "Build a Parlay" → Interactive builder
- Click "View Today's Picks" → Dashboard
- Use sidebar (desktop) or bottom tabs (mobile) to navigate

**That's it! V2 is running alongside production.**

---

## 🗺️ V2 ROUTES

### Landing
- **`/v2`** - Main landing page

### App
- **`/v2/app`** - Dashboard (stats + picks)
- **`/v2/app/builder`** - Build parlays interactively
- **`/v2/app/analytics`** - Performance metrics
- **`/v2/app/leaderboard`** - Rankings & comparisons
- **`/v2/app/settings`** - Account settings

---

## 📱 TEST ON MOBILE

1. Open DevTools (F12 or Cmd+Opt+I)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Select iPhone/Android device
4. Navigate to `localhost:3000/v2`
5. Verify bottom navigation appears

---

## 🎨 KEY FEATURES TO TEST

### Landing Page
- ✅ Hero section with 2 CTAs
- ✅ Horizontal scrolling picks
- ✅ 3-step "How It Works"
- ✅ Feature highlights
- ✅ Final CTA

### Builder Page
- ✅ Click picks to select/deselect
- ✅ Watch parlay slip update
- ✅ See confidence meter change
- ✅ Try stake input

### Dashboard
- ✅ Stats overview cards
- ✅ Today's AI picks
- ✅ Quick action buttons

### Analytics
- ✅ Performance summary
- ✅ Win rate by sport
- ✅ Recent bets list

### Leaderboard
- ✅ Daily/weekly/monthly tabs
- ✅ Top 3 medals
- ✅ AI vs community cards

### Settings
- ✅ Account inputs
- ✅ Toggle switches
- ✅ Dropdown selects

---

## 🔍 WHAT'S DIFFERENT IN V2

### Design
- **V1**: Lighter, more colorful
- **V2**: Dark sportsbook aesthetic (DraftKings-inspired)

### Navigation
- **V1**: Traditional header + sidebar
- **V2**: Sticky sidebar (desktop) + bottom tabs (mobile)

### Components
- **V1**: Standard cards
- **V2**: Glass morphism, odds chips, confidence meters

### Feel
- **V1**: General sports analytics
- **V2**: Professional sportsbook experience

---

## 🛡️ SAFETY REMINDERS

- ✅ V2 is completely isolated
- ✅ Original `/` route unchanged
- ✅ Original `/app` route unchanged
- ✅ No production data affected
- ✅ Uses mock data only

**Test V2 freely - production is safe.**

---

## 📂 WHERE IS EVERYTHING

```
V2 Code:
├── frontend/app/v2/              ← Routes
├── frontend/components/v2/       ← Components
└── frontend/lib/v2/              ← Utilities

V2 Docs:
├── V2_README.md                  ← Overview
├── V2_IMPLEMENTATION_SUMMARY.md  ← Details
├── V2_COMPONENT_GUIDE.md         ← Component docs
├── V2_FINAL_SUMMARY.md           ← Complete summary
└── V2_SAFETY_VERIFICATION.md     ← Safety proof
```

---

## 🗑️ HOW TO REMOVE V2

**If you want to delete V2**:

```bash
cd frontend
rm -rf app/v2 components/v2 lib/v2
cd ..
rm V2_*.md
```

**Done. No cleanup needed.**

---

## 🆘 TROUBLESHOOTING

### V2 page not loading?
- Check dev server is running (`npm run dev`)
- Check URL includes `/v2` prefix
- Check browser console for errors

### Styling looks wrong?
- Clear browser cache (Ctrl+Shift+R)
- Check Tailwind is compiling (`npm run dev` output)

### Navigation not working?
- Check viewport width (sidebar vs mobile nav)
- Resize window to test breakpoint

### Mock data not showing?
- Check browser console for import errors
- Verify `frontend/lib/v2/mock-data.ts` exists

---

## 💡 TIPS

1. **Mobile Testing**: Use DevTools device mode
2. **Desktop Testing**: Resize window to test breakpoints
3. **Builder**: Click picks multiple times to test toggle
4. **Leaderboard**: Switch tabs to see them work
5. **Production**: Visit `/` to verify it's unchanged

---

## 📞 NEXT STEPS

### For Testing
1. Preview all V2 pages
2. Test mobile responsive
3. Test desktop responsive
4. Gather user feedback

### For Approval
1. Review design with stakeholders
2. Test with real users
3. Collect metrics
4. Decide: keep or remove

### For Deployment
1. Replace mock data with APIs
2. Add authentication
3. Complete feature parity
4. Gradual rollout

---

## ✅ CHECKLIST

Before sharing with others:

- [ ] Dev server is running
- [ ] V2 landing page loads (`/v2`)
- [ ] All app pages work (`/v2/app/*`)
- [ ] Mobile nav works (<1024px)
- [ ] Desktop sidebar works (≥1024px)
- [ ] No console errors
- [ ] Production `/` route unchanged

**All green? Share the V2 link!**

---

## 🎉 YOU'RE READY

**V2 is live and ready for preview.**

Share this URL with your team:
```
http://localhost:3000/v2
```

Or for production preview (after deployment):
```
https://parlaygorilla.com/v2
```

**Happy testing!**
