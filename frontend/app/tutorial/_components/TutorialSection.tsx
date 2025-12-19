import type { TutorialSection as TutorialSectionModel } from "../_lib/tutorialContent"
import { TutorialStepCard } from "./TutorialStepCard"

type Props = {
  section: TutorialSectionModel
  isFirst?: boolean
}

export function TutorialSection({ section, isFirst }: Props) {
  return (
    <section id={section.id} className="scroll-mt-24">
      <div className="mb-6">
        <h2 className="text-2xl sm:text-3xl font-black text-white">{section.title}</h2>
        <p className="mt-2 text-sm sm:text-base text-white/70 max-w-3xl">{section.description}</p>
      </div>

      <div className="space-y-4">
        {section.steps.map((step, idx) => (
          <TutorialStepCard
            key={`${section.id}:${step.title}`}
            index={idx}
            step={step}
            priorityScreenshots={Boolean(isFirst && idx === 0)}
          />
        ))}
      </div>
    </section>
  )
}


