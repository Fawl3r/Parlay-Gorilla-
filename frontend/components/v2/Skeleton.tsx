/**
 * V2 Skeleton Loader Component
 * Sharp, shimmering skeleton for loading states
 */

interface SkeletonProps {
  width?: string
  height?: string
  className?: string
  variant?: 'text' | 'rect' | 'stat'
}

export function Skeleton({ width, height, className = '', variant = 'rect' }: SkeletonProps) {
  const variants = {
    text: 'h-4 w-full',
    rect: 'h-20 w-full',
    stat: 'h-24 w-full',
  }

  return (
    <div
      className={`
        v2-animate-shimmer
        bg-slate-900
        border-l-2 border-slate-800
        ${variants[variant]}
        ${className}
      `}
      style={{ width, height }}
    />
  )
}

export function SkeletonPickCard() {
  return (
    <div className="bg-slate-900/95 border-l-2 border-slate-800 p-4">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Skeleton width="60px" height="20px" variant="text" />
          <Skeleton width="40px" height="20px" variant="text" />
        </div>
        <div className="space-y-2">
          <Skeleton width="80%" height="16px" variant="text" />
          <Skeleton width="60%" height="20px" variant="text" />
        </div>
        <Skeleton width="100%" height="4px" variant="text" />
      </div>
    </div>
  )
}

export function SkeletonStatCard() {
  return (
    <div className="bg-slate-900/95 border-l-2 border-slate-800 p-4">
      <Skeleton width="80px" height="12px" variant="text" className="mb-2" />
      <Skeleton width="100px" height="32px" variant="text" className="mb-1" />
      <Skeleton width="60px" height="10px" variant="text" />
    </div>
  )
}

export function SkeletonTableRow() {
  return (
    <tr className="border-b border-slate-900">
      <td className="px-4 py-3">
        <Skeleton width="32px" height="32px" />
      </td>
      <td className="px-4 py-3">
        <Skeleton width="120px" height="16px" />
      </td>
      <td className="px-4 py-3 text-right">
        <Skeleton width="60px" height="16px" className="ml-auto" />
      </td>
      <td className="px-4 py-3 text-right">
        <Skeleton width="40px" height="16px" className="ml-auto" />
      </td>
      <td className="px-4 py-3 text-right">
        <Skeleton width="60px" height="16px" className="ml-auto" />
      </td>
      <td className="px-4 py-3 text-right">
        <Skeleton width="50px" height="16px" className="ml-auto" />
      </td>
    </tr>
  )
}
