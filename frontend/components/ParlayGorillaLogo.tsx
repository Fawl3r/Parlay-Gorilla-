import React from "react"
import Image from "next/image"

type ParlayGorillaLogoProps = {
  size?: "sm" | "md" | "lg"
  showText?: boolean
}

export const ParlayGorillaLogo: React.FC<ParlayGorillaLogoProps> = ({
  size = "md",
  showText = true,
}) => {
  const iconSize =
    size === "sm" ? "w-8 h-8" : size === "lg" ? "w-12 h-12" : "w-6 h-6"
  const fontSize =
    size === "sm" ? "text-[1.5625rem]" : size === "lg" ? "text-[2.8125rem]" : "text-[1.875rem]"

  return (
    <div className="inline-flex items-center gap-2 md:gap-3 rounded-full bg-gradient-to-br from-[#00FF001a] via-[#001B08] to-black px-2 md:px-3 py-1.5 md:py-2">
      <Image
        src="/images/newlogohead.png"
        alt="Parlay Gorilla logo"
        width={size === "sm" ? 32 : size === "lg" ? 48 : 24}
        height={size === "sm" ? 32 : size === "lg" ? 48 : 24}
        className={`${iconSize} object-contain`}
        priority
      />
      {showText && (
        <span
          className={`${fontSize} uppercase tracking-[0.15em] md:tracking-[0.18em] font-logo font-bold`}
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

