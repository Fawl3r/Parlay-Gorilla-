/**
 * Centralized team styles map for all sports.
 * 
 * This file provides team abbreviations and colors ONLY.
 * NO logos, NO images, NO trademarked graphics.
 * 
 * Legal compliance: Team names and abbreviations are used solely for identification purposes.
 */

export interface TeamStyle {
  label: string // Abbreviation (e.g., "GB", "CHI")
  primary: string // Primary color hex
  secondary: string // Secondary color hex
  name?: string // Full team name for text display
}

export type TeamStylesMap = Record<string, TeamStyle>

// ============================================================================
// NFL TEAMS
// ============================================================================
const NFL_TEAMS: TeamStylesMap = {
  "san francisco 49ers": { label: "SF", primary: "#AA0000", secondary: "#B3995D", name: "San Francisco 49ers" },
  "49ers": { label: "SF", primary: "#AA0000", secondary: "#B3995D", name: "San Francisco 49ers" },
  "chicago bears": { label: "CHI", primary: "#0B162A", secondary: "#C83803", name: "Chicago Bears" },
  "bears": { label: "CHI", primary: "#0B162A", secondary: "#C83803", name: "Chicago Bears" },
  "cincinnati bengals": { label: "CIN", primary: "#FB4F14", secondary: "#000000", name: "Cincinnati Bengals" },
  "bengals": { label: "CIN", primary: "#FB4F14", secondary: "#000000", name: "Cincinnati Bengals" },
  "buffalo bills": { label: "BUF", primary: "#00338D", secondary: "#C60C30", name: "Buffalo Bills" },
  "bills": { label: "BUF", primary: "#00338D", secondary: "#C60C30", name: "Buffalo Bills" },
  "denver broncos": { label: "DEN", primary: "#FB4F14", secondary: "#002244", name: "Denver Broncos" },
  "broncos": { label: "DEN", primary: "#FB4F14", secondary: "#002244", name: "Denver Broncos" },
  "cleveland browns": { label: "CLE", primary: "#311D00", secondary: "#FF3C00", name: "Cleveland Browns" },
  "browns": { label: "CLE", primary: "#311D00", secondary: "#FF3C00", name: "Cleveland Browns" },
  "tampa bay buccaneers": { label: "TB", primary: "#D50A0A", secondary: "#FF7900", name: "Tampa Bay Buccaneers" },
  "buccaneers": { label: "TB", primary: "#D50A0A", secondary: "#FF7900", name: "Tampa Bay Buccaneers" },
  "arizona cardinals": { label: "ARI", primary: "#97233F", secondary: "#000000", name: "Arizona Cardinals" },
  "cardinals": { label: "ARI", primary: "#97233F", secondary: "#000000", name: "Arizona Cardinals" },
  "los angeles chargers": { label: "LAC", primary: "#0080C6", secondary: "#FFC20E", name: "Los Angeles Chargers" },
  "chargers": { label: "LAC", primary: "#0080C6", secondary: "#FFC20E", name: "Los Angeles Chargers" },
  "kansas city chiefs": { label: "KC", primary: "#E31837", secondary: "#FFB81C", name: "Kansas City Chiefs" },
  "chiefs": { label: "KC", primary: "#E31837", secondary: "#FFB81C", name: "Kansas City Chiefs" },
  "indianapolis colts": { label: "IND", primary: "#002C5F", secondary: "#A2AAAD", name: "Indianapolis Colts" },
  "colts": { label: "IND", primary: "#002C5F", secondary: "#A2AAAD", name: "Indianapolis Colts" },
  "dallas cowboys": { label: "DAL", primary: "#003594", secondary: "#869397", name: "Dallas Cowboys" },
  "cowboys": { label: "DAL", primary: "#003594", secondary: "#869397", name: "Dallas Cowboys" },
  "miami dolphins": { label: "MIA", primary: "#008E97", secondary: "#FC4C02", name: "Miami Dolphins" },
  "dolphins": { label: "MIA", primary: "#008E97", secondary: "#FC4C02", name: "Miami Dolphins" },
  "philadelphia eagles": { label: "PHI", primary: "#004C54", secondary: "#A5ACAF", name: "Philadelphia Eagles" },
  "eagles": { label: "PHI", primary: "#004C54", secondary: "#A5ACAF", name: "Philadelphia Eagles" },
  "atlanta falcons": { label: "ATL", primary: "#A71930", secondary: "#000000", name: "Atlanta Falcons" },
  "falcons": { label: "ATL", primary: "#A71930", secondary: "#000000", name: "Atlanta Falcons" },
  "new york giants": { label: "NYG", primary: "#0B2265", secondary: "#A71930", name: "New York Giants" },
  "giants": { label: "NYG", primary: "#0B2265", secondary: "#A71930", name: "New York Giants" },
  "jacksonville jaguars": { label: "JAX", primary: "#006778", secondary: "#9F792C", name: "Jacksonville Jaguars" },
  "jaguars": { label: "JAX", primary: "#006778", secondary: "#9F792C", name: "Jacksonville Jaguars" },
  "new york jets": { label: "NYJ", primary: "#125740", secondary: "#000000", name: "New York Jets" },
  "jets": { label: "NYJ", primary: "#125740", secondary: "#000000", name: "New York Jets" },
  "detroit lions": { label: "DET", primary: "#0076B6", secondary: "#B0B7BC", name: "Detroit Lions" },
  "lions": { label: "DET", primary: "#0076B6", secondary: "#B0B7BC", name: "Detroit Lions" },
  "green bay packers": { label: "GB", primary: "#203731", secondary: "#FFB612", name: "Green Bay Packers" },
  "packers": { label: "GB", primary: "#203731", secondary: "#FFB612", name: "Green Bay Packers" },
  "carolina panthers": { label: "CAR", primary: "#0085CA", secondary: "#101820", name: "Carolina Panthers" },
  "panthers": { label: "CAR", primary: "#0085CA", secondary: "#101820", name: "Carolina Panthers" },
  "new england patriots": { label: "NE", primary: "#002244", secondary: "#C60C30", name: "New England Patriots" },
  "patriots": { label: "NE", primary: "#002244", secondary: "#C60C30", name: "New England Patriots" },
  "las vegas raiders": { label: "LV", primary: "#000000", secondary: "#A5ACAF", name: "Las Vegas Raiders" },
  "raiders": { label: "LV", primary: "#000000", secondary: "#A5ACAF", name: "Las Vegas Raiders" },
  "los angeles rams": { label: "LAR", primary: "#003594", secondary: "#FFA300", name: "Los Angeles Rams" },
  "rams": { label: "LAR", primary: "#003594", secondary: "#FFA300", name: "Los Angeles Rams" },
  "baltimore ravens": { label: "BAL", primary: "#241773", secondary: "#9E7C0C", name: "Baltimore Ravens" },
  "ravens": { label: "BAL", primary: "#241773", secondary: "#9E7C0C", name: "Baltimore Ravens" },
  "new orleans saints": { label: "NO", primary: "#D3BC8D", secondary: "#101820", name: "New Orleans Saints" },
  "saints": { label: "NO", primary: "#D3BC8D", secondary: "#101820", name: "New Orleans Saints" },
  "seattle seahawks": { label: "SEA", primary: "#002244", secondary: "#69BE28", name: "Seattle Seahawks" },
  "seahawks": { label: "SEA", primary: "#002244", secondary: "#69BE28", name: "Seattle Seahawks" },
  "pittsburgh steelers": { label: "PIT", primary: "#000000", secondary: "#FFB612", name: "Pittsburgh Steelers" },
  "steelers": { label: "PIT", primary: "#000000", secondary: "#FFB612", name: "Pittsburgh Steelers" },
  "houston texans": { label: "HOU", primary: "#03202F", secondary: "#A71930", name: "Houston Texans" },
  "texans": { label: "HOU", primary: "#03202F", secondary: "#A71930", name: "Houston Texans" },
  "tennessee titans": { label: "TEN", primary: "#0C2340", secondary: "#4B92DB", name: "Tennessee Titans" },
  "titans": { label: "TEN", primary: "#0C2340", secondary: "#4B92DB", name: "Tennessee Titans" },
  "minnesota vikings": { label: "MIN", primary: "#4F2683", secondary: "#FFC62F", name: "Minnesota Vikings" },
  "vikings": { label: "MIN", primary: "#4F2683", secondary: "#FFC62F", name: "Minnesota Vikings" },
  "washington commanders": { label: "WSH", primary: "#5A1414", secondary: "#FFB612", name: "Washington Commanders" },
  "commanders": { label: "WSH", primary: "#5A1414", secondary: "#FFB612", name: "Washington Commanders" },
}

