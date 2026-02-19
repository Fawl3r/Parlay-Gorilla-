import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { GameAnalysisHowItWorks } from "@/app/analysis/_components/GameAnalysisHowItWorks"

describe("GameAnalysisHowItWorks", () => {
  it("renders how-to heading and steps while sports load", () => {
    const html = renderToStaticMarkup(<GameAnalysisHowItWorks />)
    expect(html).toContain("How game analysis works")
    expect(html).toContain("Pick a sport and matchup")
    expect(html).toContain("Read the AI research layer")
    expect(html).toContain("Use it in your process")
    expect(html).toContain("Loading available sports")
  })
})
