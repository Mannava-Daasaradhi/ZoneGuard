interface Props {
  className?: string
  count?: number
}

function SkeletonLine({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-slate-700 rounded ${className}`} />
  )
}

export default function Skeleton({ className = '', count = 1 }: Props) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonLine key={i} className={className} />
      ))}
    </>
  )
}

export function ClaimSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-slate-700" />
        <div className="flex-1">
          <div className="h-4 bg-slate-700 rounded w-32 mb-2" />
          <div className="h-3 bg-slate-700 rounded w-48" />
        </div>
        <div className="h-5 bg-slate-700 rounded-full w-16" />
      </div>
    </div>
  )
}
