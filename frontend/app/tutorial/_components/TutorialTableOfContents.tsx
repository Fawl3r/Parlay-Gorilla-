import Link from "next/link"

import type { TutorialSection } from "../_lib/tutorialContent"

type Props = {
  sections: TutorialSection[]
}

export function TutorialTableOfContents({ sections }: Props) {
  return (
    <aside className="bg-white/[0.02] border border-white/10 rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-white">On this page</h2>
        <span className="text-[11px] font-semibold text-white/50">{sections.length} sections</span>
      </div>

      <nav className="mt-4">
        <ol className="space-y-2 text-sm">
          {sections.map((s) => (
            <li key={s.id}>
              <Link
                href={`#${s.id}`}
                className="block rounded-lg px-3 py-2 text-white/70 hover:text-emerald-300 hover:bg-emerald-500/10 transition-all"
              >
                {s.title}
              </Link>
            </li>
          ))}
        </ol>
      </nav>
    </aside>
  )
}


