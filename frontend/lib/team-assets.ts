/**
 * Team Assets - Colors and identification for NFL, NBA, NHL, MLB teams
 * 
 * NO LOGOS, NO IMAGES, NO TRADEMARKED GRAPHICS
 * Team names and abbreviations are used solely for identification purposes.
 */

interface TeamInfo {
  name: string
  abbreviation: string
  primaryColor: string
  secondaryColor: string
  espnId?: string
}

// Logo and image functions removed - we use TeamBadge component instead

// NFL Teams with hero images
export const NFL_TEAMS: Record<string, TeamInfo> = {
  // AFC East
  "buffalo bills": {
    name: "Buffalo Bills",
    abbreviation: "BUF",
    primaryColor: "#00338D",
    secondaryColor: "#C60C30",
    espnId: "2"
  },
  "miami dolphins": {
    name: "Miami Dolphins",
    abbreviation: "MIA",
    primaryColor: "#008E97",
    secondaryColor: "#FC4C02",
    espnId: "15",
  },
  "new england patriots": {
    name: "New England Patriots",
    abbreviation: "NE",
    primaryColor: "#002244",
    secondaryColor: "#C60C30",
    espnId: "17",
  },
  "new york jets": {
    name: "New York Jets",
    abbreviation: "NYJ",
    primaryColor: "#125740",
    secondaryColor: "#FFFFFF",
    espnId: "20",
  },
  // AFC North
  "baltimore ravens": {
    name: "Baltimore Ravens",
    abbreviation: "BAL",
    primaryColor: "#241773",
    secondaryColor: "#9E7C0C",
    espnId: "33",
  },
  "cincinnati bengals": {
    name: "Cincinnati Bengals",
    abbreviation: "CIN",
    primaryColor: "#FB4F14",
    secondaryColor: "#000000",
    espnId: "4",
  },
  "cleveland browns": {
    name: "Cleveland Browns",
    abbreviation: "CLE",
    primaryColor: "#311D00",
    secondaryColor: "#FF3C00"},
  "pittsburgh steelers": {
    name: "Pittsburgh Steelers",
    abbreviation: "PIT",
    primaryColor: "#FFB612",
    secondaryColor: "#101820"},
  // AFC South
  "houston texans": {
    name: "Houston Texans",
    abbreviation: "HOU",
    primaryColor: "#03202F",
    secondaryColor: "#A71930"},
  "indianapolis colts": {
    name: "Indianapolis Colts",
    abbreviation: "IND",
    primaryColor: "#002C5F",
    secondaryColor: "#A2AAAD"},
  "jacksonville jaguars": {
    name: "Jacksonville Jaguars",
    abbreviation: "JAX",
    primaryColor: "#101820",
    secondaryColor: "#D7A22A"},
  "tennessee titans": {
    name: "Tennessee Titans",
    abbreviation: "TEN",
    primaryColor: "#0C2340",
    secondaryColor: "#4B92DB"},
  // AFC West
  "denver broncos": {
    name: "Denver Broncos",
    abbreviation: "DEN",
    primaryColor: "#FB4F14",
    secondaryColor: "#002244"},
  "kansas city chiefs": {
    name: "Kansas City Chiefs",
    abbreviation: "KC",
    primaryColor: "#E31837",
    secondaryColor: "#FFB81C"},
  "las vegas raiders": {
    name: "Las Vegas Raiders",
    abbreviation: "LV",
    primaryColor: "#000000",
    secondaryColor: "#A5ACAF"},
  "los angeles chargers": {
    name: "Los Angeles Chargers",
    abbreviation: "LAC",
    primaryColor: "#0080C6",
    secondaryColor: "#FFC20E"},
  // NFC East
  "dallas cowboys": {
    name: "Dallas Cowboys",
    abbreviation: "DAL",
    primaryColor: "#003594",
    secondaryColor: "#869397"},
  "new york giants": {
    name: "New York Giants",
    abbreviation: "NYG",
    primaryColor: "#0B2265",
    secondaryColor: "#A71930"},
  "philadelphia eagles": {
    name: "Philadelphia Eagles",
    abbreviation: "PHI",
    primaryColor: "#004C54",
    secondaryColor: "#A5ACAF"},
  "washington commanders": {
    name: "Washington Commanders",
    abbreviation: "WAS",
    primaryColor: "#5A1414",
    secondaryColor: "#FFB612"},
  // NFC North
  "chicago bears": {
    name: "Chicago Bears",
    abbreviation: "CHI",
    primaryColor: "#0B162A",
    secondaryColor: "#C83803"},
  "detroit lions": {
    name: "Detroit Lions",
    abbreviation: "DET",
    primaryColor: "#0076B6",
    secondaryColor: "#B0B7BC"},
  "green bay packers": {
    name: "Green Bay Packers",
    abbreviation: "GB",
    primaryColor: "#203731",
    secondaryColor: "#FFB612"},
  "minnesota vikings": {
    name: "Minnesota Vikings",
    abbreviation: "MIN",
    primaryColor: "#4F2683",
    secondaryColor: "#FFC62F"},
  // NFC South
  "atlanta falcons": {
    name: "Atlanta Falcons",
    abbreviation: "ATL",
    primaryColor: "#A71930",
    secondaryColor: "#000000"},
  "carolina panthers": {
    name: "Carolina Panthers",
    abbreviation: "CAR",
    primaryColor: "#0085CA",
    secondaryColor: "#101820"},
  "new orleans saints": {
    name: "New Orleans Saints",
    abbreviation: "NO",
    primaryColor: "#D3BC8D",
    secondaryColor: "#101820"},
  "tampa bay buccaneers": {
    name: "Tampa Bay Buccaneers",
    abbreviation: "TB",
    primaryColor: "#D50A0A",
    secondaryColor: "#34302B"},
  // NFC West
  "arizona cardinals": {
    name: "Arizona Cardinals",
    abbreviation: "ARI",
    primaryColor: "#97233F",
    secondaryColor: "#000000"},
  "los angeles rams": {
    name: "Los Angeles Rams",
    abbreviation: "LAR",
    primaryColor: "#003594",
    secondaryColor: "#FFA300"},
  "san francisco 49ers": {
    name: "San Francisco 49ers",
    abbreviation: "SF",
    primaryColor: "#AA0000",
    secondaryColor: "#B3995D"},
  "seattle seahawks": {
    name: "Seattle Seahawks",
    abbreviation: "SEA",
    primaryColor: "#002244",
    secondaryColor: "#69BE28"}
  }

