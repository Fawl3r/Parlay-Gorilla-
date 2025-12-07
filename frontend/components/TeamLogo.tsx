"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface TeamLogoProps {
  teamName: string
  sport?: string // nfl, nba, nhl, mlb, ncaaf, ncaab, soccer
  size?: "sm" | "md" | "lg"
  className?: string
  showImage?: boolean
}

// ============================================================================
// NFL TEAMS
// ============================================================================
const NFL_TEAMS: Record<string, { abbr: string; primary: string; secondary: string }> = {
  "san francisco 49ers": { abbr: "sf", primary: "#AA0000", secondary: "#B3995D" },
  "49ers": { abbr: "sf", primary: "#AA0000", secondary: "#B3995D" },
  "chicago bears": { abbr: "chi", primary: "#0B162A", secondary: "#C83803" },
  "bears": { abbr: "chi", primary: "#0B162A", secondary: "#C83803" },
  "cincinnati bengals": { abbr: "cin", primary: "#FB4F14", secondary: "#000000" },
  "bengals": { abbr: "cin", primary: "#FB4F14", secondary: "#000000" },
  "buffalo bills": { abbr: "buf", primary: "#00338D", secondary: "#C60C30" },
  "bills": { abbr: "buf", primary: "#00338D", secondary: "#C60C30" },
  "denver broncos": { abbr: "den", primary: "#FB4F14", secondary: "#002244" },
  "broncos": { abbr: "den", primary: "#FB4F14", secondary: "#002244" },
  "cleveland browns": { abbr: "cle", primary: "#311D00", secondary: "#FF3C00" },
  "browns": { abbr: "cle", primary: "#311D00", secondary: "#FF3C00" },
  "tampa bay buccaneers": { abbr: "tb", primary: "#D50A0A", secondary: "#FF7900" },
  "buccaneers": { abbr: "tb", primary: "#D50A0A", secondary: "#FF7900" },
  "arizona cardinals": { abbr: "ari", primary: "#97233F", secondary: "#000000" },
  "cardinals": { abbr: "ari", primary: "#97233F", secondary: "#000000" },
  "los angeles chargers": { abbr: "lac", primary: "#0080C6", secondary: "#FFC20E" },
  "chargers": { abbr: "lac", primary: "#0080C6", secondary: "#FFC20E" },
  "kansas city chiefs": { abbr: "kc", primary: "#E31837", secondary: "#FFB81C" },
  "chiefs": { abbr: "kc", primary: "#E31837", secondary: "#FFB81C" },
  "indianapolis colts": { abbr: "ind", primary: "#002C5F", secondary: "#A2AAAD" },
  "colts": { abbr: "ind", primary: "#002C5F", secondary: "#A2AAAD" },
  "dallas cowboys": { abbr: "dal", primary: "#003594", secondary: "#869397" },
  "cowboys": { abbr: "dal", primary: "#003594", secondary: "#869397" },
  "miami dolphins": { abbr: "mia", primary: "#008E97", secondary: "#FC4C02" },
  "dolphins": { abbr: "mia", primary: "#008E97", secondary: "#FC4C02" },
  "philadelphia eagles": { abbr: "phi", primary: "#004C54", secondary: "#A5ACAF" },
  "eagles": { abbr: "phi", primary: "#004C54", secondary: "#A5ACAF" },
  "atlanta falcons": { abbr: "atl", primary: "#A71930", secondary: "#000000" },
  "falcons": { abbr: "atl", primary: "#A71930", secondary: "#000000" },
  "new york giants": { abbr: "nyg", primary: "#0B2265", secondary: "#A71930" },
  "giants": { abbr: "nyg", primary: "#0B2265", secondary: "#A71930" },
  "jacksonville jaguars": { abbr: "jax", primary: "#006778", secondary: "#9F792C" },
  "jaguars": { abbr: "jax", primary: "#006778", secondary: "#9F792C" },
  "new york jets": { abbr: "nyj", primary: "#125740", secondary: "#000000" },
  "jets": { abbr: "nyj", primary: "#125740", secondary: "#000000" },
  "detroit lions": { abbr: "det", primary: "#0076B6", secondary: "#B0B7BC" },
  "lions": { abbr: "det", primary: "#0076B6", secondary: "#B0B7BC" },
  "green bay packers": { abbr: "gb", primary: "#203731", secondary: "#FFB612" },
  "packers": { abbr: "gb", primary: "#203731", secondary: "#FFB612" },
  "carolina panthers": { abbr: "car", primary: "#0085CA", secondary: "#101820" },
  "panthers": { abbr: "car", primary: "#0085CA", secondary: "#101820" },
  "new england patriots": { abbr: "ne", primary: "#002244", secondary: "#C60C30" },
  "patriots": { abbr: "ne", primary: "#002244", secondary: "#C60C30" },
  "las vegas raiders": { abbr: "lv", primary: "#000000", secondary: "#A5ACAF" },
  "raiders": { abbr: "lv", primary: "#000000", secondary: "#A5ACAF" },
  "los angeles rams": { abbr: "lar", primary: "#003594", secondary: "#FFA300" },
  "rams": { abbr: "lar", primary: "#003594", secondary: "#FFA300" },
  "baltimore ravens": { abbr: "bal", primary: "#241773", secondary: "#9E7C0C" },
  "ravens": { abbr: "bal", primary: "#241773", secondary: "#9E7C0C" },
  "new orleans saints": { abbr: "no", primary: "#D3BC8D", secondary: "#101820" },
  "saints": { abbr: "no", primary: "#D3BC8D", secondary: "#101820" },
  "seattle seahawks": { abbr: "sea", primary: "#002244", secondary: "#69BE28" },
  "seahawks": { abbr: "sea", primary: "#002244", secondary: "#69BE28" },
  "pittsburgh steelers": { abbr: "pit", primary: "#000000", secondary: "#FFB612" },
  "steelers": { abbr: "pit", primary: "#000000", secondary: "#FFB612" },
  "houston texans": { abbr: "hou", primary: "#03202F", secondary: "#A71930" },
  "texans": { abbr: "hou", primary: "#03202F", secondary: "#A71930" },
  "tennessee titans": { abbr: "ten", primary: "#0C2340", secondary: "#4B92DB" },
  "titans": { abbr: "ten", primary: "#0C2340", secondary: "#4B92DB" },
  "minnesota vikings": { abbr: "min", primary: "#4F2683", secondary: "#FFC62F" },
  "vikings": { abbr: "min", primary: "#4F2683", secondary: "#FFC62F" },
  "washington commanders": { abbr: "wsh", primary: "#5A1414", secondary: "#FFB612" },
  "commanders": { abbr: "wsh", primary: "#5A1414", secondary: "#FFB612" },
}

// ============================================================================
// NBA TEAMS
// ============================================================================
const NBA_TEAMS: Record<string, { abbr: string; primary: string; secondary: string }> = {
  "atlanta hawks": { abbr: "atl", primary: "#E03A3E", secondary: "#C1D32F" },
  "hawks": { abbr: "atl", primary: "#E03A3E", secondary: "#C1D32F" },
  "boston celtics": { abbr: "bos", primary: "#007A33", secondary: "#BA9653" },
  "celtics": { abbr: "bos", primary: "#007A33", secondary: "#BA9653" },
  "brooklyn nets": { abbr: "bkn", primary: "#000000", secondary: "#FFFFFF" },
  "nets": { abbr: "bkn", primary: "#000000", secondary: "#FFFFFF" },
  "charlotte hornets": { abbr: "cha", primary: "#1D1160", secondary: "#00788C" },
  "hornets": { abbr: "cha", primary: "#1D1160", secondary: "#00788C" },
  "chicago bulls": { abbr: "chi", primary: "#CE1141", secondary: "#000000" },
  "bulls": { abbr: "chi", primary: "#CE1141", secondary: "#000000" },
  "cleveland cavaliers": { abbr: "cle", primary: "#860038", secondary: "#FDBB30" },
  "cavaliers": { abbr: "cle", primary: "#860038", secondary: "#FDBB30" },
  "cavs": { abbr: "cle", primary: "#860038", secondary: "#FDBB30" },
  "dallas mavericks": { abbr: "dal", primary: "#00538C", secondary: "#002B5C" },
  "mavericks": { abbr: "dal", primary: "#00538C", secondary: "#002B5C" },
  "mavs": { abbr: "dal", primary: "#00538C", secondary: "#002B5C" },
  "denver nuggets": { abbr: "den", primary: "#0E2240", secondary: "#FEC524" },
  "nuggets": { abbr: "den", primary: "#0E2240", secondary: "#FEC524" },
  "detroit pistons": { abbr: "det", primary: "#C8102E", secondary: "#1D42BA" },
  "pistons": { abbr: "det", primary: "#C8102E", secondary: "#1D42BA" },
  "golden state warriors": { abbr: "gs", primary: "#1D428A", secondary: "#FFC72C" },
  "warriors": { abbr: "gs", primary: "#1D428A", secondary: "#FFC72C" },
  "houston rockets": { abbr: "hou", primary: "#CE1141", secondary: "#000000" },
  "rockets": { abbr: "hou", primary: "#CE1141", secondary: "#000000" },
  "indiana pacers": { abbr: "ind", primary: "#002D62", secondary: "#FDBB30" },
  "pacers": { abbr: "ind", primary: "#002D62", secondary: "#FDBB30" },
  "los angeles clippers": { abbr: "lac", primary: "#C8102E", secondary: "#1D428A" },
  "clippers": { abbr: "lac", primary: "#C8102E", secondary: "#1D428A" },
  "la clippers": { abbr: "lac", primary: "#C8102E", secondary: "#1D428A" },
  "los angeles lakers": { abbr: "lal", primary: "#552583", secondary: "#FDB927" },
  "lakers": { abbr: "lal", primary: "#552583", secondary: "#FDB927" },
  "la lakers": { abbr: "lal", primary: "#552583", secondary: "#FDB927" },
  "memphis grizzlies": { abbr: "mem", primary: "#5D76A9", secondary: "#12173F" },
  "grizzlies": { abbr: "mem", primary: "#5D76A9", secondary: "#12173F" },
  "miami heat": { abbr: "mia", primary: "#98002E", secondary: "#F9A01B" },
  "heat": { abbr: "mia", primary: "#98002E", secondary: "#F9A01B" },
  "milwaukee bucks": { abbr: "mil", primary: "#00471B", secondary: "#EEE1C6" },
  "bucks": { abbr: "mil", primary: "#00471B", secondary: "#EEE1C6" },
  "minnesota timberwolves": { abbr: "min", primary: "#0C2340", secondary: "#236192" },
  "timberwolves": { abbr: "min", primary: "#0C2340", secondary: "#236192" },
  "wolves": { abbr: "min", primary: "#0C2340", secondary: "#236192" },
  "new orleans pelicans": { abbr: "no", primary: "#0C2340", secondary: "#C8102E" },
  "pelicans": { abbr: "no", primary: "#0C2340", secondary: "#C8102E" },
  "new york knicks": { abbr: "ny", primary: "#006BB6", secondary: "#F58426" },
  "knicks": { abbr: "ny", primary: "#006BB6", secondary: "#F58426" },
  "oklahoma city thunder": { abbr: "okc", primary: "#007AC1", secondary: "#EF3B24" },
  "thunder": { abbr: "okc", primary: "#007AC1", secondary: "#EF3B24" },
  "orlando magic": { abbr: "orl", primary: "#0077C0", secondary: "#C4CED4" },
  "magic": { abbr: "orl", primary: "#0077C0", secondary: "#C4CED4" },
  "philadelphia 76ers": { abbr: "phi", primary: "#006BB6", secondary: "#ED174C" },
  "76ers": { abbr: "phi", primary: "#006BB6", secondary: "#ED174C" },
  "sixers": { abbr: "phi", primary: "#006BB6", secondary: "#ED174C" },
  "phoenix suns": { abbr: "phx", primary: "#1D1160", secondary: "#E56020" },
  "suns": { abbr: "phx", primary: "#1D1160", secondary: "#E56020" },
  "portland trail blazers": { abbr: "por", primary: "#E03A3E", secondary: "#000000" },
  "trail blazers": { abbr: "por", primary: "#E03A3E", secondary: "#000000" },
  "blazers": { abbr: "por", primary: "#E03A3E", secondary: "#000000" },
  "sacramento kings": { abbr: "sac", primary: "#5A2D81", secondary: "#63727A" },
  "kings": { abbr: "sac", primary: "#5A2D81", secondary: "#63727A" },
  "san antonio spurs": { abbr: "sa", primary: "#C4CED4", secondary: "#000000" },
  "spurs": { abbr: "sa", primary: "#C4CED4", secondary: "#000000" },
  "toronto raptors": { abbr: "tor", primary: "#CE1141", secondary: "#000000" },
  "raptors": { abbr: "tor", primary: "#CE1141", secondary: "#000000" },
  "utah jazz": { abbr: "utah", primary: "#002B5C", secondary: "#00471B" },
  "jazz": { abbr: "utah", primary: "#002B5C", secondary: "#00471B" },
  "washington wizards": { abbr: "wsh", primary: "#002B5C", secondary: "#E31837" },
  "wizards": { abbr: "wsh", primary: "#002B5C", secondary: "#E31837" },
}