// ============================================================================
// NBA TEAMS (abbreviated - expand as needed)
// ============================================================================
const NBA_TEAMS: TeamStylesMap = {
  "atlanta hawks": { label: "ATL", primary: "#E03A3E", secondary: "#C1D32F", name: "Atlanta Hawks" },
  "hawks": { label: "ATL", primary: "#E03A3E", secondary: "#C1D32F", name: "Atlanta Hawks" },
  "boston celtics": { label: "BOS", primary: "#007A33", secondary: "#BA9653", name: "Boston Celtics" },
  "celtics": { label: "BOS", primary: "#007A33", secondary: "#BA9653", name: "Boston Celtics" },
  "brooklyn nets": { label: "BKN", primary: "#000000", secondary: "#FFFFFF", name: "Brooklyn Nets" },
  "nets": { label: "BKN", primary: "#000000", secondary: "#FFFFFF", name: "Brooklyn Nets" },
  "charlotte hornets": { label: "CHA", primary: "#1D1160", secondary: "#00788C", name: "Charlotte Hornets" },
  "hornets": { label: "CHA", primary: "#1D1160", secondary: "#00788C", name: "Charlotte Hornets" },
  "chicago bulls": { label: "CHI", primary: "#CE1141", secondary: "#000000", name: "Chicago Bulls" },
  "bulls": { label: "CHI", primary: "#CE1141", secondary: "#000000", name: "Chicago Bulls" },
  "cleveland cavaliers": { label: "CLE", primary: "#860038", secondary: "#FDBB30", name: "Cleveland Cavaliers" },
  "cavaliers": { label: "CLE", primary: "#860038", secondary: "#FDBB30", name: "Cleveland Cavaliers" },
  "cavs": { label: "CLE", primary: "#860038", secondary: "#FDBB30", name: "Cleveland Cavaliers" },
  "dallas mavericks": { label: "DAL", primary: "#00538C", secondary: "#002B5C", name: "Dallas Mavericks" },
  "mavericks": { label: "DAL", primary: "#00538C", secondary: "#002B5C", name: "Dallas Mavericks" },
  "mavs": { label: "DAL", primary: "#00538C", secondary: "#002B5C", name: "Dallas Mavericks" },
  "denver nuggets": { label: "DEN", primary: "#0E2240", secondary: "#FEC524", name: "Denver Nuggets" },
  "nuggets": { label: "DEN", primary: "#0E2240", secondary: "#FEC524", name: "Denver Nuggets" },
  "detroit pistons": { label: "DET", primary: "#C8102E", secondary: "#1D42BA", name: "Detroit Pistons" },
  "pistons": { label: "DET", primary: "#C8102E", secondary: "#1D42BA", name: "Detroit Pistons" },
  "golden state warriors": { label: "GS", primary: "#1D428A", secondary: "#FFC72C", name: "Golden State Warriors" },
  "warriors": { label: "GS", primary: "#1D428A", secondary: "#FFC72C", name: "Golden State Warriors" },
  "houston rockets": { label: "HOU", primary: "#CE1141", secondary: "#000000", name: "Houston Rockets" },
  "rockets": { label: "HOU", primary: "#CE1141", secondary: "#000000", name: "Houston Rockets" },
  "indiana pacers": { label: "IND", primary: "#002D62", secondary: "#FDBB30", name: "Indiana Pacers" },
  "pacers": { label: "IND", primary: "#002D62", secondary: "#FDBB30", name: "Indiana Pacers" },
  "los angeles clippers": { label: "LAC", primary: "#C8102E", secondary: "#1D428A", name: "Los Angeles Clippers" },
  "clippers": { label: "LAC", primary: "#C8102E", secondary: "#1D428A", name: "Los Angeles Clippers" },
  "la clippers": { label: "LAC", primary: "#C8102E", secondary: "#1D428A", name: "Los Angeles Clippers" },
  "los angeles lakers": { label: "LAL", primary: "#552583", secondary: "#FDB927", name: "Los Angeles Lakers" },
  "lakers": { label: "LAL", primary: "#552583", secondary: "#FDB927", name: "Los Angeles Lakers" },
  "la lakers": { label: "LAL", primary: "#552583", secondary: "#FDB927", name: "Los Angeles Lakers" },
  "memphis grizzlies": { label: "MEM", primary: "#5D76A9", secondary: "#12173F", name: "Memphis Grizzlies" },
  "grizzlies": { label: "MEM", primary: "#5D76A9", secondary: "#12173F", name: "Memphis Grizzlies" },
  "miami heat": { label: "MIA", primary: "#98002E", secondary: "#F9A01B", name: "Miami Heat" },
  "heat": { label: "MIA", primary: "#98002E", secondary: "#F9A01B", name: "Miami Heat" },
  "milwaukee bucks": { label: "MIL", primary: "#00471B", secondary: "#EEE1C6", name: "Milwaukee Bucks" },
  "bucks": { label: "MIL", primary: "#00471B", secondary: "#EEE1C6", name: "Milwaukee Bucks" },
  "minnesota timberwolves": { label: "MIN", primary: "#0C2340", secondary: "#236192", name: "Minnesota Timberwolves" },
  "timberwolves": { label: "MIN", primary: "#0C2340", secondary: "#236192", name: "Minnesota Timberwolves" },
  "wolves": { label: "MIN", primary: "#0C2340", secondary: "#236192", name: "Minnesota Timberwolves" },
  "new orleans pelicans": { label: "NO", primary: "#0C2340", secondary: "#C8102E", name: "New Orleans Pelicans" },
  "pelicans": { label: "NO", primary: "#0C2340", secondary: "#C8102E", name: "New Orleans Pelicans" },
  "new york knicks": { label: "NY", primary: "#006BB6", secondary: "#F58426", name: "New York Knicks" },
  "knicks": { label: "NY", primary: "#006BB6", secondary: "#F58426", name: "New York Knicks" },
  "oklahoma city thunder": { label: "OKC", primary: "#007AC1", secondary: "#EF3B24", name: "Oklahoma City Thunder" },
  "thunder": { label: "OKC", primary: "#007AC1", secondary: "#EF3B24", name: "Oklahoma City Thunder" },
  "orlando magic": { label: "ORL", primary: "#0077C0", secondary: "#C4CED4", name: "Orlando Magic" },
  "magic": { label: "ORL", primary: "#0077C0", secondary: "#C4CED4", name: "Orlando Magic" },
  "philadelphia 76ers": { label: "PHI", primary: "#006BB6", secondary: "#ED174C", name: "Philadelphia 76ers" },
  "76ers": { label: "PHI", primary: "#006BB6", secondary: "#ED174C", name: "Philadelphia 76ers" },
  "sixers": { label: "PHI", primary: "#006BB6", secondary: "#ED174C", name: "Philadelphia 76ers" },
  "phoenix suns": { label: "PHX", primary: "#1D1160", secondary: "#E56020", name: "Phoenix Suns" },
  "suns": { label: "PHX", primary: "#1D1160", secondary: "#E56020", name: "Phoenix Suns" },
  "portland trail blazers": { label: "POR", primary: "#E03A3E", secondary: "#000000", name: "Portland Trail Blazers" },
  "trail blazers": { label: "POR", primary: "#E03A3E", secondary: "#000000", name: "Portland Trail Blazers" },
  "blazers": { label: "POR", primary: "#E03A3E", secondary: "#000000", name: "Portland Trail Blazers" },
  "sacramento kings": { label: "SAC", primary: "#5A2D81", secondary: "#63727A", name: "Sacramento Kings" },
  "kings": { label: "SAC", primary: "#5A2D81", secondary: "#63727A", name: "Sacramento Kings" },
  "san antonio spurs": { label: "SA", primary: "#C4CED4", secondary: "#000000", name: "San Antonio Spurs" },
  "spurs": { label: "SA", primary: "#C4CED4", secondary: "#000000", name: "San Antonio Spurs" },
  "toronto raptors": { label: "TOR", primary: "#CE1141", secondary: "#000000", name: "Toronto Raptors" },
  "raptors": { label: "TOR", primary: "#CE1141", secondary: "#000000", name: "Toronto Raptors" },
  "utah jazz": { label: "UTAH", primary: "#002B5C", secondary: "#00471B", name: "Utah Jazz" },
  "jazz": { label: "UTAH", primary: "#002B5C", secondary: "#00471B", name: "Utah Jazz" },
  "washington wizards": { label: "WSH", primary: "#002B5C", secondary: "#E31837", name: "Washington Wizards" },
  "wizards": { label: "WSH", primary: "#002B5C", secondary: "#E31837", name: "Washington Wizards" },
}