// NBA Teams
export const NBA_TEAMS: Record<string, TeamInfo> = {
  "atlanta hawks": {
    name: "Atlanta Hawks",
    abbreviation: "ATL",
    primaryColor: "#E03A3E",
    secondaryColor: "#C1D32F"},
  "boston celtics": {
    name: "Boston Celtics",
    abbreviation: "BOS",
    primaryColor: "#007A33",
    secondaryColor: "#BA9653"},
  "brooklyn nets": {
    name: "Brooklyn Nets",
    abbreviation: "BKN",
    primaryColor: "#000000",
    secondaryColor: "#FFFFFF"},
  "charlotte hornets": {
    name: "Charlotte Hornets",
    abbreviation: "CHA",
    primaryColor: "#1D1160",
    secondaryColor: "#00788C"},
  "chicago bulls": {
    name: "Chicago Bulls",
    abbreviation: "CHI",
    primaryColor: "#CE1141",
    secondaryColor: "#000000"},
  "cleveland cavaliers": {
    name: "Cleveland Cavaliers",
    abbreviation: "CLE",
    primaryColor: "#860038",
    secondaryColor: "#041E42"},
  "dallas mavericks": {
    name: "Dallas Mavericks",
    abbreviation: "DAL",
    primaryColor: "#00538C",
    secondaryColor: "#002B5E"},
  "denver nuggets": {
    name: "Denver Nuggets",
    abbreviation: "DEN",
    primaryColor: "#0E2240",
    secondaryColor: "#FEC524"},
  "detroit pistons": {
    name: "Detroit Pistons",
    abbreviation: "DET",
    primaryColor: "#C8102E",
    secondaryColor: "#1D42BA"},
  "golden state warriors": {
    name: "Golden State Warriors",
    abbreviation: "GSW",
    primaryColor: "#1D428A",
    secondaryColor: "#FFC72C"},
  "houston rockets": {
    name: "Houston Rockets",
    abbreviation: "HOU",
    primaryColor: "#CE1141",
    secondaryColor: "#000000"},
  "indiana pacers": {
    name: "Indiana Pacers",
    abbreviation: "IND",
    primaryColor: "#002D62",
    secondaryColor: "#FDBB30"},
  "la clippers": {
    name: "LA Clippers",
    abbreviation: "LAC",
    primaryColor: "#C8102E",
    secondaryColor: "#1D428A"},
  "los angeles lakers": {
    name: "Los Angeles Lakers",
    abbreviation: "LAL",
    primaryColor: "#552583",
    secondaryColor: "#FDB927"},
  "memphis grizzlies": {
    name: "Memphis Grizzlies",
    abbreviation: "MEM",
    primaryColor: "#5D76A9",
    secondaryColor: "#12173F"},
  "miami heat": {
    name: "Miami Heat",
    abbreviation: "MIA",
    primaryColor: "#98002E",
    secondaryColor: "#F9A01B"},
  "milwaukee bucks": {
    name: "Milwaukee Bucks",
    abbreviation: "MIL",
    primaryColor: "#00471B",
    secondaryColor: "#EEE1C6"},
  "minnesota timberwolves": {
    name: "Minnesota Timberwolves",
    abbreviation: "MIN",
    primaryColor: "#0C2340",
    secondaryColor: "#236192"},
  "new orleans pelicans": {
    name: "New Orleans Pelicans",
    abbreviation: "NOP",
    primaryColor: "#0C2340",
    secondaryColor: "#C8102E"},
  "new york knicks": {
    name: "New York Knicks",
    abbreviation: "NYK",
    primaryColor: "#006BB6",
    secondaryColor: "#F58426"},
  "oklahoma city thunder": {
    name: "Oklahoma City Thunder",
    abbreviation: "OKC",
    primaryColor: "#007AC1",
    secondaryColor: "#EF3B24"},
  "orlando magic": {
    name: "Orlando Magic",
    abbreviation: "ORL",
    primaryColor: "#0077C0",
    secondaryColor: "#C4CED4"},
  "philadelphia 76ers": {
    name: "Philadelphia 76ers",
    abbreviation: "PHI",
    primaryColor: "#006BB6",
    secondaryColor: "#ED174C"},
  "phoenix suns": {
    name: "Phoenix Suns",
    abbreviation: "PHX",
    primaryColor: "#1D1160",
    secondaryColor: "#E56020"},
  "portland trail blazers": {
    name: "Portland Trail Blazers",
    abbreviation: "POR",
    primaryColor: "#E03A3E",
    secondaryColor: "#000000"},
  "sacramento kings": {
    name: "Sacramento Kings",
    abbreviation: "SAC",
    primaryColor: "#5A2D81",
    secondaryColor: "#63727A"},
  "san antonio spurs": {
    name: "San Antonio Spurs",
    abbreviation: "SAS",
    primaryColor: "#C4CED4",
    secondaryColor: "#000000"},
  "toronto raptors": {
    name: "Toronto Raptors",
    abbreviation: "TOR",
    primaryColor: "#CE1141",
    secondaryColor: "#000000"},
  "utah jazz": {
    name: "Utah Jazz",
    abbreviation: "UTA",
    primaryColor: "#002B5C",
    secondaryColor: "#00471B"},
  "washington wizards": {
    name: "Washington Wizards",
    abbreviation: "WAS",
    primaryColor: "#002B5C",
    secondaryColor: "#E31837"}
  }