// ============================================================================
// NHL TEAMS
// ============================================================================
const NHL_TEAMS: Record<string, { abbr: string; primary: string; secondary: string }> = {
  "anaheim ducks": { abbr: "ana", primary: "#F47A38", secondary: "#B9975B" },
  "ducks": { abbr: "ana", primary: "#F47A38", secondary: "#B9975B" },
  "arizona coyotes": { abbr: "ari", primary: "#8C2633", secondary: "#E2D6B5" },
  "coyotes": { abbr: "ari", primary: "#8C2633", secondary: "#E2D6B5" },
  "boston bruins": { abbr: "bos", primary: "#FFB81C", secondary: "#000000" },
  "bruins": { abbr: "bos", primary: "#FFB81C", secondary: "#000000" },
  "buffalo sabres": { abbr: "buf", primary: "#002654", secondary: "#FCB514" },
  "sabres": { abbr: "buf", primary: "#002654", secondary: "#FCB514" },
  "calgary flames": { abbr: "cgy", primary: "#C8102E", secondary: "#F1BE48" },
  "flames": { abbr: "cgy", primary: "#C8102E", secondary: "#F1BE48" },
  "carolina hurricanes": { abbr: "car", primary: "#CC0000", secondary: "#000000" },
  "hurricanes": { abbr: "car", primary: "#CC0000", secondary: "#000000" },
  "chicago blackhawks": { abbr: "chi", primary: "#CF0A2C", secondary: "#000000" },
  "blackhawks": { abbr: "chi", primary: "#CF0A2C", secondary: "#000000" },
  "colorado avalanche": { abbr: "col", primary: "#6F263D", secondary: "#236192" },
  "avalanche": { abbr: "col", primary: "#6F263D", secondary: "#236192" },
  "columbus blue jackets": { abbr: "cbj", primary: "#002654", secondary: "#CE1126" },
  "blue jackets": { abbr: "cbj", primary: "#002654", secondary: "#CE1126" },
  "dallas stars": { abbr: "dal", primary: "#006847", secondary: "#8F8F8C" },
  "stars": { abbr: "dal", primary: "#006847", secondary: "#8F8F8C" },
  "detroit red wings": { abbr: "det", primary: "#CE1126", secondary: "#FFFFFF" },
  "red wings": { abbr: "det", primary: "#CE1126", secondary: "#FFFFFF" },
  "edmonton oilers": { abbr: "edm", primary: "#041E42", secondary: "#FF4C00" },
  "oilers": { abbr: "edm", primary: "#041E42", secondary: "#FF4C00" },
  "florida panthers": { abbr: "fla", primary: "#041E42", secondary: "#C8102E" },
  "panthers": { abbr: "fla", primary: "#041E42", secondary: "#C8102E" },
  "los angeles kings": { abbr: "la", primary: "#111111", secondary: "#A2AAAD" },
  "kings": { abbr: "la", primary: "#111111", secondary: "#A2AAAD" },
  "minnesota wild": { abbr: "min", primary: "#154734", secondary: "#A6192E" },
  "wild": { abbr: "min", primary: "#154734", secondary: "#A6192E" },
  "montreal canadiens": { abbr: "mtl", primary: "#AF1E2D", secondary: "#192168" },
  "canadiens": { abbr: "mtl", primary: "#AF1E2D", secondary: "#192168" },
  "nashville predators": { abbr: "nsh", primary: "#FFB81C", secondary: "#041E42" },
  "predators": { abbr: "nsh", primary: "#FFB81C", secondary: "#041E42" },
  "new jersey devils": { abbr: "nj", primary: "#CE1126", secondary: "#000000" },
  "devils": { abbr: "nj", primary: "#CE1126", secondary: "#000000" },
  "new york islanders": { abbr: "nyi", primary: "#00539B", secondary: "#F47D30" },
  "islanders": { abbr: "nyi", primary: "#00539B", secondary: "#F47D30" },
  "new york rangers": { abbr: "nyr", primary: "#0038A8", secondary: "#CE1126" },
  "rangers": { abbr: "nyr", primary: "#0038A8", secondary: "#CE1126" },
  "ottawa senators": { abbr: "ott", primary: "#C52032", secondary: "#C2912C" },
  "senators": { abbr: "ott", primary: "#C52032", secondary: "#C2912C" },
  "philadelphia flyers": { abbr: "phi", primary: "#F74902", secondary: "#000000" },
  "flyers": { abbr: "phi", primary: "#F74902", secondary: "#000000" },
  "pittsburgh penguins": { abbr: "pit", primary: "#000000", secondary: "#FCB514" },
  "penguins": { abbr: "pit", primary: "#000000", secondary: "#FCB514" },
  "san jose sharks": { abbr: "sj", primary: "#006D75", secondary: "#EA7200" },
  "sharks": { abbr: "sj", primary: "#006D75", secondary: "#EA7200" },
  "seattle kraken": { abbr: "sea", primary: "#001628", secondary: "#99D9D9" },
  "kraken": { abbr: "sea", primary: "#001628", secondary: "#99D9D9" },
  "st. louis blues": { abbr: "stl", primary: "#002F87", secondary: "#FCB514" },
  "st louis blues": { abbr: "stl", primary: "#002F87", secondary: "#FCB514" },
  "saint louis blues": { abbr: "stl", primary: "#002F87", secondary: "#FCB514" },
  "blues": { abbr: "stl", primary: "#002F87", secondary: "#FCB514" },
  "tampa bay lightning": { abbr: "tb", primary: "#002868", secondary: "#FFFFFF" },
  "lightning": { abbr: "tb", primary: "#002868", secondary: "#FFFFFF" },
  "toronto maple leafs": { abbr: "tor", primary: "#00205B", secondary: "#FFFFFF" },
  "maple leafs": { abbr: "tor", primary: "#00205B", secondary: "#FFFFFF" },
  "utah hockey club": { abbr: "utah", primary: "#6CACE4", secondary: "#010101" },
  "utah mammoths": { abbr: "utah", primary: "#6CACE4", secondary: "#010101" },
  "utah mammoth": { abbr: "utah", primary: "#6CACE4", secondary: "#010101" },
  "utah hc": { abbr: "utah", primary: "#6CACE4", secondary: "#010101" },
  "vancouver canucks": { abbr: "van", primary: "#00205B", secondary: "#00843D" },
  "canucks": { abbr: "van", primary: "#00205B", secondary: "#00843D" },
  "vegas golden knights": { abbr: "vgk", primary: "#B4975A", secondary: "#333F42" },
  "golden knights": { abbr: "vgk", primary: "#B4975A", secondary: "#333F42" },
  "washington capitals": { abbr: "wsh", primary: "#C8102E", secondary: "#041E42" },
  "capitals": { abbr: "wsh", primary: "#C8102E", secondary: "#041E42" },
  "winnipeg jets": { abbr: "wpg", primary: "#041E42", secondary: "#004C97" },
  "jets": { abbr: "wpg", primary: "#041E42", secondary: "#004C97" },
}

// ============================================================================
// MLB TEAMS
// ============================================================================
const MLB_TEAMS: Record<string, { abbr: string; primary: string; secondary: string }> = {
  "arizona diamondbacks": { abbr: "ari", primary: "#A71930", secondary: "#E3D4AD" },
  "diamondbacks": { abbr: "ari", primary: "#A71930", secondary: "#E3D4AD" },
  "d-backs": { abbr: "ari", primary: "#A71930", secondary: "#E3D4AD" },
  "atlanta braves": { abbr: "atl", primary: "#CE1141", secondary: "#13274F" },
  "braves": { abbr: "atl", primary: "#CE1141", secondary: "#13274F" },
  "baltimore orioles": { abbr: "bal", primary: "#DF4601", secondary: "#000000" },
  "orioles": { abbr: "bal", primary: "#DF4601", secondary: "#000000" },
  "boston red sox": { abbr: "bos", primary: "#BD3039", secondary: "#0C2340" },
  "red sox": { abbr: "bos", primary: "#BD3039", secondary: "#0C2340" },
  "chicago cubs": { abbr: "chc", primary: "#0E3386", secondary: "#CC3433" },
  "cubs": { abbr: "chc", primary: "#0E3386", secondary: "#CC3433" },
  "chicago white sox": { abbr: "chw", primary: "#27251F", secondary: "#C4CED4" },
  "white sox": { abbr: "chw", primary: "#27251F", secondary: "#C4CED4" },
  "cincinnati reds": { abbr: "cin", primary: "#C6011F", secondary: "#000000" },
  "reds": { abbr: "cin", primary: "#C6011F", secondary: "#000000" },
  "cleveland guardians": { abbr: "cle", primary: "#00385D", secondary: "#E50022" },
  "guardians": { abbr: "cle", primary: "#00385D", secondary: "#E50022" },
  "colorado rockies": { abbr: "col", primary: "#33006F", secondary: "#C4CED4" },
  "rockies": { abbr: "col", primary: "#33006F", secondary: "#C4CED4" },
  "detroit tigers": { abbr: "det", primary: "#0C2340", secondary: "#FA4616" },
  "tigers": { abbr: "det", primary: "#0C2340", secondary: "#FA4616" },
  "houston astros": { abbr: "hou", primary: "#002D62", secondary: "#EB6E1F" },
  "astros": { abbr: "hou", primary: "#002D62", secondary: "#EB6E1F" },
  "kansas city royals": { abbr: "kc", primary: "#004687", secondary: "#BD9B60" },
  "royals": { abbr: "kc", primary: "#004687", secondary: "#BD9B60" },
  "los angeles angels": { abbr: "laa", primary: "#BA0021", secondary: "#003263" },
  "angels": { abbr: "laa", primary: "#BA0021", secondary: "#003263" },
  "los angeles dodgers": { abbr: "lad", primary: "#005A9C", secondary: "#EF3E42" },
  "dodgers": { abbr: "lad", primary: "#005A9C", secondary: "#EF3E42" },
  "miami marlins": { abbr: "mia", primary: "#00A3E0", secondary: "#EF3340" },
  "marlins": { abbr: "mia", primary: "#00A3E0", secondary: "#EF3340" },
  "milwaukee brewers": { abbr: "mil", primary: "#12284B", secondary: "#B6922E" },
  "brewers": { abbr: "mil", primary: "#12284B", secondary: "#B6922E" },
  "minnesota twins": { abbr: "min", primary: "#002B5C", secondary: "#D31145" },
  "twins": { abbr: "min", primary: "#002B5C", secondary: "#D31145" },
  "new york mets": { abbr: "nym", primary: "#002D72", secondary: "#FF5910" },
  "mets": { abbr: "nym", primary: "#002D72", secondary: "#FF5910" },
  "new york yankees": { abbr: "nyy", primary: "#003087", secondary: "#E4002C" },
  "yankees": { abbr: "nyy", primary: "#003087", secondary: "#E4002C" },
  "oakland athletics": { abbr: "oak", primary: "#003831", secondary: "#EFB21E" },
  "athletics": { abbr: "oak", primary: "#003831", secondary: "#EFB21E" },
  "a's": { abbr: "oak", primary: "#003831", secondary: "#EFB21E" },
  "philadelphia phillies": { abbr: "phi", primary: "#E81828", secondary: "#002D72" },
  "phillies": { abbr: "phi", primary: "#E81828", secondary: "#002D72" },
  "pittsburgh pirates": { abbr: "pit", primary: "#27251F", secondary: "#FDB827" },
  "pirates": { abbr: "pit", primary: "#27251F", secondary: "#FDB827" },
  "san diego padres": { abbr: "sd", primary: "#2F241D", secondary: "#FFC425" },
  "padres": { abbr: "sd", primary: "#2F241D", secondary: "#FFC425" },
  "san francisco giants": { abbr: "sf", primary: "#FD5A1E", secondary: "#27251F" },
  "giants": { abbr: "sf", primary: "#FD5A1E", secondary: "#27251F" },
  "seattle mariners": { abbr: "sea", primary: "#0C2C56", secondary: "#005C5C" },
  "mariners": { abbr: "sea", primary: "#0C2C56", secondary: "#005C5C" },
  "st. louis cardinals": { abbr: "stl", primary: "#C41E3A", secondary: "#0C2340" },
  "cardinals": { abbr: "stl", primary: "#C41E3A", secondary: "#0C2340" },
  "tampa bay rays": { abbr: "tb", primary: "#092C5C", secondary: "#8FBCE6" },
  "rays": { abbr: "tb", primary: "#092C5C", secondary: "#8FBCE6" },
  "texas rangers": { abbr: "tex", primary: "#003278", secondary: "#C0111F" },
  "rangers": { abbr: "tex", primary: "#003278", secondary: "#C0111F" },
  "toronto blue jays": { abbr: "tor", primary: "#134A8E", secondary: "#1D2D5C" },
  "blue jays": { abbr: "tor", primary: "#134A8E", secondary: "#1D2D5C" },
  "washington nationals": { abbr: "wsh", primary: "#AB0003", secondary: "#14225A" },
  "nationals": { abbr: "wsh", primary: "#AB0003", secondary: "#14225A" },
}

