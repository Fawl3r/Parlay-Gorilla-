import Image from "next/image"

import { tutorialScreenshots, type TutorialScreenshotId } from "../_lib/tutorialScreenshots"

type Props = {
  id: TutorialScreenshotId
  priority?: boolean
}

export function TutorialScreenshot({ id, priority }: Props) {
  const shot = tutorialScreenshots.get(id)
  const variantLabel = shot.variant === "mobile" ? "Mobile" : "Desktop"

  return (
    <figure
      className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden"
      data-testid="tutorial-screenshot"
      data-screenshot-id={shot.id}
      data-variant={shot.variant}
    >
      <div className="relative">
        <Image
          src={shot.src}
          alt={shot.alt}
          width={shot.width}
          height={shot.height}
          priority={Boolean(priority)}
          className="w-full h-auto"
        />
        <div className="absolute top-3 left-3">
          <span className="inline-flex items-center rounded-full border border-white/15 bg-black/60 px-2.5 py-1 text-[11px] font-semibold text-white/80">
            {variantLabel}
          </span>
        </div>
      </div>
      {shot.caption ? (
        <figcaption className="px-4 py-3 text-xs text-white/70">
          {shot.caption}
        </figcaption>
      ) : null}
    </figure>
  )
}


