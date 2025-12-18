export function formatGameTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

export function getConfidenceStyles(recommendation: string) {
  switch (recommendation) {
    case "strong":
      return "bg-green-500/20 text-green-400 border-green-500/50"
    case "moderate":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/50"
    case "weak":
      return "bg-orange-500/20 text-orange-400 border-orange-500/50"
    case "avoid":
      return "bg-red-500/20 text-red-400 border-red-500/50"
    default:
      return "bg-gray-500/20 text-gray-400 border-gray-500/50"
  }
}

export function getOverallStyles(recommendation: string) {
  switch (recommendation) {
    case "strong_play":
      return { bg: "from-green-600/30 to-green-900/30", border: "border-green-500", text: "text-green-400" }
    case "solid_play":
      return { bg: "from-yellow-600/30 to-yellow-900/30", border: "border-yellow-500", text: "text-yellow-400" }
    case "risky_play":
      return { bg: "from-orange-600/30 to-orange-900/30", border: "border-orange-500", text: "text-orange-400" }
    case "avoid":
      return { bg: "from-red-600/30 to-red-900/30", border: "border-red-500", text: "text-red-400" }
    default:
      return { bg: "from-gray-600/30 to-gray-900/30", border: "border-gray-500", text: "text-gray-400" }
  }
}