// NHL Teams
export const NHL_TEAMS: Record<string, TeamInfo> = {
  "anaheim ducks": {
    name: "Anaheim Ducks",
    abbreviation: "ANA",
    primaryColor: "#F47A38",
    secondaryColor: "#B9975B"},
  "arizona coyotes": {
    name: "Arizona Coyotes",
    abbreviation: "ARI",
    primaryColor: "#8C2633",
    secondaryColor: "#E2D6B5"},
  "boston bruins": {
    name: "Boston Bruins",
    abbreviation: "BOS",
    primaryColor: "#FFB81C",
    secondaryColor: "#000000"},
  "buffalo sabres": {
    name: "Buffalo Sabres",
    abbreviation: "BUF",
    primaryColor: "#002654",
    secondaryColor: "#FCB514"},
  "calgary flames": {
    name: "Calgary Flames",
    abbreviation: "CGY",
    primaryColor: "#C8102E",
    secondaryColor: "#F1BE48"},
  "carolina hurricanes": {
    name: "Carolina Hurricanes",
    abbreviation: "CAR",
    primaryColor: "#CC0000",
    secondaryColor: "#000000"},
  "chicago blackhawks": {
    name: "Chicago Blackhawks",
    abbreviation: "CHI",
    primaryColor: "#CF0A2C",
    secondaryColor: "#FF671B"},
  "colorado avalanche": {
    name: "Colorado Avalanche",
    abbreviation: "COL",
    primaryColor: "#6F263D",
    secondaryColor: "#236192"},
  "columbus blue jackets": {
    name: "Columbus Blue Jackets",
    abbreviation: "CBJ",
    primaryColor: "#002654",
    secondaryColor: "#CE1126"},
  "dallas stars": {
    name: "Dallas Stars",
    abbreviation: "DAL",
    primaryColor: "#006847",
    secondaryColor: "#8F8F8C"},
  "detroit red wings": {
    name: "Detroit Red Wings",
    abbreviation: "DET",
    primaryColor: "#CE1126",
    secondaryColor: "#FFFFFF"},
  "edmonton oilers": {
    name: "Edmonton Oilers",
    abbreviation: "EDM",
    primaryColor: "#041E42",
    secondaryColor: "#FF4C00"},
  "florida panthers": {
    name: "Florida Panthers",
    abbreviation: "FLA",
    primaryColor: "#041E42",
    secondaryColor: "#C8102E"},
  "los angeles kings": {
    name: "Los Angeles Kings",
    abbreviation: "LAK",
    primaryColor: "#111111",
    secondaryColor: "#A2AAAD"},
  "minnesota wild": {
    name: "Minnesota Wild",
    abbreviation: "MIN",
    primaryColor: "#154734",
    secondaryColor: "#A6192E"},
  "montreal canadiens": {
    name: "Montreal Canadiens",
    abbreviation: "MTL",
    primaryColor: "#AF1E2D",
    secondaryColor: "#192168"},
  "nashville predators": {
    name: "Nashville Predators",
    abbreviation: "NSH",
    primaryColor: "#FFB81C",
    secondaryColor: "#041E42"},
  "new jersey devils": {
    name: "New Jersey Devils",
    abbreviation: "NJD",
    primaryColor: "#CE1126",
    secondaryColor: "#000000"},
  "new york islanders": {
    name: "New York Islanders",
    abbreviation: "NYI",
    primaryColor: "#00539B",
    secondaryColor: "#F47D30"},
  "new york rangers": {
    name: "New York Rangers",
    abbreviation: "NYR",
    primaryColor: "#0038A8",
    secondaryColor: "#CE1126"},
  "ottawa senators": {
    name: "Ottawa Senators",
    abbreviation: "OTT",
    primaryColor: "#C52032",
    secondaryColor: "#C69214"},
  "philadelphia flyers": {
    name: "Philadelphia Flyers",
    abbreviation: "PHI",
    primaryColor: "#F74902",
    secondaryColor: "#000000"},
  "pittsburgh penguins": {
    name: "Pittsburgh Penguins",
    abbreviation: "PIT",
    primaryColor: "#000000",
    secondaryColor: "#FCB514"},
  "san jose sharks": {
    name: "San Jose Sharks",
    abbreviation: "SJS",
    primaryColor: "#006D75",
    secondaryColor: "#EA7200"},
  "seattle kraken": {
    name: "Seattle Kraken",
    abbreviation: "SEA",
    primaryColor: "#001628",
    secondaryColor: "#99D9D9"},
  "st. louis blues": {
    name: "St. Louis Blues",
    abbreviation: "STL",
    primaryColor: "#002F87",
    secondaryColor: "#FCB514"},
  "tampa bay lightning": {
    name: "Tampa Bay Lightning",
    abbreviation: "TBL",
    primaryColor: "#002868",
    secondaryColor: "#FFFFFF"},
  "toronto maple leafs": {
    name: "Toronto Maple Leafs",
    abbreviation: "TOR",
    primaryColor: "#00205B",
    secondaryColor: "#FFFFFF"},
  "vancouver canucks": {
    name: "Vancouver Canucks",
    abbreviation: "VAN",
    primaryColor: "#00205B",
    secondaryColor: "#00843D"},
  "vegas golden knights": {
    name: "Vegas Golden Knights",
    abbreviation: "VGK",
    primaryColor: "#B4975A",
    secondaryColor: "#333F42"},
  "washington capitals": {
    name: "Washington Capitals",
    abbreviation: "WSH",
    primaryColor: "#C8102E",
    secondaryColor: "#041E42"},
  "winnipeg jets": {
    name: "Winnipeg Jets",
    abbreviation: "WPG",
    primaryColor: "#041E42",
    secondaryColor: "#004C97"}
  }