// ============================================================================
// COLLEGE FOOTBALL TEAMS (Top Programs) - Using ESPN Team IDs
// ============================================================================
const NCAAF_TEAMS: Record<string, { abbr: string; id: string; primary: string; secondary: string }> = {
  "alabama crimson tide": { abbr: "ALA", id: "333", primary: "#9E1B32", secondary: "#828A8F" },
  "alabama": { abbr: "ALA", id: "333", primary: "#9E1B32", secondary: "#828A8F" },
  "ohio state buckeyes": { abbr: "OSU", id: "194", primary: "#BB0000", secondary: "#666666" },
  "ohio state": { abbr: "OSU", id: "194", primary: "#BB0000", secondary: "#666666" },
  "georgia bulldogs": { abbr: "UGA", id: "61", primary: "#BA0C2F", secondary: "#000000" },
  "georgia": { abbr: "UGA", id: "61", primary: "#BA0C2F", secondary: "#000000" },
  "michigan wolverines": { abbr: "MICH", id: "130", primary: "#00274C", secondary: "#FFCB05" },
  "michigan": { abbr: "MICH", id: "130", primary: "#00274C", secondary: "#FFCB05" },
  "clemson tigers": { abbr: "CLEM", id: "228", primary: "#F56600", secondary: "#522D80" },
  "clemson": { abbr: "CLEM", id: "228", primary: "#F56600", secondary: "#522D80" },
  "texas longhorns": { abbr: "TEX", id: "251", primary: "#BF5700", secondary: "#FFFFFF" },
  "texas": { abbr: "TEX", id: "251", primary: "#BF5700", secondary: "#FFFFFF" },
  "usc trojans": { abbr: "USC", id: "30", primary: "#990000", secondary: "#FFC72C" },
  "usc": { abbr: "USC", id: "30", primary: "#990000", secondary: "#FFC72C" },
  "southern california": { abbr: "USC", id: "30", primary: "#990000", secondary: "#FFC72C" },
  "notre dame fighting irish": { abbr: "ND", id: "87", primary: "#0C2340", secondary: "#C99700" },
  "notre dame": { abbr: "ND", id: "87", primary: "#0C2340", secondary: "#C99700" },
  "lsu tigers": { abbr: "LSU", id: "99", primary: "#461D7C", secondary: "#FDD023" },
  "lsu": { abbr: "LSU", id: "99", primary: "#461D7C", secondary: "#FDD023" },
  "oklahoma sooners": { abbr: "OU", id: "201", primary: "#841617", secondary: "#FDF9D8" },
  "oklahoma": { abbr: "OU", id: "201", primary: "#841617", secondary: "#FDF9D8" },
  "penn state nittany lions": { abbr: "PSU", id: "213", primary: "#041E42", secondary: "#FFFFFF" },
  "penn state": { abbr: "PSU", id: "213", primary: "#041E42", secondary: "#FFFFFF" },
  "florida gators": { abbr: "FLA", id: "57", primary: "#0021A5", secondary: "#FA4616" },
  "florida": { abbr: "FLA", id: "57", primary: "#0021A5", secondary: "#FA4616" },
  "oregon ducks": { abbr: "ORE", id: "2483", primary: "#154733", secondary: "#FEE123" },
  "oregon": { abbr: "ORE", id: "2483", primary: "#154733", secondary: "#FEE123" },
  "auburn tigers": { abbr: "AUB", id: "2", primary: "#0C2340", secondary: "#E87722" },
  "auburn": { abbr: "AUB", id: "2", primary: "#0C2340", secondary: "#E87722" },
  "tennessee volunteers": { abbr: "TENN", id: "2633", primary: "#FF8200", secondary: "#FFFFFF" },
  "tennessee": { abbr: "TENN", id: "2633", primary: "#FF8200", secondary: "#FFFFFF" },
  "miami hurricanes": { abbr: "MIA", id: "2390", primary: "#F47321", secondary: "#005030" },
  "miami (fl)": { abbr: "MIA", id: "2390", primary: "#F47321", secondary: "#005030" },
  "texas a&m aggies": { abbr: "TAMU", id: "245", primary: "#500000", secondary: "#FFFFFF" },
  "texas a&m": { abbr: "TAMU", id: "245", primary: "#500000", secondary: "#FFFFFF" },
  "wisconsin badgers": { abbr: "WIS", id: "275", primary: "#C5050C", secondary: "#FFFFFF" },
  "wisconsin": { abbr: "WIS", id: "275", primary: "#C5050C", secondary: "#FFFFFF" },
  "michigan state spartans": { abbr: "MSU", id: "127", primary: "#18453B", secondary: "#FFFFFF" },
  "michigan state": { abbr: "MSU", id: "127", primary: "#18453B", secondary: "#FFFFFF" },
  "florida state seminoles": { abbr: "FSU", id: "52", primary: "#782F40", secondary: "#CEB888" },
  "florida state": { abbr: "FSU", id: "52", primary: "#782F40", secondary: "#CEB888" },
  "iowa hawkeyes": { abbr: "IOWA", id: "2294", primary: "#FFCD00", secondary: "#000000" },
  "iowa": { abbr: "IOWA", id: "2294", primary: "#FFCD00", secondary: "#000000" },
  "washington huskies": { abbr: "WASH", id: "264", primary: "#4B2E83", secondary: "#B7A57A" },
  "washington": { abbr: "WASH", id: "264", primary: "#4B2E83", secondary: "#B7A57A" },
  "colorado buffaloes": { abbr: "COLO", id: "38", primary: "#CFB87C", secondary: "#000000" },
  "colorado": { abbr: "COLO", id: "38", primary: "#CFB87C", secondary: "#000000" },
  "ole miss rebels": { abbr: "MISS", id: "145", primary: "#CE1126", secondary: "#14213D" },
  "ole miss": { abbr: "MISS", id: "145", primary: "#CE1126", secondary: "#14213D" },
  "mississippi": { abbr: "MISS", id: "145", primary: "#CE1126", secondary: "#14213D" },
  "arkansas razorbacks": { abbr: "ARK", id: "8", primary: "#9D2235", secondary: "#FFFFFF" },
  "arkansas": { abbr: "ARK", id: "8", primary: "#9D2235", secondary: "#FFFFFF" },
  "baylor bears": { abbr: "BAY", id: "239", primary: "#154734", secondary: "#FFB81C" },
  "baylor": { abbr: "BAY", id: "239", primary: "#154734", secondary: "#FFB81C" },
  "kentucky wildcats": { abbr: "UK", id: "96", primary: "#0033A0", secondary: "#FFFFFF" },
  "utah utes": { abbr: "UTAH", id: "254", primary: "#CC0000", secondary: "#000000" },
  "utah": { abbr: "UTAH", id: "254", primary: "#CC0000", secondary: "#000000" },
  "nc state wolfpack": { abbr: "NCST", id: "152", primary: "#CC0000", secondary: "#000000" },
  "nc state": { abbr: "NCST", id: "152", primary: "#CC0000", secondary: "#000000" },
  "north carolina state": { abbr: "NCST", id: "152", primary: "#CC0000", secondary: "#000000" },
  "north carolina tar heels": { abbr: "UNC", id: "153", primary: "#7BAFD4", secondary: "#FFFFFF" },
  "north carolina": { abbr: "UNC", id: "153", primary: "#7BAFD4", secondary: "#FFFFFF" },
  "unc": { abbr: "UNC", id: "153", primary: "#7BAFD4", secondary: "#FFFFFF" },
  "virginia tech hokies": { abbr: "VT", id: "259", primary: "#630031", secondary: "#CF4520" },
  "virginia tech": { abbr: "VT", id: "259", primary: "#630031", secondary: "#CF4520" },
  "west virginia mountaineers": { abbr: "WVU", id: "277", primary: "#002855", secondary: "#EAAA00" },
  "west virginia": { abbr: "WVU", id: "277", primary: "#002855", secondary: "#EAAA00" },
  "pittsburgh panthers": { abbr: "PITT", id: "221", primary: "#003594", secondary: "#FFB81C" },
  "pittsburgh": { abbr: "PITT", id: "221", primary: "#003594", secondary: "#FFB81C" },
  "pitt": { abbr: "PITT", id: "221", primary: "#003594", secondary: "#FFB81C" },
  "louisville cardinals": { abbr: "LOU", id: "97", primary: "#AD0000", secondary: "#000000" },
  "louisville": { abbr: "LOU", id: "97", primary: "#AD0000", secondary: "#000000" },
  "arizona state sun devils": { abbr: "ASU", id: "9", primary: "#8C1D40", secondary: "#FFC627" },
  "arizona state": { abbr: "ASU", id: "9", primary: "#8C1D40", secondary: "#FFC627" },
  "arizona wildcats": { abbr: "ARIZ", id: "12", primary: "#CC0033", secondary: "#003366" },
  "arizona": { abbr: "ARIZ", id: "12", primary: "#CC0033", secondary: "#003366" },
  "stanford cardinal": { abbr: "STAN", id: "24", primary: "#8C1515", secondary: "#FFFFFF" },
  "stanford": { abbr: "STAN", id: "24", primary: "#8C1515", secondary: "#FFFFFF" },
  "ucla bruins": { abbr: "UCLA", id: "26", primary: "#2D68C4", secondary: "#F2A900" },
  "ucla": { abbr: "UCLA", id: "26", primary: "#2D68C4", secondary: "#F2A900" },
  "cal bears": { abbr: "CAL", id: "25", primary: "#003262", secondary: "#FDB515" },
  "california": { abbr: "CAL", id: "25", primary: "#003262", secondary: "#FDB515" },
  "cal": { abbr: "CAL", id: "25", primary: "#003262", secondary: "#FDB515" },
  // More Teams
  "illinois fighting illini": { abbr: "ILL", id: "356", primary: "#E84A27", secondary: "#13294B" },
  "illinois": { abbr: "ILL", id: "356", primary: "#E84A27", secondary: "#13294B" },
  "minnesota golden gophers": { abbr: "MINN", id: "135", primary: "#7A0019", secondary: "#FFCC33" },
  "minnesota": { abbr: "MINN", id: "135", primary: "#7A0019", secondary: "#FFCC33" },
  "purdue boilermakers": { abbr: "PUR", id: "2509", primary: "#CEB888", secondary: "#000000" },
  "purdue": { abbr: "PUR", id: "2509", primary: "#CEB888", secondary: "#000000" },
  "indiana hoosiers": { abbr: "IND", id: "84", primary: "#990000", secondary: "#FFFFFF" },
  "indiana": { abbr: "IND", id: "84", primary: "#990000", secondary: "#FFFFFF" },
  "nebraska cornhuskers": { abbr: "NEB", id: "158", primary: "#E41C38", secondary: "#FFFFFF" },
  "nebraska": { abbr: "NEB", id: "158", primary: "#E41C38", secondary: "#FFFFFF" },
  "northwestern wildcats": { abbr: "NW", id: "77", primary: "#4E2A84", secondary: "#FFFFFF" },
  "northwestern": { abbr: "NW", id: "77", primary: "#4E2A84", secondary: "#FFFFFF" },
  "rutgers scarlet knights": { abbr: "RUTG", id: "164", primary: "#CC0033", secondary: "#5F6A72" },
  "rutgers": { abbr: "RUTG", id: "164", primary: "#CC0033", secondary: "#5F6A72" },
  "maryland terrapins": { abbr: "MD", id: "120", primary: "#E03A3E", secondary: "#FFD520" },
  "maryland": { abbr: "MD", id: "120", primary: "#E03A3E", secondary: "#FFD520" },
  "kansas state wildcats": { abbr: "KSU", id: "2306", primary: "#512888", secondary: "#FFFFFF" },
  "kansas state": { abbr: "KSU", id: "2306", primary: "#512888", secondary: "#FFFFFF" },
  "k-state": { abbr: "KSU", id: "2306", primary: "#512888", secondary: "#FFFFFF" },
  "kansas jayhawks": { abbr: "KU", id: "2305", primary: "#0051BA", secondary: "#E8000D" },
  "kansas": { abbr: "KU", id: "2305", primary: "#0051BA", secondary: "#E8000D" },
  "iowa state cyclones": { abbr: "ISU", id: "66", primary: "#C8102E", secondary: "#F1BE48" },
  "iowa state": { abbr: "ISU", id: "66", primary: "#C8102E", secondary: "#F1BE48" },
  "tcu horned frogs": { abbr: "TCU", id: "2628", primary: "#4D1979", secondary: "#A3A9AC" },
  "tcu": { abbr: "TCU", id: "2628", primary: "#4D1979", secondary: "#A3A9AC" },
  "texas tech red raiders": { abbr: "TTU", id: "2641", primary: "#CC0000", secondary: "#000000" },
  "texas tech": { abbr: "TTU", id: "2641", primary: "#CC0000", secondary: "#000000" },
  "byu cougars": { abbr: "BYU", id: "252", primary: "#002E5D", secondary: "#FFFFFF" },
  "byu": { abbr: "BYU", id: "252", primary: "#002E5D", secondary: "#FFFFFF" },
  "brigham young": { abbr: "BYU", id: "252", primary: "#002E5D", secondary: "#FFFFFF" },
  "cincinnati bearcats": { abbr: "CIN", id: "2132", primary: "#E00122", secondary: "#000000" },
  "cincinnati": { abbr: "CIN", id: "2132", primary: "#E00122", secondary: "#000000" },
  "ucf knights": { abbr: "UCF", id: "2116", primary: "#BA9B37", secondary: "#000000" },
  "ucf": { abbr: "UCF", id: "2116", primary: "#BA9B37", secondary: "#000000" },
  "central florida": { abbr: "UCF", id: "2116", primary: "#BA9B37", secondary: "#000000" },
  "houston cougars": { abbr: "HOU", id: "248", primary: "#C8102E", secondary: "#FFFFFF" },
  "houston": { abbr: "HOU", id: "248", primary: "#C8102E", secondary: "#FFFFFF" },
  "oregon state beavers": { abbr: "ORST", id: "204", primary: "#DC4405", secondary: "#000000" },
  "oregon state": { abbr: "ORST", id: "204", primary: "#DC4405", secondary: "#000000" },
  "washington state cougars": { abbr: "WSU", id: "265", primary: "#981E32", secondary: "#5E6A71" },
  "washington state": { abbr: "WSU", id: "265", primary: "#981E32", secondary: "#5E6A71" },
  "wsu": { abbr: "WSU", id: "265", primary: "#981E32", secondary: "#5E6A71" },
  "memphis tigers": { abbr: "MEM", id: "235", primary: "#003087", secondary: "#898D8D" },
  "memphis": { abbr: "MEM", id: "235", primary: "#003087", secondary: "#898D8D" },
  "smu mustangs": { abbr: "SMU", id: "2567", primary: "#354CA1", secondary: "#C8102E" },
  "smu": { abbr: "SMU", id: "2567", primary: "#354CA1", secondary: "#C8102E" },
  "tulane green wave": { abbr: "TUL", id: "2655", primary: "#006747", secondary: "#87CEEB" },
  "tulane": { abbr: "TUL", id: "2655", primary: "#006747", secondary: "#87CEEB" },
  "syracuse orange": { abbr: "SYR", id: "183", primary: "#F76900", secondary: "#002D72" },
  "syracuse": { abbr: "SYR", id: "183", primary: "#F76900", secondary: "#002D72" },
  "boston college eagles": { abbr: "BC", id: "103", primary: "#98002E", secondary: "#BC9B6A" },
  "boston college": { abbr: "BC", id: "103", primary: "#98002E", secondary: "#BC9B6A" },
  "duke blue devils": { abbr: "DUKE", id: "150", primary: "#003087", secondary: "#FFFFFF" },
  "duke": { abbr: "DUKE", id: "150", primary: "#003087", secondary: "#FFFFFF" },
  "wake forest demon deacons": { abbr: "WAKE", id: "154", primary: "#9E7E38", secondary: "#000000" },
  "wake forest": { abbr: "WAKE", id: "154", primary: "#9E7E38", secondary: "#000000" },
  "virginia cavaliers": { abbr: "UVA", id: "258", primary: "#232D4B", secondary: "#F84C1E" },
  "virginia": { abbr: "UVA", id: "258", primary: "#232D4B", secondary: "#F84C1E" },
  "georgia tech yellow jackets": { abbr: "GT", id: "59", primary: "#B3A369", secondary: "#003057" },
  "georgia tech": { abbr: "GT", id: "59", primary: "#B3A369", secondary: "#003057" },
  "south carolina gamecocks": { abbr: "SCAR", id: "2579", primary: "#73000A", secondary: "#000000" },
  "south carolina": { abbr: "SCAR", id: "2579", primary: "#73000A", secondary: "#000000" },
  "mississippi state bulldogs": { abbr: "MSST", id: "344", primary: "#660000", secondary: "#FFFFFF" },
  "mississippi state": { abbr: "MSST", id: "344", primary: "#660000", secondary: "#FFFFFF" },
  "miss state": { abbr: "MSST", id: "344", primary: "#660000", secondary: "#FFFFFF" },
  "vanderbilt commodores": { abbr: "VAN", id: "238", primary: "#866D4B", secondary: "#000000" },
  "vanderbilt": { abbr: "VAN", id: "238", primary: "#866D4B", secondary: "#000000" },
  "missouri tigers": { abbr: "MIZ", id: "142", primary: "#F1B82D", secondary: "#000000" },
  "missouri": { abbr: "MIZ", id: "142", primary: "#F1B82D", secondary: "#000000" },
  "mizzou": { abbr: "MIZ", id: "142", primary: "#F1B82D", secondary: "#000000" },
  // Group of 5 Teams
  "boise state broncos": { abbr: "BSU", id: "68", primary: "#0033A0", secondary: "#D64309" },
  "boise state": { abbr: "BSU", id: "68", primary: "#0033A0", secondary: "#D64309" },
  "liberty flames": { abbr: "LIB", id: "2335", primary: "#990000", secondary: "#FFFFFF" },
  "liberty": { abbr: "LIB", id: "2335", primary: "#990000", secondary: "#FFFFFF" },
  "app state mountaineers": { abbr: "APP", id: "2026", primary: "#FFCC00", secondary: "#000000" },
  "appalachian state": { abbr: "APP", id: "2026", primary: "#FFCC00", secondary: "#000000" },
  "app state": { abbr: "APP", id: "2026", primary: "#FFCC00", secondary: "#000000" },
  "marshall thundering herd": { abbr: "MRSH", id: "276", primary: "#00B140", secondary: "#FFFFFF" },
  "marshall": { abbr: "MRSH", id: "276", primary: "#00B140", secondary: "#FFFFFF" },
  "coastal carolina chanticleers": { abbr: "CCU", id: "324", primary: "#006F71", secondary: "#A27752" },
  "coastal carolina": { abbr: "CCU", id: "324", primary: "#006F71", secondary: "#A27752" },
  "james madison dukes": { abbr: "JMU", id: "256", primary: "#450084", secondary: "#B8860B" },
  "james madison": { abbr: "JMU", id: "256", primary: "#450084", secondary: "#B8860B" },
  "jmu": { abbr: "JMU", id: "256", primary: "#450084", secondary: "#B8860B" },
  "san jose state spartans": { abbr: "SJSU", id: "23", primary: "#0055A2", secondary: "#E5A823" },
  "san jose state": { abbr: "SJSU", id: "23", primary: "#0055A2", secondary: "#E5A823" },
  "fresno state bulldogs": { abbr: "FRES", id: "278", primary: "#DB0032", secondary: "#13294B" },
  "fresno state": { abbr: "FRES", id: "278", primary: "#DB0032", secondary: "#13294B" },
  "san diego state aztecs": { abbr: "SDSU", id: "21", primary: "#A6192E", secondary: "#000000" },
  "san diego state": { abbr: "SDSU", id: "21", primary: "#A6192E", secondary: "#000000" },
  "sdsu": { abbr: "SDSU", id: "21", primary: "#A6192E", secondary: "#000000" },
  "unlv rebels": { abbr: "UNLV", id: "2439", primary: "#B10202", secondary: "#666666" },
  "unlv": { abbr: "UNLV", id: "2439", primary: "#B10202", secondary: "#666666" },
  "nevada wolf pack": { abbr: "NEV", id: "2440", primary: "#003366", secondary: "#807F84" },
  "nevada": { abbr: "NEV", id: "2440", primary: "#003366", secondary: "#807F84" },
  "air force falcons": { abbr: "AFA", id: "2005", primary: "#003087", secondary: "#8F8F8C" },
  "air force": { abbr: "AFA", id: "2005", primary: "#003087", secondary: "#8F8F8C" },
  "army black knights": { abbr: "ARMY", id: "349", primary: "#000000", secondary: "#D3BC8D" },
  "army": { abbr: "ARMY", id: "349", primary: "#000000", secondary: "#D3BC8D" },
  "navy midshipmen": { abbr: "NAVY", id: "2426", primary: "#00205B", secondary: "#B8860B" },
  "navy": { abbr: "NAVY", id: "2426", primary: "#00205B", secondary: "#B8860B" },
  "usf bulls": { abbr: "USF", id: "58", primary: "#006747", secondary: "#CFC493" },
  "south florida": { abbr: "USF", id: "58", primary: "#006747", secondary: "#CFC493" },
  "usf": { abbr: "USF", id: "58", primary: "#006747", secondary: "#CFC493" },
  "east carolina pirates": { abbr: "ECU", id: "151", primary: "#592A8A", secondary: "#FDC82F" },
  "east carolina": { abbr: "ECU", id: "151", primary: "#592A8A", secondary: "#FDC82F" },
  "charlotte 49ers": { abbr: "CLT", id: "2429", primary: "#00703C", secondary: "#B4975A" },
  "rice owls": { abbr: "RICE", id: "242", primary: "#00205B", secondary: "#5E6A71" },
  "rice": { abbr: "RICE", id: "242", primary: "#00205B", secondary: "#5E6A71" },
  "utsa roadrunners": { abbr: "UTSA", id: "2636", primary: "#0C2340", secondary: "#F47321" },
  "utsa": { abbr: "UTSA", id: "2636", primary: "#0C2340", secondary: "#F47321" },
  "north texas mean green": { abbr: "UNT", id: "249", primary: "#00853E", secondary: "#FFFFFF" },
  "north texas": { abbr: "UNT", id: "249", primary: "#00853E", secondary: "#FFFFFF" },
  "unt": { abbr: "UNT", id: "249", primary: "#00853E", secondary: "#FFFFFF" },
  "tulsa golden hurricane": { abbr: "TLSA", id: "202", primary: "#002D62", secondary: "#C8102E" },
  "tulsa": { abbr: "TLSA", id: "202", primary: "#002D62", secondary: "#C8102E" },
  "fau owls": { abbr: "FAU", id: "2226", primary: "#003366", secondary: "#CC0000" },
  "florida atlantic": { abbr: "FAU", id: "2226", primary: "#003366", secondary: "#CC0000" },
  "fau": { abbr: "FAU", id: "2226", primary: "#003366", secondary: "#CC0000" },
  "uab blazers": { abbr: "UAB", id: "5", primary: "#1E6B52", secondary: "#D4AF37" },
  "uab": { abbr: "UAB", id: "5", primary: "#1E6B52", secondary: "#D4AF37" },
  "temple owls": { abbr: "TEM", id: "218", primary: "#A41E35", secondary: "#FFFFFF" },
  "temple": { abbr: "TEM", id: "218", primary: "#A41E35", secondary: "#FFFFFF" },
}

