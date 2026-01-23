"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

export function UpsetFinderTab() {
  const router = useRouter()
  
  useEffect(() => {
    router.push("/tools/upset-finder")
  }, [router])
  
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <p className="text-gray-400">Redirecting to Upset Finder...</p>
      </div>
    </div>
  )
}