// MLB Teams
export const MLB_TEAMS: Record<string, TeamInfo> = {
  "arizona diamondbacks": {
    name: "Arizona Diamondbacks",
    abbreviation: "ARI",
    primaryColor: "#A71930",
    secondaryColor: "#E3D4AD"},
  "atlanta braves": {
    name: "Atlanta Braves",
    abbreviation: "ATL",
    primaryColor: "#CE1141",
    secondaryColor: "#13274F"},
  "baltimore orioles": {
    name: "Baltimore Orioles",
    abbreviation: "BAL",
    primaryColor: "#DF4601",
    secondaryColor: "#000000"},
  "boston red sox": {
    name: "Boston Red Sox",
    abbreviation: "BOS",
    primaryColor: "#BD3039",
    secondaryColor: "#0C2340"},
  "chicago cubs": {
    name: "Chicago Cubs",
    abbreviation: "CHC",
    primaryColor: "#0E3386",
    secondaryColor: "#CC3433"},
  "chicago white sox": {
    name: "Chicago White Sox",
    abbreviation: "CHW",
    primaryColor: "#27251F",
    secondaryColor: "#C4CED4"},
  "cincinnati reds": {
    name: "Cincinnati Reds",
    abbreviation: "CIN",
    primaryColor: "#C6011F",
    secondaryColor: "#000000"},
  "cleveland guardians": {
    name: "Cleveland Guardians",
    abbreviation: "CLE",
    primaryColor: "#00385D",
    secondaryColor: "#E50022"},
  "colorado rockies": {
    name: "Colorado Rockies",
    abbreviation: "COL",
    primaryColor: "#33006F",
    secondaryColor: "#C4CED4"},
  "detroit tigers": {
    name: "Detroit Tigers",
    abbreviation: "DET",
    primaryColor: "#0C2340",
    secondaryColor: "#FA4616"},
  "houston astros": {
    name: "Houston Astros",
    abbreviation: "HOU",
    primaryColor: "#002D62",
    secondaryColor: "#EB6E1F"},
  "kansas city royals": {
    name: "Kansas City Royals",
    abbreviation: "KC",
    primaryColor: "#004687",
    secondaryColor: "#BD9B60"},
  "los angeles angels": {
    name: "Los Angeles Angels",
    abbreviation: "LAA",
    primaryColor: "#BA0021",
    secondaryColor: "#003263"},
  "los angeles dodgers": {
    name: "Los Angeles Dodgers",
    abbreviation: "LAD",
    primaryColor: "#005A9C",
    secondaryColor: "#EF3E42"},
  "miami marlins": {
    name: "Miami Marlins",
    abbreviation: "MIA",
    primaryColor: "#00A3E0",
    secondaryColor: "#EF3340"},
  "milwaukee brewers": {
    name: "Milwaukee Brewers",
    abbreviation: "MIL",
    primaryColor: "#12284B",
    secondaryColor: "#B6922E"},
  "minnesota twins": {
    name: "Minnesota Twins",
    abbreviation: "MIN",
    primaryColor: "#002B5C",
    secondaryColor: "#D31145"},
  "new york mets": {
    name: "New York Mets",
    abbreviation: "NYM",
    primaryColor: "#002D72",
    secondaryColor: "#FF5910"},
  "new york yankees": {
    name: "New York Yankees",
    abbreviation: "NYY",
    primaryColor: "#0C2340",
    secondaryColor: "#C4CED3"},
  "oakland athletics": {
    name: "Oakland Athletics",
    abbreviation: "OAK",
    primaryColor: "#003831",
    secondaryColor: "#EFB21E"},
  "philadelphia phillies": {
    name: "Philadelphia Phillies",
    abbreviation: "PHI",
    primaryColor: "#E81828",
    secondaryColor: "#002D72"},
  "pittsburgh pirates": {
    name: "Pittsburgh Pirates",
    abbreviation: "PIT",
    primaryColor: "#27251F",
    secondaryColor: "#FDB827"},
  "san diego padres": {
    name: "San Diego Padres",
    abbreviation: "SD",
    primaryColor: "#2F241D",
    secondaryColor: "#FFC425"},
  "san francisco giants": {
    name: "San Francisco Giants",
    abbreviation: "SF",
    primaryColor: "#FD5A1E",
    secondaryColor: "#27251F"},
  "seattle mariners": {
    name: "Seattle Mariners",
    abbreviation: "SEA",
    primaryColor: "#0C2C56",
    secondaryColor: "#005C5C"},
  "st. louis cardinals": {
    name: "St. Louis Cardinals",
    abbreviation: "STL",
    primaryColor: "#C41E3A",
    secondaryColor: "#0C2340"},
  "tampa bay rays": {
    name: "Tampa Bay Rays",
    abbreviation: "TB",
    primaryColor: "#092C5C",
    secondaryColor: "#8FBCE6"},
  "texas rangers": {
    name: "Texas Rangers",
    abbreviation: "TEX",
    primaryColor: "#003278",
    secondaryColor: "#C0111F"},
  "toronto blue jays": {
    name: "Toronto Blue Jays",
    abbreviation: "TOR",
    primaryColor: "#134A8E",
    secondaryColor: "#1D2D5C"},
  "washington nationals": {
    name: "Washington Nationals",
    abbreviation: "WSH",
    primaryColor: "#AB0003",
    secondaryColor: "#14225A"}
  }

