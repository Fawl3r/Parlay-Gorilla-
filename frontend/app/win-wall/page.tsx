import { redirect } from "next/navigation"

/**
 * Win Wall has been replaced by Performance Rankings (Leaderboards).
 * Redirect existing links to the canonical route.
 */
export default function WinWallRedirect() {
  redirect("/leaderboards")
}