// ============================================================================
// COLLEGE BASKETBALL TEAMS - Comprehensive List with ESPN Team IDs
// ============================================================================
const NCAAB_TEAMS: Record<string, { abbr: string; id: string; primary: string; secondary: string }> = {
  // Power Conference Teams
  "duke blue devils": { abbr: "DUKE", id: "150", primary: "#003087", secondary: "#FFFFFF" },
  "duke": { abbr: "DUKE", id: "150", primary: "#003087", secondary: "#FFFFFF" },
  "north carolina tar heels": { abbr: "UNC", id: "153", primary: "#7BAFD4", secondary: "#FFFFFF" },
  "north carolina": { abbr: "UNC", id: "153", primary: "#7BAFD4", secondary: "#FFFFFF" },
  "unc": { abbr: "UNC", id: "153", primary: "#7BAFD4", secondary: "#FFFFFF" },
  "kentucky wildcats": { abbr: "UK", id: "96", primary: "#0033A0", secondary: "#FFFFFF" },
  "kentucky": { abbr: "UK", id: "96", primary: "#0033A0", secondary: "#FFFFFF" },
  "kansas jayhawks": { abbr: "KU", id: "2305", primary: "#0051BA", secondary: "#E8000D" },
  "kansas": { abbr: "KU", id: "2305", primary: "#0051BA", secondary: "#E8000D" },
  "villanova wildcats": { abbr: "NOVA", id: "222", primary: "#00205B", secondary: "#13B5EA" },
  "villanova": { abbr: "NOVA", id: "222", primary: "#00205B", secondary: "#13B5EA" },
  "gonzaga bulldogs": { abbr: "GONZ", id: "2250", primary: "#002967", secondary: "#C8102E" },
  "gonzaga": { abbr: "GONZ", id: "2250", primary: "#002967", secondary: "#C8102E" },
  "ucla bruins": { abbr: "UCLA", id: "26", primary: "#2D68C4", secondary: "#F2A900" },
  "ucla": { abbr: "UCLA", id: "26", primary: "#2D68C4", secondary: "#F2A900" },
  "uconn huskies": { abbr: "CONN", id: "41", primary: "#000E2F", secondary: "#E4002B" },
  "uconn": { abbr: "CONN", id: "41", primary: "#000E2F", secondary: "#E4002B" },
  "connecticut": { abbr: "CONN", id: "41", primary: "#000E2F", secondary: "#E4002B" },
  "connecticut huskies": { abbr: "CONN", id: "41", primary: "#000E2F", secondary: "#E4002B" },
  "purdue boilermakers": { abbr: "PUR", id: "2509", primary: "#CEB888", secondary: "#000000" },
  "purdue": { abbr: "PUR", id: "2509", primary: "#CEB888", secondary: "#000000" },
  "houston cougars": { abbr: "HOU", id: "248", primary: "#C8102E", secondary: "#FFFFFF" },
  "houston": { abbr: "HOU", id: "248", primary: "#C8102E", secondary: "#FFFFFF" },
  "arizona wildcats": { abbr: "ARIZ", id: "12", primary: "#CC0033", secondary: "#003366" },
  "arizona": { abbr: "ARIZ", id: "12", primary: "#CC0033", secondary: "#003366" },
  "baylor bears": { abbr: "BAY", id: "239", primary: "#154734", secondary: "#FFB81C" },
  "baylor": { abbr: "BAY", id: "239", primary: "#154734", secondary: "#FFB81C" },
  "creighton bluejays": { abbr: "CREI", id: "156", primary: "#005CA9", secondary: "#FFFFFF" },
  "creighton": { abbr: "CREI", id: "156", primary: "#005CA9", secondary: "#FFFFFF" },
  "marquette golden eagles": { abbr: "MARQ", id: "269", primary: "#003366", secondary: "#FFCC00" },
  "marquette": { abbr: "MARQ", id: "269", primary: "#003366", secondary: "#FFCC00" },
  "syracuse orange": { abbr: "SYR", id: "183", primary: "#F76900", secondary: "#002D72" },
  "syracuse": { abbr: "SYR", id: "183", primary: "#F76900", secondary: "#002D72" },
  "tennessee volunteers": { abbr: "TENN", id: "2633", primary: "#FF8200", secondary: "#FFFFFF" },
  "tennessee": { abbr: "TENN", id: "2633", primary: "#FF8200", secondary: "#FFFFFF" },
  "alabama crimson tide": { abbr: "ALA", id: "333", primary: "#9E1B32", secondary: "#828A8F" },
  "alabama": { abbr: "ALA", id: "333", primary: "#9E1B32", secondary: "#828A8F" },
  "auburn tigers": { abbr: "AUB", id: "2", primary: "#0C2340", secondary: "#E87722" },
  "auburn": { abbr: "AUB", id: "2", primary: "#0C2340", secondary: "#E87722" },
  "michigan state spartans": { abbr: "MSU", id: "127", primary: "#18453B", secondary: "#FFFFFF" },
  "michigan state": { abbr: "MSU", id: "127", primary: "#18453B", secondary: "#FFFFFF" },
  "iowa state cyclones": { abbr: "ISU", id: "66", primary: "#C8102E", secondary: "#F1BE48" },
  "iowa state": { abbr: "ISU", id: "66", primary: "#C8102E", secondary: "#F1BE48" },
  "texas longhorns": { abbr: "TEX", id: "251", primary: "#BF5700", secondary: "#FFFFFF" },
  "texas": { abbr: "TEX", id: "251", primary: "#BF5700", secondary: "#FFFFFF" },
  "indiana hoosiers": { abbr: "IND", id: "84", primary: "#990000", secondary: "#FFFFFF" },
  "indiana": { abbr: "IND", id: "84", primary: "#990000", secondary: "#FFFFFF" },
  "michigan wolverines": { abbr: "MICH", id: "130", primary: "#00274C", secondary: "#FFCB05" },
  "michigan": { abbr: "MICH", id: "130", primary: "#00274C", secondary: "#FFCB05" },
  "florida gators": { abbr: "FLA", id: "57", primary: "#0021A5", secondary: "#FA4616" },
  "florida": { abbr: "FLA", id: "57", primary: "#0021A5", secondary: "#FA4616" },
  "arkansas razorbacks": { abbr: "ARK", id: "8", primary: "#9D2235", secondary: "#FFFFFF" },
  "arkansas": { abbr: "ARK", id: "8", primary: "#9D2235", secondary: "#FFFFFF" },
  "san diego state aztecs": { abbr: "SDSU", id: "21", primary: "#A6192E", secondary: "#000000" },
  "san diego state": { abbr: "SDSU", id: "21", primary: "#A6192E", secondary: "#000000" },
  // More Teams
  "ohio state buckeyes": { abbr: "OSU", id: "194", primary: "#BB0000", secondary: "#666666" },
  "ohio state": { abbr: "OSU", id: "194", primary: "#BB0000", secondary: "#666666" },
  "louisville cardinals": { abbr: "LOU", id: "97", primary: "#AD0000", secondary: "#000000" },
  "louisville": { abbr: "LOU", id: "97", primary: "#AD0000", secondary: "#000000" },
  "wisconsin badgers": { abbr: "WIS", id: "275", primary: "#C5050C", secondary: "#FFFFFF" },
  "wisconsin": { abbr: "WIS", id: "275", primary: "#C5050C", secondary: "#FFFFFF" },
  "iowa hawkeyes": { abbr: "IOWA", id: "2294", primary: "#FFCD00", secondary: "#000000" },
  "iowa": { abbr: "IOWA", id: "2294", primary: "#FFCD00", secondary: "#000000" },
  "illinois fighting illini": { abbr: "ILL", id: "356", primary: "#E84A27", secondary: "#13294B" },
  "illinois": { abbr: "ILL", id: "356", primary: "#E84A27", secondary: "#13294B" },
  "texas tech red raiders": { abbr: "TTU", id: "2641", primary: "#CC0000", secondary: "#000000" },
  "texas tech": { abbr: "TTU", id: "2641", primary: "#CC0000", secondary: "#000000" },
  "xavier musketeers": { abbr: "XAV", id: "2752", primary: "#002B5C", secondary: "#FFFFFF" },
  "xavier": { abbr: "XAV", id: "2752", primary: "#002B5C", secondary: "#FFFFFF" },
  "st. john's red storm": { abbr: "SJU", id: "2599", primary: "#BA0C2F", secondary: "#FFFFFF" },
  "st johns": { abbr: "SJU", id: "2599", primary: "#BA0C2F", secondary: "#FFFFFF" },
  "st. johns": { abbr: "SJU", id: "2599", primary: "#BA0C2F", secondary: "#FFFFFF" },
  "providence friars": { abbr: "PROV", id: "2507", primary: "#000000", secondary: "#FFFFFF" },
  "providence": { abbr: "PROV", id: "2507", primary: "#000000", secondary: "#FFFFFF" },
  "seton hall pirates": { abbr: "HALL", id: "2550", primary: "#003DA5", secondary: "#FFFFFF" },
  "seton hall": { abbr: "HALL", id: "2550", primary: "#003DA5", secondary: "#FFFFFF" },
  "butler bulldogs": { abbr: "BUT", id: "2086", primary: "#13294B", secondary: "#FFFFFF" },
  "butler": { abbr: "BUT", id: "2086", primary: "#13294B", secondary: "#FFFFFF" },
  "depaul blue demons": { abbr: "DEP", id: "305", primary: "#005EB8", secondary: "#E4002B" },
  "depaul": { abbr: "DEP", id: "305", primary: "#005EB8", secondary: "#E4002B" },
  "georgetown hoyas": { abbr: "GTWN", id: "46", primary: "#041E42", secondary: "#8D817B" },
  "georgetown": { abbr: "GTWN", id: "46", primary: "#041E42", secondary: "#8D817B" },
  "oregon ducks": { abbr: "ORE", id: "2483", primary: "#154733", secondary: "#FEE123" },
  "oregon": { abbr: "ORE", id: "2483", primary: "#154733", secondary: "#FEE123" },
  "usc trojans": { abbr: "USC", id: "30", primary: "#990000", secondary: "#FFC72C" },
  "usc": { abbr: "USC", id: "30", primary: "#990000", secondary: "#FFC72C" },
  "colorado buffaloes": { abbr: "COLO", id: "38", primary: "#CFB87C", secondary: "#000000" },
  "colorado": { abbr: "COLO", id: "38", primary: "#CFB87C", secondary: "#000000" },
  "oklahoma sooners": { abbr: "OU", id: "201", primary: "#841617", secondary: "#FDF9D8" },
  "oklahoma": { abbr: "OU", id: "201", primary: "#841617", secondary: "#FDF9D8" },
  "kansas state wildcats": { abbr: "KSU", id: "2306", primary: "#512888", secondary: "#FFFFFF" },
  "kansas state": { abbr: "KSU", id: "2306", primary: "#512888", secondary: "#FFFFFF" },
  "k-state": { abbr: "KSU", id: "2306", primary: "#512888", secondary: "#FFFFFF" },
  "tcu horned frogs": { abbr: "TCU", id: "2628", primary: "#4D1979", secondary: "#A3A9AC" },
  "tcu": { abbr: "TCU", id: "2628", primary: "#4D1979", secondary: "#A3A9AC" },
  "byu cougars": { abbr: "BYU", id: "252", primary: "#002E5D", secondary: "#FFFFFF" },
  "byu": { abbr: "BYU", id: "252", primary: "#002E5D", secondary: "#FFFFFF" },
  "brigham young": { abbr: "BYU", id: "252", primary: "#002E5D", secondary: "#FFFFFF" },
  "cincinnati bearcats": { abbr: "CIN", id: "2132", primary: "#E00122", secondary: "#000000" },
  "cincinnati": { abbr: "CIN", id: "2132", primary: "#E00122", secondary: "#000000" },
  "ucf knights": { abbr: "UCF", id: "2116", primary: "#BA9B37", secondary: "#000000" },
  "ucf": { abbr: "UCF", id: "2116", primary: "#BA9B37", secondary: "#000000" },
  "central florida": { abbr: "UCF", id: "2116", primary: "#BA9B37", secondary: "#000000" },
  "memphis tigers": { abbr: "MEM", id: "235", primary: "#003087", secondary: "#898D8D" },
  "memphis": { abbr: "MEM", id: "235", primary: "#003087", secondary: "#898D8D" },
  "smu mustangs": { abbr: "SMU", id: "2567", primary: "#354CA1", secondary: "#C8102E" },
  "smu": { abbr: "SMU", id: "2567", primary: "#354CA1", secondary: "#C8102E" },
  "southern methodist": { abbr: "SMU", id: "2567", primary: "#354CA1", secondary: "#C8102E" },
  "florida atlantic owls": { abbr: "FAU", id: "2226", primary: "#003366", secondary: "#CC0000" },
  "florida atlantic": { abbr: "FAU", id: "2226", primary: "#003366", secondary: "#CC0000" },
  "fau": { abbr: "FAU", id: "2226", primary: "#003366", secondary: "#CC0000" },
  "northwestern wildcats": { abbr: "NW", id: "77", primary: "#4E2A84", secondary: "#FFFFFF" },
  "northwestern": { abbr: "NW", id: "77", primary: "#4E2A84", secondary: "#FFFFFF" },
  "minnesota golden gophers": { abbr: "MINN", id: "135", primary: "#7A0019", secondary: "#FFCC33" },
  "minnesota": { abbr: "MINN", id: "135", primary: "#7A0019", secondary: "#FFCC33" },
  "nebraska cornhuskers": { abbr: "NEB", id: "158", primary: "#E41C38", secondary: "#FFFFFF" },
  "nebraska": { abbr: "NEB", id: "158", primary: "#E41C38", secondary: "#FFFFFF" },
  "penn state nittany lions": { abbr: "PSU", id: "213", primary: "#041E42", secondary: "#FFFFFF" },
  "penn state": { abbr: "PSU", id: "213", primary: "#041E42", secondary: "#FFFFFF" },
  "rutgers scarlet knights": { abbr: "RUTG", id: "164", primary: "#CC0033", secondary: "#5F6A72" },
  "rutgers": { abbr: "RUTG", id: "164", primary: "#CC0033", secondary: "#5F6A72" },
  "maryland terrapins": { abbr: "MD", id: "120", primary: "#E03A3E", secondary: "#FFD520" },
  "maryland": { abbr: "MD", id: "120", primary: "#E03A3E", secondary: "#FFD520" },
}