/**
 * Get team info by name and league
 */
export function getTeamInfo(teamName: string, league: string): TeamInfo | null {
  const normalizedName = teamName.toLowerCase().trim()
  const leagueUpper = league.toUpperCase()

  let teams: Record<string, TeamInfo>
  switch (leagueUpper) {
    case "NFL":
      teams = NFL_TEAMS
      break
    case "NBA":
      teams = NBA_TEAMS
      break
    case "NHL":
      teams = NHL_TEAMS
      break
    case "MLB":
      teams = MLB_TEAMS
      break
    default:
      return null
  }

  // Direct match
  if (teams[normalizedName]) {
    return teams[normalizedName]
  }

  // Partial match - find team that contains the search term
  for (const [key, value] of Object.entries(teams)) {
    if (key.includes(normalizedName) || normalizedName.includes(key)) {
      return value
    }
    // Match by team nickname (last word)
    const nickname = key.split(" ").pop() || ""
    if (normalizedName.includes(nickname)) {
      return value
    }
  }

  return null
}

/**
 * Parse matchup string to get home and away team names
 */
export function parseMatchup(matchup: string): { awayTeam: string; homeTeam: string } {
  // Format: "Away Team @ Home Team" or "Away Team vs Home Team"
  const atMatch = matchup.match(/^(.+?)\s*@\s*(.+)$/i)
  if (atMatch) {
    return { awayTeam: atMatch[1].trim(), homeTeam: atMatch[2].trim() }
  }

  const vsMatch = matchup.match(/^(.+?)\s+vs\.?\s+(.+)$/i)
  if (vsMatch) {
    return { awayTeam: vsMatch[1].trim(), homeTeam: vsMatch[2].trim() }
  }

  return { awayTeam: "", homeTeam: "" }
}

/**
 * Get both teams' info from a matchup string
 */
export function getMatchupTeams(
  matchup: string,
  league: string
): { awayTeam: TeamInfo | null; homeTeam: TeamInfo | null } {
  const { awayTeam, homeTeam } = parseMatchup(matchup)
  return {
    awayTeam: getTeamInfo(awayTeam, league),
    homeTeam: getTeamInfo(homeTeam, league)
  }
}