// ============================================================================
// NHL TEAMS (abbreviated - expand as needed)
// ============================================================================
const NHL_TEAMS: TeamStylesMap = {
  "anaheim ducks": { label: "ANA", primary: "#F47A38", secondary: "#B9975B", name: "Anaheim Ducks" },
  "ducks": { label: "ANA", primary: "#F47A38", secondary: "#B9975B", name: "Anaheim Ducks" },
  "arizona coyotes": { label: "ARI", primary: "#8C2633", secondary: "#E2D6B5", name: "Arizona Coyotes" },
  "coyotes": { label: "ARI", primary: "#8C2633", secondary: "#E2D6B5", name: "Arizona Coyotes" },
  "boston bruins": { label: "BOS", primary: "#FFB81C", secondary: "#000000", name: "Boston Bruins" },
  "bruins": { label: "BOS", primary: "#FFB81C", secondary: "#000000", name: "Boston Bruins" },
  "buffalo sabres": { label: "BUF", primary: "#002654", secondary: "#FCB514", name: "Buffalo Sabres" },
  "sabres": { label: "BUF", primary: "#002654", secondary: "#FCB514", name: "Buffalo Sabres" },
  "calgary flames": { label: "CGY", primary: "#C8102E", secondary: "#F1BE48", name: "Calgary Flames" },
  "flames": { label: "CGY", primary: "#C8102E", secondary: "#F1BE48", name: "Calgary Flames" },
  "carolina hurricanes": { label: "CAR", primary: "#CC0000", secondary: "#000000", name: "Carolina Hurricanes" },
  "hurricanes": { label: "CAR", primary: "#CC0000", secondary: "#000000", name: "Carolina Hurricanes" },
  "chicago blackhawks": { label: "CHI", primary: "#CF0A2C", secondary: "#000000", name: "Chicago Blackhawks" },
  "blackhawks": { label: "CHI", primary: "#CF0A2C", secondary: "#000000", name: "Chicago Blackhawks" },
  "colorado avalanche": { label: "COL", primary: "#6F263D", secondary: "#236192", name: "Colorado Avalanche" },
  "avalanche": { label: "COL", primary: "#6F263D", secondary: "#236192", name: "Colorado Avalanche" },
  "columbus blue jackets": { label: "CBJ", primary: "#002654", secondary: "#CE1126", name: "Columbus Blue Jackets" },
  "blue jackets": { label: "CBJ", primary: "#002654", secondary: "#CE1126", name: "Columbus Blue Jackets" },
  "dallas stars": { label: "DAL", primary: "#006847", secondary: "#8F8F8C", name: "Dallas Stars" },
  "stars": { label: "DAL", primary: "#006847", secondary: "#8F8F8C", name: "Dallas Stars" },
  "detroit red wings": { label: "DET", primary: "#CE1126", secondary: "#FFFFFF", name: "Detroit Red Wings" },
  "red wings": { label: "DET", primary: "#CE1126", secondary: "#FFFFFF", name: "Detroit Red Wings" },
  "edmonton oilers": { label: "EDM", primary: "#041E42", secondary: "#FF4C00", name: "Edmonton Oilers" },
  "oilers": { label: "EDM", primary: "#041E42", secondary: "#FF4C00", name: "Edmonton Oilers" },
  "florida panthers": { label: "FLA", primary: "#041E42", secondary: "#C8102E", name: "Florida Panthers" },
  "panthers": { label: "FLA", primary: "#041E42", secondary: "#C8102E", name: "Florida Panthers" },
  "los angeles kings": { label: "LA", primary: "#111111", secondary: "#A2AAAD", name: "Los Angeles Kings" },
  "kings": { label: "LA", primary: "#111111", secondary: "#A2AAAD", name: "Los Angeles Kings" },
  "minnesota wild": { label: "MIN", primary: "#154734", secondary: "#A6192E", name: "Minnesota Wild" },
  "wild": { label: "MIN", primary: "#154734", secondary: "#A6192E", name: "Minnesota Wild" },
  "montreal canadiens": { label: "MTL", primary: "#AF1E2D", secondary: "#192168", name: "Montreal Canadiens" },
  "canadiens": { label: "MTL", primary: "#AF1E2D", secondary: "#192168", name: "Montreal Canadiens" },
  "nashville predators": { label: "NSH", primary: "#FFB81C", secondary: "#041E42", name: "Nashville Predators" },
  "predators": { label: "NSH", primary: "#FFB81C", secondary: "#041E42", name: "Nashville Predators" },
  "new jersey devils": { label: "NJ", primary: "#CE1126", secondary: "#000000", name: "New Jersey Devils" },
  "devils": { label: "NJ", primary: "#CE1126", secondary: "#000000", name: "New Jersey Devils" },
  "new york islanders": { label: "NYI", primary: "#00539B", secondary: "#F47D30", name: "New York Islanders" },
  "islanders": { label: "NYI", primary: "#00539B", secondary: "#F47D30", name: "New York Islanders" },
  "new york rangers": { label: "NYR", primary: "#0038A8", secondary: "#CE1126", name: "New York Rangers" },
  "rangers": { label: "NYR", primary: "#0038A8", secondary: "#CE1126", name: "New York Rangers" },
  "ottawa senators": { label: "OTT", primary: "#C52032", secondary: "#C2912C", name: "Ottawa Senators" },
  "senators": { label: "OTT", primary: "#C52032", secondary: "#C2912C", name: "Ottawa Senators" },
  "philadelphia flyers": { label: "PHI", primary: "#F74902", secondary: "#000000", name: "Philadelphia Flyers" },
  "flyers": { label: "PHI", primary: "#F74902", secondary: "#000000", name: "Philadelphia Flyers" },
  "pittsburgh penguins": { label: "PIT", primary: "#000000", secondary: "#FCB514", name: "Pittsburgh Penguins" },
  "penguins": { label: "PIT", primary: "#000000", secondary: "#FCB514", name: "Pittsburgh Penguins" },
  "san jose sharks": { label: "SJ", primary: "#006D75", secondary: "#EA7200", name: "San Jose Sharks" },
  "sharks": { label: "SJ", primary: "#006D75", secondary: "#EA7200", name: "San Jose Sharks" },
  "seattle kraken": { label: "SEA", primary: "#001628", secondary: "#99D9D9", name: "Seattle Kraken" },
  "kraken": { label: "SEA", primary: "#001628", secondary: "#99D9D9", name: "Seattle Kraken" },
  "st. louis blues": { label: "STL", primary: "#002F87", secondary: "#FCB514", name: "St. Louis Blues" },
  "st louis blues": { label: "STL", primary: "#002F87", secondary: "#FCB514", name: "St. Louis Blues" },
  "saint louis blues": { label: "STL", primary: "#002F87", secondary: "#FCB514", name: "St. Louis Blues" },
  "blues": { label: "STL", primary: "#002F87", secondary: "#FCB514", name: "St. Louis Blues" },
  "tampa bay lightning": { label: "TB", primary: "#002868", secondary: "#FFFFFF", name: "Tampa Bay Lightning" },
  "lightning": { label: "TB", primary: "#002868", secondary: "#FFFFFF", name: "Tampa Bay Lightning" },
  "toronto maple leafs": { label: "TOR", primary: "#00205B", secondary: "#FFFFFF", name: "Toronto Maple Leafs" },
  "maple leafs": { label: "TOR", primary: "#00205B", secondary: "#FFFFFF", name: "Toronto Maple Leafs" },
  "utah hockey club": { label: "UTAH", primary: "#6CACE4", secondary: "#010101", name: "Utah Hockey Club" },
  "utah mammoths": { label: "UTAH", primary: "#6CACE4", secondary: "#010101", name: "Utah Hockey Club" },
  "utah mammoth": { label: "UTAH", primary: "#6CACE4", secondary: "#010101", name: "Utah Hockey Club" },
  "utah hc": { label: "UTAH", primary: "#6CACE4", secondary: "#010101", name: "Utah Hockey Club" },
  "vancouver canucks": { label: "VAN", primary: "#00205B", secondary: "#00843D", name: "Vancouver Canucks" },
  "canucks": { label: "VAN", primary: "#00205B", secondary: "#00843D", name: "Vancouver Canucks" },
  "vegas golden knights": { label: "VGK", primary: "#B4975A", secondary: "#333F42", name: "Vegas Golden Knights" },
  "golden knights": { label: "VGK", primary: "#B4975A", secondary: "#333F42", name: "Vegas Golden Knights" },
  "washington capitals": { label: "WSH", primary: "#C8102E", secondary: "#041E42", name: "Washington Capitals" },
  "capitals": { label: "WSH", primary: "#C8102E", secondary: "#041E42", name: "Washington Capitals" },
  "winnipeg jets": { label: "WPG", primary: "#041E42", secondary: "#004C97", name: "Winnipeg Jets" },
  "jets": { label: "WPG", primary: "#041E42", secondary: "#004C97", name: "Winnipeg Jets" },
}

