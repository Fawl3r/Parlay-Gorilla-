import Link from "next/link"

import type { TutorialStep } from "../_lib/tutorialContent"
import { TutorialScreenshot } from "./TutorialScreenshot"

type Props = {
  index: number
  step: TutorialStep
  priorityScreenshots?: boolean
}

export function TutorialStepCard({ index, step, priorityScreenshots }: Props) {
  const stepNumber = index + 1

  return (
    <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-5 sm:p-6">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 text-black font-black flex items-center justify-center">
          {stepNumber}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg sm:text-xl font-bold text-white">{step.title}</h3>

          <ul className="mt-3 space-y-2 text-sm text-white/70">
            {step.bullets.map((b) => (
              <li key={b} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-400/80 flex-shrink-0" />
                <span className="min-w-0">{b}</span>
              </li>
            ))}
          </ul>

          {step.links && step.links.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {step.links.map((l) => (
                <Link
                  key={`${l.href}:${l.label}`}
                  href={l.href}
                  className="inline-flex items-center rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-semibold text-emerald-300 hover:border-emerald-500/40 hover:bg-emerald-500/10 transition-all"
                >
                  {l.label}
                </Link>
              ))}
            </div>
          ) : null}

          {step.screenshots && step.screenshots.length > 0 ? (
            <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
              {step.screenshots.map((id, screenshotIndex) => (
                <TutorialScreenshot
                  key={id}
                  id={id}
                  priority={Boolean(priorityScreenshots && screenshotIndex === 0)}
                />
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}