// ============================================================================
// SOCCER TEAMS - Comprehensive List (MLS, EPL, La Liga, UCL, etc.)
// ============================================================================
const SOCCER_TEAMS: Record<string, { abbr: string; id: string; league: string; primary: string; secondary: string }> = {
  // ==================== MLS Teams ====================
  "la galaxy": { abbr: "LA", id: "69", league: "usa.1", primary: "#00245D", secondary: "#FFD200" },
  "galaxy": { abbr: "LA", id: "69", league: "usa.1", primary: "#00245D", secondary: "#FFD200" },
  "los angeles galaxy": { abbr: "LA", id: "69", league: "usa.1", primary: "#00245D", secondary: "#FFD200" },
  "lafc": { abbr: "LAFC", id: "21866", league: "usa.1", primary: "#000000", secondary: "#C39E6D" },
  "los angeles fc": { abbr: "LAFC", id: "21866", league: "usa.1", primary: "#000000", secondary: "#C39E6D" },
  "inter miami": { abbr: "MIA", id: "26853", league: "usa.1", primary: "#F7B5CD", secondary: "#231F20" },
  "inter miami cf": { abbr: "MIA", id: "26853", league: "usa.1", primary: "#F7B5CD", secondary: "#231F20" },
  "atlanta united": { abbr: "ATL", id: "18497", league: "usa.1", primary: "#80000A", secondary: "#231F20" },
  "atlanta united fc": { abbr: "ATL", id: "18497", league: "usa.1", primary: "#80000A", secondary: "#231F20" },
  "seattle sounders": { abbr: "SEA", id: "9726", league: "usa.1", primary: "#5D9741", secondary: "#005595" },
  "seattle sounders fc": { abbr: "SEA", id: "9726", league: "usa.1", primary: "#5D9741", secondary: "#005595" },
  "new york red bulls": { abbr: "RBNY", id: "399", league: "usa.1", primary: "#ED1E36", secondary: "#FFCD00" },
  "ny red bulls": { abbr: "RBNY", id: "399", league: "usa.1", primary: "#ED1E36", secondary: "#FFCD00" },
  "red bulls": { abbr: "RBNY", id: "399", league: "usa.1", primary: "#ED1E36", secondary: "#FFCD00" },
  "new york city fc": { abbr: "NYC", id: "17012", league: "usa.1", primary: "#6CACE4", secondary: "#F15524" },
  "nycfc": { abbr: "NYC", id: "17012", league: "usa.1", primary: "#6CACE4", secondary: "#F15524" },
  "portland timbers": { abbr: "POR", id: "9498", league: "usa.1", primary: "#004812", secondary: "#EBE72B" },
  "timbers": { abbr: "POR", id: "9498", league: "usa.1", primary: "#004812", secondary: "#EBE72B" },
  "fc cincinnati": { abbr: "CIN", id: "21816", league: "usa.1", primary: "#F05323", secondary: "#263B80" },
  "columbus crew": { abbr: "CLB", id: "54", league: "usa.1", primary: "#000000", secondary: "#FFDB00" },
  "crew": { abbr: "CLB", id: "54", league: "usa.1", primary: "#000000", secondary: "#FFDB00" },
  "chicago fire fc": { abbr: "CHI", id: "182", league: "usa.1", primary: "#141414", secondary: "#FF0000" },
  "chicago fire": { abbr: "CHI", id: "182", league: "usa.1", primary: "#141414", secondary: "#FF0000" },
  "fire": { abbr: "CHI", id: "182", league: "usa.1", primary: "#141414", secondary: "#FF0000" },
  "sporting kansas city": { abbr: "SKC", id: "339", league: "usa.1", primary: "#93B1D7", secondary: "#002F65" },
  "sporting kc": { abbr: "SKC", id: "339", league: "usa.1", primary: "#93B1D7", secondary: "#002F65" },
  "austin fc": { abbr: "ATX", id: "25571", league: "usa.1", primary: "#00B140", secondary: "#000000" },
  "austin": { abbr: "ATX", id: "25571", league: "usa.1", primary: "#00B140", secondary: "#000000" },
  "charlotte fc": { abbr: "CLT", id: "24737", league: "usa.1", primary: "#1A85C8", secondary: "#000000" },
  "charlotte": { abbr: "CLT", id: "24737", league: "usa.1", primary: "#1A85C8", secondary: "#000000" },
  "nashville sc": { abbr: "NSH", id: "22653", league: "usa.1", primary: "#ECE83A", secondary: "#1F1646" },
  "nashville": { abbr: "NSH", id: "22653", league: "usa.1", primary: "#ECE83A", secondary: "#1F1646" },
  "philadelphia union": { abbr: "PHI", id: "9511", league: "usa.1", primary: "#002D55", secondary: "#B18500" },
  "union": { abbr: "PHI", id: "9511", league: "usa.1", primary: "#002D55", secondary: "#B18500" },
  "dc united": { abbr: "DC", id: "193", league: "usa.1", primary: "#000000", secondary: "#EF3E42" },
  "d.c. united": { abbr: "DC", id: "193", league: "usa.1", primary: "#000000", secondary: "#EF3E42" },
  "new england revolution": { abbr: "NE", id: "220", league: "usa.1", primary: "#C63323", secondary: "#0A1E32" },
  "revolution": { abbr: "NE", id: "220", league: "usa.1", primary: "#C63323", secondary: "#0A1E32" },
  "toronto fc": { abbr: "TOR", id: "9568", league: "usa.1", primary: "#B81137", secondary: "#455560" },
  "toronto": { abbr: "TOR", id: "9568", league: "usa.1", primary: "#B81137", secondary: "#455560" },
  "cf montreal": { abbr: "MTL", id: "338", league: "usa.1", primary: "#000000", secondary: "#C2B59B" },
  "montreal": { abbr: "MTL", id: "338", league: "usa.1", primary: "#000000", secondary: "#C2B59B" },
  "vancouver whitecaps": { abbr: "VAN", id: "9508", league: "usa.1", primary: "#00245D", secondary: "#9DC3E6" },
  "whitecaps": { abbr: "VAN", id: "9508", league: "usa.1", primary: "#00245D", secondary: "#9DC3E6" },
  "orlando city": { abbr: "ORL", id: "17015", league: "usa.1", primary: "#633492", secondary: "#FDE192" },
  "orlando city sc": { abbr: "ORL", id: "17015", league: "usa.1", primary: "#633492", secondary: "#FDE192" },
  "minnesota united": { abbr: "MIN", id: "18577", league: "usa.1", primary: "#8CD2E5", secondary: "#231F20" },
  "minnesota united fc": { abbr: "MIN", id: "18577", league: "usa.1", primary: "#8CD2E5", secondary: "#231F20" },
  "houston dynamo": { abbr: "HOU", id: "333", league: "usa.1", primary: "#FF6B00", secondary: "#101820" },
  "dynamo": { abbr: "HOU", id: "333", league: "usa.1", primary: "#FF6B00", secondary: "#101820" },
  "fc dallas": { abbr: "DAL", id: "259", league: "usa.1", primary: "#BF0D3E", secondary: "#0C2340" },
  "dallas": { abbr: "DAL", id: "259", league: "usa.1", primary: "#BF0D3E", secondary: "#0C2340" },
  "real salt lake": { abbr: "RSL", id: "337", league: "usa.1", primary: "#B30838", secondary: "#013A81" },
  "rsl": { abbr: "RSL", id: "337", league: "usa.1", primary: "#B30838", secondary: "#013A81" },
  "colorado rapids": { abbr: "COL", id: "195", league: "usa.1", primary: "#8B2346", secondary: "#96D1FF" },
  "rapids": { abbr: "COL", id: "195", league: "usa.1", primary: "#8B2346", secondary: "#96D1FF" },
  "san jose earthquakes": { abbr: "SJ", id: "233", league: "usa.1", primary: "#0067B1", secondary: "#000000" },
  "earthquakes": { abbr: "SJ", id: "233", league: "usa.1", primary: "#0067B1", secondary: "#000000" },
  "st. louis city sc": { abbr: "STL", id: "27232", league: "usa.1", primary: "#D22630", secondary: "#0C2340" },
  "st louis city": { abbr: "STL", id: "27232", league: "usa.1", primary: "#D22630", secondary: "#0C2340" },
  // ==================== EPL Teams ====================
  "manchester united": { abbr: "MUN", id: "360", league: "eng.1", primary: "#DA291C", secondary: "#FBE122" },
  "man united": { abbr: "MUN", id: "360", league: "eng.1", primary: "#DA291C", secondary: "#FBE122" },
  "man utd": { abbr: "MUN", id: "360", league: "eng.1", primary: "#DA291C", secondary: "#FBE122" },
  "manchester city": { abbr: "MCI", id: "382", league: "eng.1", primary: "#6CABDD", secondary: "#1C2C5B" },
  "man city": { abbr: "MCI", id: "382", league: "eng.1", primary: "#6CABDD", secondary: "#1C2C5B" },
  "liverpool": { abbr: "LIV", id: "364", league: "eng.1", primary: "#C8102E", secondary: "#00B2A9" },
  "liverpool fc": { abbr: "LIV", id: "364", league: "eng.1", primary: "#C8102E", secondary: "#00B2A9" },
  "chelsea": { abbr: "CHE", id: "363", league: "eng.1", primary: "#034694", secondary: "#DBA111" },
  "chelsea fc": { abbr: "CHE", id: "363", league: "eng.1", primary: "#034694", secondary: "#DBA111" },
  "arsenal": { abbr: "ARS", id: "359", league: "eng.1", primary: "#EF0107", secondary: "#063672" },
  "arsenal fc": { abbr: "ARS", id: "359", league: "eng.1", primary: "#EF0107", secondary: "#063672" },
  "tottenham hotspur": { abbr: "TOT", id: "367", league: "eng.1", primary: "#132257", secondary: "#FFFFFF" },
  "tottenham": { abbr: "TOT", id: "367", league: "eng.1", primary: "#132257", secondary: "#FFFFFF" },
  "spurs": { abbr: "TOT", id: "367", league: "eng.1", primary: "#132257", secondary: "#FFFFFF" },
  "newcastle united": { abbr: "NEW", id: "361", league: "eng.1", primary: "#241F20", secondary: "#FFFFFF" },
  "newcastle": { abbr: "NEW", id: "361", league: "eng.1", primary: "#241F20", secondary: "#FFFFFF" },
  "aston villa": { abbr: "AVL", id: "362", league: "eng.1", primary: "#670E36", secondary: "#95BFE5" },
  "brighton & hove albion": { abbr: "BHA", id: "331", league: "eng.1", primary: "#0057B8", secondary: "#FFFFFF" },
  "brighton": { abbr: "BHA", id: "331", league: "eng.1", primary: "#0057B8", secondary: "#FFFFFF" },
  "west ham united": { abbr: "WHU", id: "371", league: "eng.1", primary: "#7A263A", secondary: "#1BB1E7" },
  "west ham": { abbr: "WHU", id: "371", league: "eng.1", primary: "#7A263A", secondary: "#1BB1E7" },
  "everton": { abbr: "EVE", id: "368", league: "eng.1", primary: "#003399", secondary: "#FFFFFF" },
  "everton fc": { abbr: "EVE", id: "368", league: "eng.1", primary: "#003399", secondary: "#FFFFFF" },
  "fulham": { abbr: "FUL", id: "370", league: "eng.1", primary: "#000000", secondary: "#FFFFFF" },
  "fulham fc": { abbr: "FUL", id: "370", league: "eng.1", primary: "#000000", secondary: "#FFFFFF" },
  "crystal palace": { abbr: "CRY", id: "384", league: "eng.1", primary: "#1B458F", secondary: "#C4122E" },
  "wolverhampton wanderers": { abbr: "WOL", id: "380", league: "eng.1", primary: "#FDB913", secondary: "#231F20" },
  "wolves": { abbr: "WOL", id: "380", league: "eng.1", primary: "#FDB913", secondary: "#231F20" },
  "wolverhampton": { abbr: "WOL", id: "380", league: "eng.1", primary: "#FDB913", secondary: "#231F20" },
  "afc bournemouth": { abbr: "BOU", id: "349", league: "eng.1", primary: "#DA291C", secondary: "#000000" },
  "bournemouth": { abbr: "BOU", id: "349", league: "eng.1", primary: "#DA291C", secondary: "#000000" },
  "brentford": { abbr: "BRE", id: "337", league: "eng.1", primary: "#E30613", secondary: "#FFFFFF" },
  "brentford fc": { abbr: "BRE", id: "337", league: "eng.1", primary: "#E30613", secondary: "#FFFFFF" },
  "nottingham forest": { abbr: "NFO", id: "393", league: "eng.1", primary: "#DD0000", secondary: "#FFFFFF" },
  "nott'm forest": { abbr: "NFO", id: "393", league: "eng.1", primary: "#DD0000", secondary: "#FFFFFF" },
  "leicester city": { abbr: "LEI", id: "375", league: "eng.1", primary: "#003090", secondary: "#FDBE11" },
  "leicester": { abbr: "LEI", id: "375", league: "eng.1", primary: "#003090", secondary: "#FDBE11" },
  "ipswich town": { abbr: "IPS", id: "349", league: "eng.1", primary: "#0000FF", secondary: "#FFFFFF" },
  "ipswich": { abbr: "IPS", id: "349", league: "eng.1", primary: "#0000FF", secondary: "#FFFFFF" },
  "southampton": { abbr: "SOU", id: "376", league: "eng.1", primary: "#D71920", secondary: "#130C0E" },
  "southampton fc": { abbr: "SOU", id: "376", league: "eng.1", primary: "#D71920", secondary: "#130C0E" },
  // ==================== La Liga Teams ====================
  "real madrid": { abbr: "RMA", id: "86", league: "esp.1", primary: "#FEBE10", secondary: "#00529F" },
  "real madrid cf": { abbr: "RMA", id: "86", league: "esp.1", primary: "#FEBE10", secondary: "#00529F" },
  "barcelona": { abbr: "BAR", id: "83", league: "esp.1", primary: "#A50044", secondary: "#004D98" },
  "fc barcelona": { abbr: "BAR", id: "83", league: "esp.1", primary: "#A50044", secondary: "#004D98" },
  "atletico madrid": { abbr: "ATM", id: "1068", league: "esp.1", primary: "#CB3524", secondary: "#272E61" },
  "atletico de madrid": { abbr: "ATM", id: "1068", league: "esp.1", primary: "#CB3524", secondary: "#272E61" },
  "sevilla fc": { abbr: "SEV", id: "243", league: "esp.1", primary: "#D81E32", secondary: "#FFFFFF" },
  "sevilla": { abbr: "SEV", id: "243", league: "esp.1", primary: "#D81E32", secondary: "#FFFFFF" },
  "real sociedad": { abbr: "RSO", id: "89", league: "esp.1", primary: "#0067B1", secondary: "#FFFFFF" },
  "real betis": { abbr: "BET", id: "244", league: "esp.1", primary: "#00954C", secondary: "#FFFFFF" },
  "real betis balompie": { abbr: "BET", id: "244", league: "esp.1", primary: "#00954C", secondary: "#FFFFFF" },
  "villarreal cf": { abbr: "VIL", id: "102", league: "esp.1", primary: "#FFE667", secondary: "#005187" },
  "villarreal": { abbr: "VIL", id: "102", league: "esp.1", primary: "#FFE667", secondary: "#005187" },
  "athletic club": { abbr: "ATH", id: "93", league: "esp.1", primary: "#EE2523", secondary: "#FFFFFF" },
  "athletic bilbao": { abbr: "ATH", id: "93", league: "esp.1", primary: "#EE2523", secondary: "#FFFFFF" },
  "valencia cf": { abbr: "VAL", id: "94", league: "esp.1", primary: "#EE3524", secondary: "#000000" },
  "valencia": { abbr: "VAL", id: "94", league: "esp.1", primary: "#EE3524", secondary: "#000000" },
  "celta vigo": { abbr: "CEL", id: "85", league: "esp.1", primary: "#8AC3EE", secondary: "#FFFFFF" },
  "rc celta": { abbr: "CEL", id: "85", league: "esp.1", primary: "#8AC3EE", secondary: "#FFFFFF" },
  "getafe cf": { abbr: "GET", id: "3709", league: "esp.1", primary: "#005999", secondary: "#FFFFFF" },
  "getafe": { abbr: "GET", id: "3709", league: "esp.1", primary: "#005999", secondary: "#FFFFFF" },
  "osasuna": { abbr: "OSA", id: "97", league: "esp.1", primary: "#D91A21", secondary: "#0A3F7D" },
  "ca osasuna": { abbr: "OSA", id: "97", league: "esp.1", primary: "#D91A21", secondary: "#0A3F7D" },
  "rayo vallecano": { abbr: "RAY", id: "101", league: "esp.1", primary: "#E53027", secondary: "#FFFFFF" },
  "mallorca": { abbr: "MLL", id: "95", league: "esp.1", primary: "#E20613", secondary: "#000000" },
  "rcd mallorca": { abbr: "MLL", id: "95", league: "esp.1", primary: "#E20613", secondary: "#000000" },
  "girona fc": { abbr: "GIR", id: "9812", league: "esp.1", primary: "#CD2534", secondary: "#FFFFFF" },
  "girona": { abbr: "GIR", id: "9812", league: "esp.1", primary: "#CD2534", secondary: "#FFFFFF" },
  "las palmas": { abbr: "LPA", id: "466", league: "esp.1", primary: "#FFE400", secondary: "#0033A0" },
  "ud las palmas": { abbr: "LPA", id: "466", league: "esp.1", primary: "#FFE400", secondary: "#0033A0" },
  "deportivo alaves": { abbr: "ALA", id: "96", league: "esp.1", primary: "#003DA5", secondary: "#FFFFFF" },
  "alaves": { abbr: "ALA", id: "96", league: "esp.1", primary: "#003DA5", secondary: "#FFFFFF" },
  // ==================== Other Big European Teams (UCL, etc.) ====================
  "bayern munich": { abbr: "BAY", id: "132", league: "ger.1", primary: "#DC052D", secondary: "#0066B2" },
  "bayern": { abbr: "BAY", id: "132", league: "ger.1", primary: "#DC052D", secondary: "#0066B2" },
  "fc bayern munich": { abbr: "BAY", id: "132", league: "ger.1", primary: "#DC052D", secondary: "#0066B2" },
  "borussia dortmund": { abbr: "BVB", id: "124", league: "ger.1", primary: "#FDE100", secondary: "#000000" },
  "dortmund": { abbr: "BVB", id: "124", league: "ger.1", primary: "#FDE100", secondary: "#000000" },
  "bvb": { abbr: "BVB", id: "124", league: "ger.1", primary: "#FDE100", secondary: "#000000" },
  "paris saint-germain": { abbr: "PSG", id: "160", league: "fra.1", primary: "#004170", secondary: "#DA291C" },
  "psg": { abbr: "PSG", id: "160", league: "fra.1", primary: "#004170", secondary: "#DA291C" },
  "paris sg": { abbr: "PSG", id: "160", league: "fra.1", primary: "#004170", secondary: "#DA291C" },
  "juventus": { abbr: "JUV", id: "111", league: "ita.1", primary: "#000000", secondary: "#FFFFFF" },
  "juventus fc": { abbr: "JUV", id: "111", league: "ita.1", primary: "#000000", secondary: "#FFFFFF" },
  "ac milan": { abbr: "MIL", id: "103", league: "ita.1", primary: "#FB090B", secondary: "#000000" },
  "milan": { abbr: "MIL", id: "103", league: "ita.1", primary: "#FB090B", secondary: "#000000" },
  "inter milan": { abbr: "INT", id: "110", league: "ita.1", primary: "#010E80", secondary: "#000000" },
  "inter": { abbr: "INT", id: "110", league: "ita.1", primary: "#010E80", secondary: "#000000" },
  "internazionale": { abbr: "INT", id: "110", league: "ita.1", primary: "#010E80", secondary: "#000000" },
  "napoli": { abbr: "NAP", id: "114", league: "ita.1", primary: "#12A0D7", secondary: "#FFFFFF" },
  "ssc napoli": { abbr: "NAP", id: "114", league: "ita.1", primary: "#12A0D7", secondary: "#FFFFFF" },
  "as roma": { abbr: "ROM", id: "104", league: "ita.1", primary: "#8E1F2F", secondary: "#F0BC42" },
  "roma": { abbr: "ROM", id: "104", league: "ita.1", primary: "#8E1F2F", secondary: "#F0BC42" },
  "lazio": { abbr: "LAZ", id: "105", league: "ita.1", primary: "#87D8F7", secondary: "#FFFFFF" },
  "ss lazio": { abbr: "LAZ", id: "105", league: "ita.1", primary: "#87D8F7", secondary: "#FFFFFF" },
  "atalanta": { abbr: "ATA", id: "107", league: "ita.1", primary: "#1E71B8", secondary: "#000000" },
  "atalanta bc": { abbr: "ATA", id: "107", league: "ita.1", primary: "#1E71B8", secondary: "#000000" },
  "fiorentina": { abbr: "FIO", id: "109", league: "ita.1", primary: "#482E92", secondary: "#FFFFFF" },
  "acf fiorentina": { abbr: "FIO", id: "109", league: "ita.1", primary: "#482E92", secondary: "#FFFFFF" },
  "rb leipzig": { abbr: "RBL", id: "11420", league: "ger.1", primary: "#DD0741", secondary: "#FFFFFF" },
  "leipzig": { abbr: "RBL", id: "11420", league: "ger.1", primary: "#DD0741", secondary: "#FFFFFF" },
  "bayer leverkusen": { abbr: "LEV", id: "131", league: "ger.1", primary: "#E32221", secondary: "#000000" },
  "leverkusen": { abbr: "LEV", id: "131", league: "ger.1", primary: "#E32221", secondary: "#000000" },
  "eintracht frankfurt": { abbr: "SGE", id: "125", league: "ger.1", primary: "#E1000F", secondary: "#000000" },
  "frankfurt": { abbr: "SGE", id: "125", league: "ger.1", primary: "#E1000F", secondary: "#000000" },
  "vfb stuttgart": { abbr: "STU", id: "134", league: "ger.1", primary: "#E32219", secondary: "#FFFFFF" },
  "stuttgart": { abbr: "STU", id: "134", league: "ger.1", primary: "#E32219", secondary: "#FFFFFF" },
  "borussia monchengladbach": { abbr: "BMG", id: "127", league: "ger.1", primary: "#000000", secondary: "#1C9B47" },
  "gladbach": { abbr: "BMG", id: "127", league: "ger.1", primary: "#000000", secondary: "#1C9B47" },
  "ajax": { abbr: "AJA", id: "139", league: "ned.1", primary: "#CF0032", secondary: "#FFFFFF" },
  "afc ajax": { abbr: "AJA", id: "139", league: "ned.1", primary: "#CF0032", secondary: "#FFFFFF" },
  "psv eindhoven": { abbr: "PSV", id: "144", league: "ned.1", primary: "#ED1C24", secondary: "#FFFFFF" },
  "psv": { abbr: "PSV", id: "144", league: "ned.1", primary: "#ED1C24", secondary: "#FFFFFF" },
  "benfica": { abbr: "SLB", id: "212", league: "por.1", primary: "#FF0000", secondary: "#FFFFFF" },
  "sl benfica": { abbr: "SLB", id: "212", league: "por.1", primary: "#FF0000", secondary: "#FFFFFF" },
  "porto": { abbr: "POR", id: "213", league: "por.1", primary: "#004B93", secondary: "#FFFFFF" },
  "fc porto": { abbr: "POR", id: "213", league: "por.1", primary: "#004B93", secondary: "#FFFFFF" },
  "sporting cp": { abbr: "SCP", id: "214", league: "por.1", primary: "#008B4D", secondary: "#FFFFFF" },
  "sporting lisbon": { abbr: "SCP", id: "214", league: "por.1", primary: "#008B4D", secondary: "#FFFFFF" },
  "celtic": { abbr: "CEL", id: "142", league: "sco.1", primary: "#017B48", secondary: "#FFFFFF" },
  "celtic fc": { abbr: "CEL", id: "142", league: "sco.1", primary: "#017B48", secondary: "#FFFFFF" },
  "rangers": { abbr: "RAN", id: "143", league: "sco.1", primary: "#0000FF", secondary: "#FFFFFF" },
  "rangers fc": { abbr: "RAN", id: "143", league: "sco.1", primary: "#0000FF", secondary: "#FFFFFF" },
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Detect sport from team name if not provided
 */
function detectSport(teamName: string): string {
  const name = teamName.toLowerCase().trim()
  
  // Check each sport's team list
  if (NFL_TEAMS[name]) return "nfl"
  if (NBA_TEAMS[name]) return "nba"
  if (NHL_TEAMS[name]) return "nhl"
  if (MLB_TEAMS[name]) return "mlb"
  if (NCAAF_TEAMS[name]) return "ncaaf"
  if (NCAAB_TEAMS[name]) return "ncaab"
  if (SOCCER_TEAMS[name]) return "soccer"
  
  // Default to NFL if not found
  return "nfl"
}

/**
 * Team info type that can include optional id and league
 */
interface TeamInfo {
  abbr: string
  primary: string
  secondary: string
  id?: string
  league?: string
}

/**
 * Get team info (abbreviation, colors, and ESPN ID) for a given team and sport
 */
function getTeamInfo(teamName: string, sport: string): TeamInfo | null {
  const name = teamName.toLowerCase().trim()
  const sportLower = sport.toLowerCase()
  
  switch (sportLower) {
    case "nfl":
      return NFL_TEAMS[name] || null
    case "nba":
      return NBA_TEAMS[name] || null
    case "nhl":
      return NHL_TEAMS[name] || null
    case "mlb":
      return MLB_TEAMS[name] || null
    case "ncaaf":
    case "cfb":
    case "college football":
      return NCAAF_TEAMS[name] || null
    case "ncaab":
    case "cbb":
    case "college basketball":
      return NCAAB_TEAMS[name] || null
    case "soccer":
    case "mls":
    case "epl":
    case "laliga":
    case "ucl":
      return SOCCER_TEAMS[name] || null
    default:
      // Try all sports
      return NFL_TEAMS[name] || NBA_TEAMS[name] || NHL_TEAMS[name] || MLB_TEAMS[name] || 
             NCAAF_TEAMS[name] || NCAAB_TEAMS[name] || SOCCER_TEAMS[name] || null
  }
}

/**
 * Get ESPN logo URL for a team
 */
function getTeamLogoUrl(teamName: string, sport: string): string | null {
  const name = teamName.toLowerCase().trim()
  const sportLower = sport.toLowerCase()
  
  // Get team info based on sport
  let teamInfo: TeamInfo | null = null
  
  switch (sportLower) {
    case "nfl":
      teamInfo = NFL_TEAMS[name]
      if (teamInfo) {
        return `https://a.espncdn.com/i/teamlogos/nfl/500/${teamInfo.abbr.toLowerCase()}.png`
      }
      break
    case "nba":
      teamInfo = NBA_TEAMS[name]
      if (teamInfo) {
        return `https://a.espncdn.com/i/teamlogos/nba/500/${teamInfo.abbr.toLowerCase()}.png`
      }
      break
    case "nhl":
      teamInfo = NHL_TEAMS[name]
      if (teamInfo) {
        return `https://a.espncdn.com/i/teamlogos/nhl/500/${teamInfo.abbr.toLowerCase()}.png`
      }
      break
    case "mlb":
      teamInfo = MLB_TEAMS[name]
      if (teamInfo) {
        return `https://a.espncdn.com/i/teamlogos/mlb/500/${teamInfo.abbr.toLowerCase()}.png`
      }
      break
    case "ncaaf":
    case "cfb":
    case "college football":
      teamInfo = NCAAF_TEAMS[name]
      if (teamInfo && teamInfo.id) {
        // College teams use numeric IDs
        return `https://a.espncdn.com/i/teamlogos/ncaa/500/${teamInfo.id}.png`
      }
      break
    case "ncaab":
    case "cbb":
    case "college basketball":
      teamInfo = NCAAB_TEAMS[name]
      if (teamInfo && teamInfo.id) {
        // College teams use numeric IDs
        return `https://a.espncdn.com/i/teamlogos/ncaa/500/${teamInfo.id}.png`
      }
      break
    case "soccer":
    case "mls":
    case "epl":
    case "laliga":
    case "ucl":
      teamInfo = SOCCER_TEAMS[name]
      if (teamInfo && teamInfo.id) {
        // Soccer teams use numeric IDs with league-specific paths
        return `https://a.espncdn.com/i/teamlogos/soccer/500/${teamInfo.id}.png`
      }
      break
  }
  
  return null
}

/**
 * Get fallback abbreviation from team name
 */
function getFallbackAbbr(teamName: string): string {
  const words = teamName.trim().split(" ")
  if (words.length >= 2) {
    // Use last word's first 2-3 letters (usually the team name)
    const lastWord = words[words.length - 1]
    return lastWord.substring(0, Math.min(3, lastWord.length)).toUpperCase()
  }
  return teamName.substring(0, Math.min(3, teamName.length)).toUpperCase()
}

// ============================================================================
// COMPONENT
// ============================================================================

const sizeMap = {
  sm: "h-8 w-8 text-xs",
  md: "h-12 w-12 text-sm",
  lg: "h-16 w-16 text-base",
}

export function TeamLogo({ 
  teamName, 
  sport, 
  size = "md", 
  className, 
  showImage = true 
}: TeamLogoProps) {
  // Auto-detect sport if not provided
  const detectedSport = sport || detectSport(teamName)
  
  // Get team info
  const teamInfo = getTeamInfo(teamName, detectedSport)
  const abbr = teamInfo?.abbr?.toUpperCase() || getFallbackAbbr(teamName)
  const colors = teamInfo 
    ? { primary: teamInfo.primary, secondary: teamInfo.secondary }
    : { primary: "#1E293B", secondary: "#38BDF8" }
  
  // Get logo URL
  const logoUrl = getTeamLogoUrl(teamName, detectedSport)
  
  const [imageError, setImageError] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  
  // Reset image state when team changes
  useState(() => {
    setImageError(false)
    setImageLoaded(false)
  })
  
  // Show actual logo if enabled and available
  if (showImage && logoUrl && !imageError) {
    return (
      <motion.div
        className={cn(
          "relative flex items-center justify-center rounded-full overflow-hidden",
          sizeMap[size],
          className
        )}
        style={{
          background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`,
          boxShadow: `0 0 15px ${colors.primary}60`,
        }}
        whileHover={{ scale: 1.1 }}
        transition={{ duration: 0.2 }}
      >
        {/* Loading skeleton */}
        {!imageLoaded && (
          <div className="absolute inset-0 bg-gradient-to-r from-gray-700 via-gray-600 to-gray-700 animate-pulse" />
        )}
        
        {/* Actual logo */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={logoUrl}
          alt={teamName}
          className={cn(
            "w-full h-full object-contain p-1 transition-opacity duration-300",
            imageLoaded ? "opacity-100" : "opacity-0"
          )}
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageError(true)}
          loading="lazy"
        />
        
        {/* Glow effect */}
        <motion.div
          className="absolute inset-0 rounded-full opacity-0 blur-xl pointer-events-none"
          style={{ backgroundColor: colors.primary }}
          whileHover={{ opacity: 0.4 }}
          transition={{ duration: 0.3 }}
        />
      </motion.div>
    )
  }
  
  // Fallback to abbreviation-based logo
  return (
    <motion.div
      className={cn(
        "relative flex items-center justify-center rounded-full font-bold text-white",
        sizeMap[size],
        className
      )}
      style={{
        background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`,
        boxShadow: `0 0 20px ${colors.primary}80, inset 0 0 20px ${colors.secondary}40`,
      }}
      whileHover={{ scale: 1.1, rotate: 5 }}
      transition={{ duration: 0.2 }}
    >
      <span className="relative z-10 drop-shadow-lg">{abbr}</span>
      
      {/* Glow effect */}
      <motion.div
        className="absolute inset-0 rounded-full opacity-0 blur-xl"
        style={{ backgroundColor: colors.primary }}
        whileHover={{ opacity: 0.6 }}
        transition={{ duration: 0.3 }}
      />
    </motion.div>
  )
}