// ============================================================================
// MLB TEAMS (abbreviated - expand as needed)
// ============================================================================
const MLB_TEAMS: TeamStylesMap = {
  "arizona diamondbacks": { label: "ARI", primary: "#A71930", secondary: "#E3D4AD", name: "Arizona Diamondbacks" },
  "diamondbacks": { label: "ARI", primary: "#A71930", secondary: "#E3D4AD", name: "Arizona Diamondbacks" },
  "d-backs": { label: "ARI", primary: "#A71930", secondary: "#E3D4AD", name: "Arizona Diamondbacks" },
  "atlanta braves": { label: "ATL", primary: "#CE1141", secondary: "#13274F", name: "Atlanta Braves" },
  "braves": { label: "ATL", primary: "#CE1141", secondary: "#13274F", name: "Atlanta Braves" },
  "baltimore orioles": { label: "BAL", primary: "#DF4601", secondary: "#000000", name: "Baltimore Orioles" },
  "orioles": { label: "BAL", primary: "#DF4601", secondary: "#000000", name: "Baltimore Orioles" },
  "boston red sox": { label: "BOS", primary: "#BD3039", secondary: "#0C2340", name: "Boston Red Sox" },
  "red sox": { label: "BOS", primary: "#BD3039", secondary: "#0C2340", name: "Boston Red Sox" },
  "chicago cubs": { label: "CHC", primary: "#0E3386", secondary: "#CC3433", name: "Chicago Cubs" },
  "cubs": { label: "CHC", primary: "#0E3386", secondary: "#CC3433", name: "Chicago Cubs" },
  "chicago white sox": { label: "CHW", primary: "#27251F", secondary: "#C4CED4", name: "Chicago White Sox" },
  "white sox": { label: "CHW", primary: "#27251F", secondary: "#C4CED4", name: "Chicago White Sox" },
  "cincinnati reds": { label: "CIN", primary: "#C6011F", secondary: "#000000", name: "Cincinnati Reds" },
  "reds": { label: "CIN", primary: "#C6011F", secondary: "#000000", name: "Cincinnati Reds" },
  "cleveland guardians": { label: "CLE", primary: "#00385D", secondary: "#E50022", name: "Cleveland Guardians" },
  "guardians": { label: "CLE", primary: "#00385D", secondary: "#E50022", name: "Cleveland Guardians" },
  "colorado rockies": { label: "COL", primary: "#33006F", secondary: "#C4CED4", name: "Colorado Rockies" },
  "rockies": { label: "COL", primary: "#33006F", secondary: "#C4CED4", name: "Colorado Rockies" },
  "detroit tigers": { label: "DET", primary: "#0C2340", secondary: "#FA4616", name: "Detroit Tigers" },
  "tigers": { label: "DET", primary: "#0C2340", secondary: "#FA4616", name: "Detroit Tigers" },
  "houston astros": { label: "HOU", primary: "#002D62", secondary: "#EB6E1F", name: "Houston Astros" },
  "astros": { label: "HOU", primary: "#002D62", secondary: "#EB6E1F", name: "Houston Astros" },
  "kansas city royals": { label: "KC", primary: "#004687", secondary: "#BD9B60", name: "Kansas City Royals" },
  "royals": { label: "KC", primary: "#004687", secondary: "#BD9B60", name: "Kansas City Royals" },
  "los angeles angels": { label: "LAA", primary: "#BA0021", secondary: "#003263", name: "Los Angeles Angels" },
  "angels": { label: "LAA", primary: "#BA0021", secondary: "#003263", name: "Los Angeles Angels" },
  "los angeles dodgers": { label: "LAD", primary: "#005A9C", secondary: "#EF3E42", name: "Los Angeles Dodgers" },
  "dodgers": { label: "LAD", primary: "#005A9C", secondary: "#EF3E42", name: "Los Angeles Dodgers" },
  "miami marlins": { label: "MIA", primary: "#00A3E0", secondary: "#EF3340", name: "Miami Marlins" },
  "marlins": { label: "MIA", primary: "#00A3E0", secondary: "#EF3340", name: "Miami Marlins" },
  "milwaukee brewers": { label: "MIL", primary: "#12284B", secondary: "#B6922E", name: "Milwaukee Brewers" },
  "brewers": { label: "MIL", primary: "#12284B", secondary: "#B6922E", name: "Milwaukee Brewers" },
  "minnesota twins": { label: "MIN", primary: "#002B5C", secondary: "#D31145", name: "Minnesota Twins" },
  "twins": { label: "MIN", primary: "#002B5C", secondary: "#D31145", name: "Minnesota Twins" },
  "new york mets": { label: "NYM", primary: "#002D72", secondary: "#FF5910", name: "New York Mets" },
  "mets": { label: "NYM", primary: "#002D72", secondary: "#FF5910", name: "New York Mets" },
  "new york yankees": { label: "NYY", primary: "#003087", secondary: "#E4002C", name: "New York Yankees" },
  "yankees": { label: "NYY", primary: "#003087", secondary: "#E4002C", name: "New York Yankees" },
  "oakland athletics": { label: "OAK", primary: "#003831", secondary: "#EFB21E", name: "Oakland Athletics" },
  "athletics": { label: "OAK", primary: "#003831", secondary: "#EFB21E", name: "Oakland Athletics" },
  "a's": { label: "OAK", primary: "#003831", secondary: "#EFB21E", name: "Oakland Athletics" },
  "philadelphia phillies": { label: "PHI", primary: "#E81828", secondary: "#002D72", name: "Philadelphia Phillies" },
  "phillies": { label: "PHI", primary: "#E81828", secondary: "#002D72", name: "Philadelphia Phillies" },
  "pittsburgh pirates": { label: "PIT", primary: "#27251F", secondary: "#FDB827", name: "Pittsburgh Pirates" },
  "pirates": { label: "PIT", primary: "#27251F", secondary: "#FDB827", name: "Pittsburgh Pirates" },
  "san diego padres": { label: "SD", primary: "#2F241D", secondary: "#FFC425", name: "San Diego Padres" },
  "padres": { label: "SD", primary: "#2F241D", secondary: "#FFC425", name: "San Diego Padres" },
  "san francisco giants": { label: "SF", primary: "#FD5A1E", secondary: "#27251F", name: "San Francisco Giants" },
  "giants": { label: "SF", primary: "#FD5A1E", secondary: "#27251F", name: "San Francisco Giants" },
  "seattle mariners": { label: "SEA", primary: "#0C2C56", secondary: "#005C5C", name: "Seattle Mariners" },
  "mariners": { label: "SEA", primary: "#0C2C56", secondary: "#005C5C", name: "Seattle Mariners" },
  "st. louis cardinals": { label: "STL", primary: "#C41E3A", secondary: "#0C2340", name: "St. Louis Cardinals" },
  "cardinals": { label: "STL", primary: "#C41E3A", secondary: "#0C2340", name: "St. Louis Cardinals" },
  "tampa bay rays": { label: "TB", primary: "#092C5C", secondary: "#8FBCE6", name: "Tampa Bay Rays" },
  "rays": { label: "TB", primary: "#092C5C", secondary: "#8FBCE6", name: "Tampa Bay Rays" },
  "texas rangers": { label: "TEX", primary: "#003278", secondary: "#C0111F", name: "Texas Rangers" },
  "rangers": { label: "TEX", primary: "#003278", secondary: "#C0111F", name: "Texas Rangers" },
  "toronto blue jays": { label: "TOR", primary: "#134A8E", secondary: "#1D2D5C", name: "Toronto Blue Jays" },
  "blue jays": { label: "TOR", primary: "#134A8E", secondary: "#1D2D5C", name: "Toronto Blue Jays" },
  "washington nationals": { label: "WSH", primary: "#AB0003", secondary: "#14225A", name: "Washington Nationals" },
  "nationals": { label: "WSH", primary: "#AB0003", secondary: "#14225A", name: "Washington Nationals" },
}

