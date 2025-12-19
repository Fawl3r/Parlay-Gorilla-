import { CheckCircle, Clock, XCircle } from "lucide-react"

export const STATUS_COLORS: Record<string, { bg: string; text: string; icon: typeof CheckCircle }> = {
  pending: { bg: "bg-yellow-500/20", text: "text-yellow-400", icon: Clock },
  ready: { bg: "bg-emerald-500/20", text: "text-emerald-400", icon: CheckCircle },
  paid: { bg: "bg-blue-500/20", text: "text-blue-400", icon: CheckCircle },
  cancelled: { bg: "bg-red-500/20", text: "text-red-400", icon: XCircle },
}

export const TIER_COLORS: Record<string, string> = {
  rookie: "#9ca3af",
  pro: "#3b82f6",
  all_star: "#8b5cf6",
  hall_of_fame: "#f59e0b",
}


