import React from "react"
import Image from "next/image"

type ParlayGorillaLogoProps = {
  size?: "sm" | "md" | "lg"
  showText?: boolean
  className?: string
}

export const ParlayGorillaLogo: React.FC<ParlayGorillaLogoProps> = ({
  size = "md",
  showText = true,
  className,
}) => {
  // Responsive sizing (keeps UI looking "normal" across screen sizes):
  // - Use clamp() so it gently scales within a safe min/max range.
  // - When showing text, size the icon to 1em so the mark matches the text height.
  const containerTextSize =
    size === "sm"
      ? "text-[clamp(1rem,1.6vw,1.125rem)]"
      : size === "lg"
      ? "text-[clamp(1.25rem,2.2vw,1.75rem)]"
      : "text-[clamp(1.0625rem,1.9vw,1.25rem)]"

  const iconSizeClass = showText
    ? "w-[1em] h-[1em]"
    : size === "sm"
    ? "w-8 h-8"
    : size === "lg"
    ? "w-12 h-12"
    : "w-10 h-10"

  return (
    <div
      className={[
        "inline-flex items-center gap-2 md:gap-3 rounded-full bg-gradient-to-br from-[#00FF001a] via-[#001B08] to-black",
        "px-2.5 md:px-3 py-1.5 md:py-2",
        "leading-none",
        containerTextSize,
        className || "",
      ].join(" ")}
    >
      <Image
        src="/images/newlogohead.png"
        alt="Parlay Gorilla logo"
        width={64}
        height={64}
        className={`${iconSizeClass} object-contain shrink-0`}
        priority
      />
      {showText && (
        <span
          className="uppercase whitespace-nowrap tracking-[0.12em] sm:tracking-[0.14em] md:tracking-[0.16em] font-logo font-bold"
          style={{
            color: "#000000",
            WebkitTextStroke: "1.5px #00FF00",
            textShadow:
              "0 0 0 2px #000000, 0 0 3px #00FF00, 0 0 6px #00DD00, 0 0 13px #00BB00, 0 0 21px #009900",
          }}
        >
          Parlay Gorilla
        </span>
      )}
    </div>
  )
}