// ============================================================================
// COLLEGE FOOTBALL & BASKETBALL (abbreviated - expand as needed)
// ============================================================================
const NCAA_TEAMS: TeamStylesMap = {
  "alabama crimson tide": { label: "ALA", primary: "#9E1B32", secondary: "#828A8F", name: "Alabama Crimson Tide" },
  "alabama": { label: "ALA", primary: "#9E1B32", secondary: "#828A8F", name: "Alabama Crimson Tide" },
  "ohio state buckeyes": { label: "OSU", primary: "#BB0000", secondary: "#666666", name: "Ohio State Buckeyes" },
  "ohio state": { label: "OSU", primary: "#BB0000", secondary: "#666666", name: "Ohio State Buckeyes" },
  "georgia bulldogs": { label: "UGA", primary: "#BA0C2F", secondary: "#000000", name: "Georgia Bulldogs" },
  "georgia": { label: "UGA", primary: "#BA0C2F", secondary: "#000000", name: "Georgia Bulldogs" },
  "michigan wolverines": { label: "MICH", primary: "#00274C", secondary: "#FFCB05", name: "Michigan Wolverines" },
  "michigan": { label: "MICH", primary: "#00274C", secondary: "#FFCB05", name: "Michigan Wolverines" },
  "clemson tigers": { label: "CLEM", primary: "#F56600", secondary: "#522D80", name: "Clemson Tigers" },
  "clemson": { label: "CLEM", primary: "#F56600", secondary: "#522D80", name: "Clemson Tigers" },
  "texas longhorns": { label: "TEX", primary: "#BF5700", secondary: "#FFFFFF", name: "Texas Longhorns" },
  "texas": { label: "TEX", primary: "#BF5700", secondary: "#FFFFFF", name: "Texas Longhorns" },
  "usc trojans": { label: "USC", primary: "#990000", secondary: "#FFC72C", name: "USC Trojans" },
  "usc": { label: "USC", primary: "#990000", secondary: "#FFC72C", name: "USC Trojans" },
  "southern california": { label: "USC", primary: "#990000", secondary: "#FFC72C", name: "USC Trojans" },
  "notre dame fighting irish": { label: "ND", primary: "#0C2340", secondary: "#C99700", name: "Notre Dame Fighting Irish" },
  "notre dame": { label: "ND", primary: "#0C2340", secondary: "#C99700", name: "Notre Dame Fighting Irish" },
  "lsu tigers": { label: "LSU", primary: "#461D7C", secondary: "#FDD023", name: "LSU Tigers" },
  "lsu": { label: "LSU", primary: "#461D7C", secondary: "#FDD023", name: "LSU Tigers" },
  "oklahoma sooners": { label: "OU", primary: "#841617", secondary: "#FDF9D8", name: "Oklahoma Sooners" },
  "oklahoma": { label: "OU", primary: "#841617", secondary: "#FDF9D8", name: "Oklahoma Sooners" },
  "penn state nittany lions": { label: "PSU", primary: "#041E42", secondary: "#FFFFFF", name: "Penn State Nittany Lions" },
  "penn state": { label: "PSU", primary: "#041E42", secondary: "#FFFFFF", name: "Penn State Nittany Lions" },
  "florida gators": { label: "FLA", primary: "#0021A5", secondary: "#FA4616", name: "Florida Gators" },
  "florida": { label: "FLA", primary: "#0021A5", secondary: "#FA4616", name: "Florida Gators" },
  "oregon ducks": { label: "ORE", primary: "#154733", secondary: "#FEE123", name: "Oregon Ducks" },
  "oregon": { label: "ORE", primary: "#154733", secondary: "#FEE123", name: "Oregon Ducks" },
  "auburn tigers": { label: "AUB", primary: "#0C2340", secondary: "#E87722", name: "Auburn Tigers" },
  "auburn": { label: "AUB", primary: "#0C2340", secondary: "#E87722", name: "Auburn Tigers" },
  "tennessee volunteers": { label: "TENN", primary: "#FF8200", secondary: "#FFFFFF", name: "Tennessee Volunteers" },
  "tennessee": { label: "TENN", primary: "#FF8200", secondary: "#FFFFFF", name: "Tennessee Volunteers" },
  "miami hurricanes": { label: "MIA", primary: "#F47321", secondary: "#005030", name: "Miami Hurricanes" },
  "miami (fl)": { label: "MIA", primary: "#F47321", secondary: "#005030", name: "Miami Hurricanes" },
  "texas a&m aggies": { label: "TAMU", primary: "#500000", secondary: "#FFFFFF", name: "Texas A&M Aggies" },
  "texas a&m": { label: "TAMU", primary: "#500000", secondary: "#FFFFFF", name: "Texas A&M Aggies" },
  "wisconsin badgers": { label: "WIS", primary: "#C5050C", secondary: "#FFFFFF", name: "Wisconsin Badgers" },
  "wisconsin": { label: "WIS", primary: "#C5050C", secondary: "#FFFFFF", name: "Wisconsin Badgers" },
  "michigan state spartans": { label: "MSU", primary: "#18453B", secondary: "#FFFFFF", name: "Michigan State Spartans" },
  "michigan state": { label: "MSU", primary: "#18453B", secondary: "#FFFFFF", name: "Michigan State Spartans" },
  "florida state seminoles": { label: "FSU", primary: "#782F40", secondary: "#CEB888", name: "Florida State Seminoles" },
  "florida state": { label: "FSU", primary: "#782F40", secondary: "#CEB888", name: "Florida State Seminoles" },
  "iowa hawkeyes": { label: "IOWA", primary: "#FFCD00", secondary: "#000000", name: "Iowa Hawkeyes" },
  "iowa": { label: "IOWA", primary: "#FFCD00", secondary: "#000000", name: "Iowa Hawkeyes" },
  "washington huskies": { label: "WASH", primary: "#4B2E83", secondary: "#B7A57A", name: "Washington Huskies" },
  "washington": { label: "WASH", primary: "#4B2E83", secondary: "#B7A57A", name: "Washington Huskies" },
  "colorado buffaloes": { label: "COLO", primary: "#CFB87C", secondary: "#000000", name: "Colorado Buffaloes" },
  "colorado": { label: "COLO", primary: "#CFB87C", secondary: "#000000", name: "Colorado Buffaloes" },
  "duke blue devils": { label: "DUKE", primary: "#003087", secondary: "#FFFFFF", name: "Duke Blue Devils" },
  "duke": { label: "DUKE", primary: "#003087", secondary: "#FFFFFF", name: "Duke Blue Devils" },
  "north carolina tar heels": { label: "UNC", primary: "#7BAFD4", secondary: "#FFFFFF", name: "North Carolina Tar Heels" },
  "north carolina": { label: "UNC", primary: "#7BAFD4", secondary: "#FFFFFF", name: "North Carolina Tar Heels" },
  "unc": { label: "UNC", primary: "#7BAFD4", secondary: "#FFFFFF", name: "North Carolina Tar Heels" },
  "kentucky wildcats": { label: "UK", primary: "#0033A0", secondary: "#FFFFFF", name: "Kentucky Wildcats" },
  "kentucky": { label: "UK", primary: "#0033A0", secondary: "#FFFFFF", name: "Kentucky Wildcats" },
  "kansas jayhawks": { label: "KU", primary: "#0051BA", secondary: "#E8000D", name: "Kansas Jayhawks" },
  "kansas": { label: "KU", primary: "#0051BA", secondary: "#E8000D", name: "Kansas Jayhawks" },
  "ucla bruins": { label: "UCLA", primary: "#2D68C4", secondary: "#F2A900", name: "UCLA Bruins" },
  "ucla": { label: "UCLA", primary: "#2D68C4", secondary: "#F2A900", name: "UCLA Bruins" },
}

