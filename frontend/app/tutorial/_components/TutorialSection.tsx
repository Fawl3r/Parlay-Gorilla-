import type { TutorialSection as TutorialSectionModel } from "../_lib/tutorialContent"
import { TutorialStepCard } from "./TutorialStepCard"

type Props = {
  section: TutorialSectionModel
  isFirst?: boolean
}

export function TutorialSection({ section, isFirst }: Props) {
  return (
    <section id={section.id} className="scroll-mt-24">
      <details
        className="group rounded-2xl border border-white/10 bg-white/[0.02] p-5 sm:p-6"
        open={Boolean(isFirst)}
      >
        <summary className="cursor-pointer list-none select-none">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h2 className="text-2xl sm:text-3xl font-black text-white">{section.title}</h2>
              <p className="mt-2 text-sm sm:text-base text-white/70 max-w-3xl">{section.description}</p>
            </div>
            <div className="shrink-0 text-xs text-white/50 mt-1">
              <span className="group-open:hidden">Tap to expand</span>
              <span className="hidden group-open:inline">Tap to collapse</span>
            </div>
          </div>
        </summary>

        <div className="mt-5 space-y-4">
          {section.steps.map((step, idx) => (
            <TutorialStepCard
              key={`${section.id}:${step.title}`}
              index={idx}
              step={step}
              priorityScreenshots={Boolean(isFirst && idx === 0)}
            />
          ))}
        </div>
      </details>
    </section>
  )
}