// ============================================================================
// SOCCER TEAMS (MLS, EPL, La Liga - abbreviated)
// ============================================================================
const SOCCER_TEAMS: TeamStylesMap = {
  "la galaxy": { label: "LA", primary: "#00245D", secondary: "#FFD200", name: "LA Galaxy" },
  "galaxy": { label: "LA", primary: "#00245D", secondary: "#FFD200", name: "LA Galaxy" },
  "los angeles galaxy": { label: "LA", primary: "#00245D", secondary: "#FFD200", name: "LA Galaxy" },
  "lafc": { label: "LAFC", primary: "#000000", secondary: "#C39E6D", name: "Los Angeles FC" },
  "los angeles fc": { label: "LAFC", primary: "#000000", secondary: "#C39E6D", name: "Los Angeles FC" },
  "inter miami": { label: "MIA", primary: "#F7B5CD", secondary: "#231F20", name: "Inter Miami CF" },
  "inter miami cf": { label: "MIA", primary: "#F7B5CD", secondary: "#231F20", name: "Inter Miami CF" },
  "atlanta united": { label: "ATL", primary: "#80000A", secondary: "#231F20", name: "Atlanta United FC" },
  "atlanta united fc": { label: "ATL", primary: "#80000A", secondary: "#231F20", name: "Atlanta United FC" },
  "seattle sounders": { label: "SEA", primary: "#5D9741", secondary: "#005595", name: "Seattle Sounders FC" },
  "seattle sounders fc": { label: "SEA", primary: "#5D9741", secondary: "#005595", name: "Seattle Sounders FC" },
  "new york red bulls": { label: "RBNY", primary: "#ED1E36", secondary: "#FFCD00", name: "New York Red Bulls" },
  "ny red bulls": { label: "RBNY", primary: "#ED1E36", secondary: "#FFCD00", name: "New York Red Bulls" },
  "red bulls": { label: "RBNY", primary: "#ED1E36", secondary: "#FFCD00", name: "New York Red Bulls" },
  "new york city fc": { label: "NYC", primary: "#6CACE4", secondary: "#F15524", name: "New York City FC" },
  "nycfc": { label: "NYC", primary: "#6CACE4", secondary: "#F15524", name: "New York City FC" },
  "portland timbers": { label: "POR", primary: "#004812", secondary: "#EBE72B", name: "Portland Timbers" },
  "timbers": { label: "POR", primary: "#004812", secondary: "#EBE72B", name: "Portland Timbers" },
  "fc cincinnati": { label: "CIN", primary: "#F05323", secondary: "#263B80", name: "FC Cincinnati" },
  "columbus crew": { label: "CLB", primary: "#000000", secondary: "#FFDB00", name: "Columbus Crew" },
  "crew": { label: "CLB", primary: "#000000", secondary: "#FFDB00", name: "Columbus Crew" },
  "chicago fire fc": { label: "CHI", primary: "#141414", secondary: "#FF0000", name: "Chicago Fire FC" },
  "chicago fire": { label: "CHI", primary: "#141414", secondary: "#FF0000", name: "Chicago Fire FC" },
  "fire": { label: "CHI", primary: "#141414", secondary: "#FF0000", name: "Chicago Fire FC" },
  "sporting kansas city": { label: "SKC", primary: "#93B1D7", secondary: "#002F65", name: "Sporting Kansas City" },
  "sporting kc": { label: "SKC", primary: "#93B1D7", secondary: "#002F65", name: "Sporting Kansas City" },
  "austin fc": { label: "ATX", primary: "#00B140", secondary: "#000000", name: "Austin FC" },
  "austin": { label: "ATX", primary: "#00B140", secondary: "#000000", name: "Austin FC" },
  "charlotte fc": { label: "CLT", primary: "#1A85C8", secondary: "#000000", name: "Charlotte FC" },
  "charlotte": { label: "CLT", primary: "#1A85C8", secondary: "#000000", name: "Charlotte FC" },
  "nashville sc": { label: "NSH", primary: "#ECE83A", secondary: "#1F1646", name: "Nashville SC" },
  "nashville": { label: "NSH", primary: "#ECE83A", secondary: "#1F1646", name: "Nashville SC" },
  "philadelphia union": { label: "PHI", primary: "#002D55", secondary: "#B18500", name: "Philadelphia Union" },
  "union": { label: "PHI", primary: "#002D55", secondary: "#B18500", name: "Philadelphia Union" },
  "dc united": { label: "DC", primary: "#000000", secondary: "#EF3E42", name: "DC United" },
  "d.c. united": { label: "DC", primary: "#000000", secondary: "#EF3E42", name: "DC United" },
  "new england revolution": { label: "NE", primary: "#C63323", secondary: "#0A1E32", name: "New England Revolution" },
  "revolution": { label: "NE", primary: "#C63323", secondary: "#0A1E32", name: "New England Revolution" },
  "toronto fc": { label: "TOR", primary: "#B81137", secondary: "#455560", name: "Toronto FC" },
  "toronto": { label: "TOR", primary: "#B81137", secondary: "#455560", name: "Toronto FC" },
  "cf montreal": { label: "MTL", primary: "#000000", secondary: "#C2B59B", name: "CF Montreal" },
  "montreal": { label: "MTL", primary: "#000000", secondary: "#C2B59B", name: "CF Montreal" },
  "vancouver whitecaps": { label: "VAN", primary: "#00245D", secondary: "#9DC3E6", name: "Vancouver Whitecaps" },
  "whitecaps": { label: "VAN", primary: "#00245D", secondary: "#9DC3E6", name: "Vancouver Whitecaps" },
  "orlando city": { label: "ORL", primary: "#633492", secondary: "#FDE192", name: "Orlando City SC" },
  "orlando city sc": { label: "ORL", primary: "#633492", secondary: "#FDE192", name: "Orlando City SC" },
  "minnesota united": { label: "MIN", primary: "#8CD2E5", secondary: "#231F20", name: "Minnesota United FC" },
  "minnesota united fc": { label: "MIN", primary: "#8CD2E5", secondary: "#231F20", name: "Minnesota United FC" },
  "houston dynamo": { label: "HOU", primary: "#FF6B00", secondary: "#101820", name: "Houston Dynamo" },
  "dynamo": { label: "HOU", primary: "#FF6B00", secondary: "#101820", name: "Houston Dynamo" },
  "fc dallas": { label: "DAL", primary: "#BF0D3E", secondary: "#0C2340", name: "FC Dallas" },
  "dallas": { label: "DAL", primary: "#BF0D3E", secondary: "#0C2340", name: "FC Dallas" },
  "real salt lake": { label: "RSL", primary: "#B30838", secondary: "#013A81", name: "Real Salt Lake" },
  "rsl": { label: "RSL", primary: "#B30838", secondary: "#013A81", name: "Real Salt Lake" },
  "colorado rapids": { label: "COL", primary: "#8B2346", secondary: "#96D1FF", name: "Colorado Rapids" },
  "rapids": { label: "COL", primary: "#8B2346", secondary: "#96D1FF", name: "Colorado Rapids" },
  "san jose earthquakes": { label: "SJ", primary: "#0067B1", secondary: "#000000", name: "San Jose Earthquakes" },
  "earthquakes": { label: "SJ", primary: "#0067B1", secondary: "#000000", name: "San Jose Earthquakes" },
  "st. louis city sc": { label: "STL", primary: "#D22630", secondary: "#0C2340", name: "St. Louis City SC" },
  "st louis city": { label: "STL", primary: "#D22630", secondary: "#0C2340", name: "St. Louis City SC" },
  "manchester united": { label: "MUN", primary: "#DA291C", secondary: "#FBE122", name: "Manchester United" },
  "man united": { label: "MUN", primary: "#DA291C", secondary: "#FBE122", name: "Manchester United" },
  "man utd": { label: "MUN", primary: "#DA291C", secondary: "#FBE122", name: "Manchester United" },
  "manchester city": { label: "MCI", primary: "#6CABDD", secondary: "#1C2C5B", name: "Manchester City" },
  "man city": { label: "MCI", primary: "#6CABDD", secondary: "#1C2C5B", name: "Manchester City" },
  "liverpool": { label: "LIV", primary: "#C8102E", secondary: "#00B2A9", name: "Liverpool FC" },
  "liverpool fc": { label: "LIV", primary: "#C8102E", secondary: "#00B2A9", name: "Liverpool FC" },
  "chelsea": { label: "CHE", primary: "#034694", secondary: "#DBA111", name: "Chelsea FC" },
  "chelsea fc": { label: "CHE", primary: "#034694", secondary: "#DBA111", name: "Chelsea FC" },
  "arsenal": { label: "ARS", primary: "#EF0107", secondary: "#063672", name: "Arsenal FC" },
  "arsenal fc": { label: "ARS", primary: "#EF0107", secondary: "#063672", name: "Arsenal FC" },
  "tottenham hotspur": { label: "TOT", primary: "#132257", secondary: "#FFFFFF", name: "Tottenham Hotspur" },
  "tottenham": { label: "TOT", primary: "#132257", secondary: "#FFFFFF", name: "Tottenham Hotspur" },
  "spurs": { label: "TOT", primary: "#132257", secondary: "#FFFFFF", name: "Tottenham Hotspur" },
  "newcastle united": { label: "NEW", primary: "#241F20", secondary: "#FFFFFF", name: "Newcastle United" },
  "newcastle": { label: "NEW", primary: "#241F20", secondary: "#FFFFFF", name: "Newcastle United" },
  "aston villa": { label: "AVL", primary: "#670E36", secondary: "#95BFE5", name: "Aston Villa" },
  "brighton & hove albion": { label: "BHA", primary: "#0057B8", secondary: "#FFFFFF", name: "Brighton & Hove Albion" },
  "brighton": { label: "BHA", primary: "#0057B8", secondary: "#FFFFFF", name: "Brighton & Hove Albion" },
  "west ham united": { label: "WHU", primary: "#7A263A", secondary: "#1BB1E7", name: "West Ham United" },
  "west ham": { label: "WHU", primary: "#7A263A", secondary: "#1BB1E7", name: "West Ham United" },
  "everton": { label: "EVE", primary: "#003399", secondary: "#FFFFFF", name: "Everton FC" },
  "everton fc": { label: "EVE", primary: "#003399", secondary: "#FFFFFF", name: "Everton FC" },
  "fulham": { label: "FUL", primary: "#000000", secondary: "#FFFFFF", name: "Fulham FC" },
  "fulham fc": { label: "FUL", primary: "#000000", secondary: "#FFFFFF", name: "Fulham FC" },
  "crystal palace": { label: "CRY", primary: "#1B458F", secondary: "#C4122E", name: "Crystal Palace" },
  "wolverhampton wanderers": { label: "WOL", primary: "#FDB913", secondary: "#231F20", name: "Wolverhampton Wanderers" },
  "wolves": { label: "WOL", primary: "#FDB913", secondary: "#231F20", name: "Wolverhampton Wanderers" },
  "wolverhampton": { label: "WOL", primary: "#FDB913", secondary: "#231F20", name: "Wolverhampton Wanderers" },
  "afc bournemouth": { label: "BOU", primary: "#DA291C", secondary: "#000000", name: "AFC Bournemouth" },
  "bournemouth": { label: "BOU", primary: "#DA291C", secondary: "#000000", name: "AFC Bournemouth" },
  "brentford": { label: "BRE", primary: "#E30613", secondary: "#FFFFFF", name: "Brentford FC" },
  "brentford fc": { label: "BRE", primary: "#E30613", secondary: "#FFFFFF", name: "Brentford FC" },
  "nottingham forest": { label: "NFO", primary: "#DD0000", secondary: "#FFFFFF", name: "Nottingham Forest" },
  "nott'm forest": { label: "NFO", primary: "#DD0000", secondary: "#FFFFFF", name: "Nottingham Forest" },
  "leicester city": { label: "LEI", primary: "#003090", secondary: "#FDBE11", name: "Leicester City" },
  "leicester": { label: "LEI", primary: "#003090", secondary: "#FDBE11", name: "Leicester City" },
  "ipswich town": { label: "IPS", primary: "#0000FF", secondary: "#FFFFFF", name: "Ipswich Town" },
  "ipswich": { label: "IPS", primary: "#0000FF", secondary: "#FFFFFF", name: "Ipswich Town" },
  "southampton": { label: "SOU", primary: "#D71920", secondary: "#130C0E", name: "Southampton FC" },
  "southampton fc": { label: "SOU", primary: "#D71920", secondary: "#130C0E", name: "Southampton FC" },
  "real madrid": { label: "RMA", primary: "#FEBE10", secondary: "#00529F", name: "Real Madrid CF" },
  "real madrid cf": { label: "RMA", primary: "#FEBE10", secondary: "#00529F", name: "Real Madrid CF" },
  "barcelona": { label: "BAR", primary: "#A50044", secondary: "#004D98", name: "FC Barcelona" },
  "fc barcelona": { label: "BAR", primary: "#A50044", secondary: "#004D98", name: "FC Barcelona" },
  "atletico madrid": { label: "ATM", primary: "#CB3524", secondary: "#272E61", name: "Atletico Madrid" },
  "atletico de madrid": { label: "ATM", primary: "#CB3524", secondary: "#272E61", name: "Atletico Madrid" },
  "sevilla fc": { label: "SEV", primary: "#D81E32", secondary: "#FFFFFF", name: "Sevilla FC" },
  "sevilla": { label: "SEV", primary: "#D81E32", secondary: "#FFFFFF", name: "Sevilla FC" },
  "real sociedad": { label: "RSO", primary: "#0067B1", secondary: "#FFFFFF", name: "Real Sociedad" },
  "real betis": { label: "BET", primary: "#00954C", secondary: "#FFFFFF", name: "Real Betis" },
  "real betis balompie": { label: "BET", primary: "#00954C", secondary: "#FFFFFF", name: "Real Betis" },
  "villarreal cf": { label: "VIL", primary: "#FFE667", secondary: "#005187", name: "Villarreal CF" },
  "villarreal": { label: "VIL", primary: "#FFE667", secondary: "#005187", name: "Villarreal CF" },
  "athletic club": { label: "ATH", primary: "#EE2523", secondary: "#FFFFFF", name: "Athletic Club" },
  "athletic bilbao": { label: "ATH", primary: "#EE2523", secondary: "#FFFFFF", name: "Athletic Club" },
  "valencia cf": { label: "VAL", primary: "#EE3524", secondary: "#000000", name: "Valencia CF" },
  "valencia": { label: "VAL", primary: "#EE3524", secondary: "#000000", name: "Valencia CF" },
  "celta vigo": { label: "CEL", primary: "#8AC3EE", secondary: "#FFFFFF", name: "RC Celta" },
  "rc celta": { label: "CEL", primary: "#8AC3EE", secondary: "#FFFFFF", name: "RC Celta" },
  "getafe cf": { label: "GET", primary: "#005999", secondary: "#FFFFFF", name: "Getafe CF" },
  "getafe": { label: "GET", primary: "#005999", secondary: "#FFFFFF", name: "Getafe CF" },
  "osasuna": { label: "OSA", primary: "#D91A21", secondary: "#0A3F7D", name: "CA Osasuna" },
  "ca osasuna": { label: "OSA", primary: "#D91A21", secondary: "#0A3F7D", name: "CA Osasuna" },
  "rayo vallecano": { label: "RAY", primary: "#E53027", secondary: "#FFFFFF", name: "Rayo Vallecano" },
  "mallorca": { label: "MLL", primary: "#E20613", secondary: "#000000", name: "RCD Mallorca" },
  "rcd mallorca": { label: "MLL", primary: "#E20613", secondary: "#000000", name: "RCD Mallorca" },
  "girona fc": { label: "GIR", primary: "#CD2534", secondary: "#FFFFFF", name: "Girona FC" },
  "girona": { label: "GIR", primary: "#CD2534", secondary: "#FFFFFF", name: "Girona FC" },
  "las palmas": { label: "LPA", primary: "#FFE400", secondary: "#0033A0", name: "UD Las Palmas" },
  "ud las palmas": { label: "LPA", primary: "#FFE400", secondary: "#0033A0", name: "UD Las Palmas" },
  "deportivo alaves": { label: "ALA", primary: "#003DA5", secondary: "#FFFFFF", name: "Deportivo Alaves" },
  "alaves": { label: "ALA", primary: "#003DA5", secondary: "#FFFFFF", name: "Deportivo Alaves" },
  "bayern munich": { label: "BAY", primary: "#DC052D", secondary: "#0066B2", name: "FC Bayern Munich" },
  "bayern": { label: "BAY", primary: "#DC052D", secondary: "#0066B2", name: "FC Bayern Munich" },
  "fc bayern munich": { label: "BAY", primary: "#DC052D", secondary: "#0066B2", name: "FC Bayern Munich" },
  "borussia dortmund": { label: "BVB", primary: "#FDE100", secondary: "#000000", name: "Borussia Dortmund" },
  "dortmund": { label: "BVB", primary: "#FDE100", secondary: "#000000", name: "Borussia Dortmund" },
  "bvb": { label: "BVB", primary: "#FDE100", secondary: "#000000", name: "Borussia Dortmund" },
  "paris saint-germain": { label: "PSG", primary: "#004170", secondary: "#DA291C", name: "Paris Saint-Germain" },
  "psg": { label: "PSG", primary: "#004170", secondary: "#DA291C", name: "Paris Saint-Germain" },
  "paris sg": { label: "PSG", primary: "#004170", secondary: "#DA291C", name: "Paris Saint-Germain" },
  "juventus": { label: "JUV", primary: "#000000", secondary: "#FFFFFF", name: "Juventus FC" },
  "juventus fc": { label: "JUV", primary: "#000000", secondary: "#FFFFFF", name: "Juventus FC" },
  "ac milan": { label: "MIL", primary: "#FB090B", secondary: "#000000", name: "AC Milan" },
  "milan": { label: "MIL", primary: "#FB090B", secondary: "#000000", name: "AC Milan" },
  "inter milan": { label: "INT", primary: "#010E80", secondary: "#000000", name: "Inter Milan" },
  "inter": { label: "INT", primary: "#010E80", secondary: "#000000", name: "Inter Milan" },
  "internazionale": { label: "INT", primary: "#010E80", secondary: "#000000", name: "Inter Milan" },
  "napoli": { label: "NAP", primary: "#12A0D7", secondary: "#FFFFFF", name: "SSC Napoli" },
  "ssc napoli": { label: "NAP", primary: "#12A0D7", secondary: "#FFFFFF", name: "SSC Napoli" },
  "as roma": { label: "ROM", primary: "#8E1F2F", secondary: "#F0BC42", name: "AS Roma" },
  "roma": { label: "ROM", primary: "#8E1F2F", secondary: "#F0BC42", name: "AS Roma" },
  "lazio": { label: "LAZ", primary: "#87D8F7", secondary: "#FFFFFF", name: "SS Lazio" },
  "ss lazio": { label: "LAZ", primary: "#87D8F7", secondary: "#FFFFFF", name: "SS Lazio" },
  "atalanta": { label: "ATA", primary: "#1E71B8", secondary: "#000000", name: "Atalanta BC" },
  "atalanta bc": { label: "ATA", primary: "#1E71B8", secondary: "#000000", name: "Atalanta BC" },
  "fiorentina": { label: "FIO", primary: "#482E92", secondary: "#FFFFFF", name: "ACF Fiorentina" },
  "acf fiorentina": { label: "FIO", primary: "#482E92", secondary: "#FFFFFF", name: "ACF Fiorentina" },
  "rb leipzig": { label: "RBL", primary: "#DD0741", secondary: "#FFFFFF", name: "RB Leipzig" },
  "leipzig": { label: "RBL", primary: "#DD0741", secondary: "#FFFFFF", name: "RB Leipzig" },
  "bayer leverkusen": { label: "LEV", primary: "#E32221", secondary: "#000000", name: "Bayer Leverkusen" },
  "leverkusen": { label: "LEV", primary: "#E32221", secondary: "#000000", name: "Bayer Leverkusen" },
  "eintracht frankfurt": { label: "SGE", primary: "#E1000F", secondary: "#000000", name: "Eintracht Frankfurt" },
  "frankfurt": { label: "SGE", primary: "#E1000F", secondary: "#000000", name: "Eintracht Frankfurt" },
  "vfb stuttgart": { label: "STU", primary: "#E32219", secondary: "#FFFFFF", name: "VfB Stuttgart" },
  "stuttgart": { label: "STU", primary: "#E32219", secondary: "#FFFFFF", name: "VfB Stuttgart" },
  "borussia monchengladbach": { label: "BMG", primary: "#000000", secondary: "#1C9B47", name: "Borussia Monchengladbach" },
  "gladbach": { label: "BMG", primary: "#000000", secondary: "#1C9B47", name: "Borussia Monchengladbach" },
  "ajax": { label: "AJA", primary: "#CF0032", secondary: "#FFFFFF", name: "AFC Ajax" },
  "afc ajax": { label: "AJA", primary: "#CF0032", secondary: "#FFFFFF", name: "AFC Ajax" },
  "psv eindhoven": { label: "PSV", primary: "#ED1C24", secondary: "#FFFFFF", name: "PSV Eindhoven" },
  "psv": { label: "PSV", primary: "#ED1C24", secondary: "#FFFFFF", name: "PSV Eindhoven" },
  "benfica": { label: "SLB", primary: "#FF0000", secondary: "#FFFFFF", name: "SL Benfica" },
  "sl benfica": { label: "SLB", primary: "#FF0000", secondary: "#FFFFFF", name: "SL Benfica" },
  "porto": { label: "POR", primary: "#004B93", secondary: "#FFFFFF", name: "FC Porto" },
  "fc porto": { label: "POR", primary: "#004B93", secondary: "#FFFFFF", name: "FC Porto" },
  "sporting cp": { label: "SCP", primary: "#008B4D", secondary: "#FFFFFF", name: "Sporting CP" },
  "sporting lisbon": { label: "SCP", primary: "#008B4D", secondary: "#FFFFFF", name: "Sporting CP" },
  "celtic": { label: "CEL", primary: "#017B48", secondary: "#FFFFFF", name: "Celtic FC" },
  "celtic fc": { label: "CEL", primary: "#017B48", secondary: "#FFFFFF", name: "Celtic FC" },
  "rangers": { label: "RAN", primary: "#0000FF", secondary: "#FFFFFF", name: "Rangers FC" },
  "rangers fc": { label: "RAN", primary: "#0000FF", secondary: "#FFFFFF", name: "Rangers FC" },
}

// ============================================================================
// COMBINED TEAM STYLES MAP
// ============================================================================
export const TEAM_STYLES: TeamStylesMap = {
  ...NFL_TEAMS,
  ...NBA_TEAMS,
  ...NHL_TEAMS,
  ...MLB_TEAMS,
  ...NCAA_TEAMS,
  ...SOCCER_TEAMS,
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get team style by team name and sport
 */
export function getTeamStyle(teamName: string, sport?: string): TeamStyle {
  const name = teamName.toLowerCase().trim()
  
  // Try exact match first
  if (TEAM_STYLES[name]) {
    return TEAM_STYLES[name]
  }
  
  // Try with sport-specific lookup if provided
  if (sport) {
    const sportLower = sport.toLowerCase()
    let sportMap: TeamStylesMap | undefined
    
    switch (sportLower) {
      case "nfl":
        sportMap = NFL_TEAMS
        break
      case "nba":
        sportMap = NBA_TEAMS
        break
      case "nhl":
        sportMap = NHL_TEAMS
        break
      case "mlb":
        sportMap = MLB_TEAMS
        break
      case "ncaaf":
      case "ncaab":
      case "cfb":
      case "cbb":
      case "college football":
      case "college basketball":
        sportMap = NCAA_TEAMS
        break
      case "soccer":
      case "mls":
      case "epl":
      case "laliga":
      case "ucl":
        sportMap = SOCCER_TEAMS
        break
    }
    
    if (sportMap && sportMap[name]) {
      return sportMap[name]
    }
  }
  
  // Fallback: generate abbreviation from team name
  const words = teamName.trim().split(" ")
  const abbr = words.length > 1 
    ? words.map(w => w[0]?.toUpperCase() || "").join("").slice(0, 3)
    : teamName.substring(0, 3).toUpperCase()
  
  return {
    label: abbr,
    primary: "#1F2937", // Dark gray fallback
    secondary: "#10B981", // Green accent fallback
    name: teamName,
  }
}

/**
 * Get team abbreviation
 */
export function getTeamAbbreviation(teamName: string, sport?: string): string {
  return getTeamStyle(teamName, sport).label
}

/**
 * Get team colors
 */
export function getTeamColors(teamName: string, sport?: string): { primary: string; secondary: string } {
  const style = getTeamStyle(teamName, sport)
  return {
    primary: style.primary,
    secondary: style.secondary,
  }
}



