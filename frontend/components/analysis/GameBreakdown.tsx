"use client"

import { GameAnalysisContent } from "@/lib/api"
import { AiTextNormalizer } from "@/lib/text/AiTextNormalizer"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"

interface GameBreakdownProps {
  content: GameAnalysisContent
}

export function GameBreakdown({ content }: GameBreakdownProps) {
  const hasText = (value: unknown): value is string =>
    typeof value === "string" && value.trim().length > 0

  const hasOffensiveEdges =
    hasText((content as any)?.offensive_matchup_edges?.home_advantage) ||
    hasText((content as any)?.offensive_matchup_edges?.away_advantage) ||
    hasText((content as any)?.offensive_matchup_edges?.key_matchup)

  const hasDefensiveEdges =
    hasText((content as any)?.defensive_matchup_edges?.home_advantage) ||
    hasText((content as any)?.defensive_matchup_edges?.away_advantage) ||
    hasText((content as any)?.defensive_matchup_edges?.key_matchup)

  // Parse the full article and render with proper formatting
  const parseArticle = (article: string) => {
    if (!article) return null

    const normalizedArticle = AiTextNormalizer.normalizeEscapedNewlines(article)

    // Split by H2 headings (##)
    const sections = normalizedArticle.split(/(?=## )/g)
    
    return sections.map((section, index) => {
      if (!section.trim()) return null
      
      // Extract H2 heading
      const h2Match = section.match(/^## (.+?)$/m)
      const h2Title = h2Match ? h2Match[1] : null
      const contentAfterH2 = h2Match ? section.replace(/^## .+?\n/, '') : section
      
      // Check if this is a major section (Offensive Matchup, Defensive Matchup, etc.)
      const isMajorSection = h2Title && (
        h2Title.toLowerCase().includes('offensive matchup') ||
        h2Title.toLowerCase().includes('defensive matchup') ||
        h2Title.toLowerCase().includes('key stats') ||
        h2Title.toLowerCase().includes('ats trends') ||
        h2Title.toLowerCase().includes('totals trends')
      )
      
      // Split by H3 headings (###)
      const h3Sections = contentAfterH2.split(/(?=### )/g)
      
      return (
        <div key={index} className="mb-8">
          {h2Title && (
            <div className={`mb-6 mt-8 first:mt-0 ${isMajorSection ? 'bg-gradient-to-r from-emerald-500/10 to-cyan-500/5 border-l-4 border-emerald-500/50 rounded-lg p-4' : ''}`}>
              <h2 className={`text-3xl font-bold text-gray-900 dark:text-white ${
                isMajorSection 
                  ? 'mb-2' 
                  : 'border-b border-emerald-500/30 pb-3'
              }`}>
                {h2Title}
              </h2>
              {isMajorSection && (
                <p className="text-sm text-emerald-400/80 font-medium">
                  {h2Title.toLowerCase().includes('offensive') && 'Analysis of offensive strengths, weaknesses, and key matchups'}
                  {h2Title.toLowerCase().includes('defensive') && 'Analysis of defensive strengths, weaknesses, and key matchups'}
                  {h2Title.toLowerCase().includes('key stats') && 'Important statistics and metrics for this matchup'}
                  {h2Title.toLowerCase().includes('ats trends') && 'Against the spread trends and analysis'}
                  {h2Title.toLowerCase().includes('totals trends') && 'Over/under trends and analysis'}
                </p>
              )}
            </div>
          )}
          
          <div className={isMajorSection ? 'bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-6 mt-2' : ''}>
            {h3Sections.map((h3Section, h3Index) => {
              if (!h3Section.trim()) return null
              
              // Extract H3 heading
              const h3Match = h3Section.match(/^### (.+?)$/m)
              const h3Title = h3Match ? h3Match[1] : null
              const contentAfterH3 = h3Match ? h3Section.replace(/^### .+?\n/, '') : h3Section
              
              // Parse paragraphs
              const paragraphs = contentAfterH3
                .split(/\n\n+/)
                .filter(p => p.trim() && !p.trim().startsWith('#'))
                .map(p => p.trim())
              
              return (
                <div key={h3Index} className={`${isMajorSection ? 'mb-6' : 'mb-6'} ${h3Index < h3Sections.length - 1 && isMajorSection ? 'border-b border-emerald-500/10 pb-6' : ''}`}>
                  {h3Title && (
                    <div className="mb-4">
                      <h3 className={`text-xl font-semibold text-emerald-400 flex items-center gap-2 ${
                        isMajorSection ? 'text-cyan-300' : ''
                      }`}>
                        <span className={`w-2 h-2 rounded-full ${isMajorSection ? 'bg-cyan-400' : 'bg-emerald-400'}`}></span>
                        {h3Title}
                      </h3>
                      {isMajorSection && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-4 font-medium italic">
                          ↳ Part of {h2Title}
                        </p>
                      )}
                    </div>
                  )}
                  
                  {paragraphs.map((paragraph, pIndex) => {
                    // Check if paragraph contains stats (numbers with context)
                    const hasStats = /\d+\.\d+|\d+%|\d+-\d+/.test(paragraph)
                    
                    return (
                      <p
                        key={pIndex}
                        className={`mb-4 leading-7 text-gray-700 dark:text-gray-300 ${
                          hasStats ? 'font-medium' : ''
                        }`}
                      >
                        {paragraph.split('\n').map((line, lineIndex, array) => (
                          <span key={lineIndex}>
                            {line}
                            {lineIndex < array.length - 1 && <br />}
                          </span>
                        ))}
                      </p>
                    )
                  })}
                </div>
              )
            })}
          </div>
          
          {index < sections.length - 1 && <Separator className="my-8 bg-emerald-500/20" />}
        </div>
      )
    })
  }

  return (
    <Card className="border-primary/20">
      <CardHeader>
        <CardTitle className="text-2xl font-bold">Full Game Breakdown</CardTitle>
        <p className="text-sm text-muted-foreground mt-2">
          Comprehensive analysis and insights
        </p>
      </CardHeader>
      <CardContent>
        <div className="prose prose-invert max-w-none">
          {content.full_article ? (
            parseArticle(content.full_article)
          ) : (
            <div className="space-y-4">
              {/* Opening Summary */}
              {content.opening_summary && (
                <div className="mb-8">
                  <p className="text-lg leading-relaxed text-gray-700 dark:text-gray-200 mb-4">
                    {AiTextNormalizer.normalizeEscapedNewlines(content.opening_summary)}
                  </p>
                </div>
              )}
              
              {/* Offensive Matchup */}
              {hasOffensiveEdges && (
                <div className="mb-8">
                  <div className="mb-6">
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white border-b border-emerald-500/50 bg-emerald-500/5 -mx-4 px-4 py-3 rounded-t-lg">
                      Offensive Matchup
                    </h2>
                    <p className="text-sm text-emerald-400/70 mt-2 px-4">
                      Analysis of offensive strengths, weaknesses, and key matchups
                    </p>
                  </div>
                  
                  <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-6 -mx-4">
                    {content.offensive_matchup_edges.home_advantage && (
                      <div className="mb-6 border-b border-emerald-500/10 pb-6 last:border-0 last:pb-0">
                        <h3 className="text-xl font-semibold mb-4 text-emerald-400 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Home Team Advantages
                        </h3>
                        <p className="text-xs text-gray-500 mb-2 ml-3.5">
                          Part of Offensive Matchup
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 leading-7">
                          {content.offensive_matchup_edges.home_advantage}
                        </p>
                      </div>
                    )}
                    
                    {content.offensive_matchup_edges.away_advantage && (
                      <div className="mb-6 border-b border-emerald-500/10 pb-6 last:border-0 last:pb-0">
                        <h3 className="text-xl font-semibold mb-4 text-emerald-400 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Away Team Advantages
                        </h3>
                        <p className="text-xs text-gray-500 mb-2 ml-3.5">
                          Part of Offensive Matchup
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 leading-7">
                          {content.offensive_matchup_edges.away_advantage}
                        </p>
                      </div>
                    )}
                    
                    {content.offensive_matchup_edges.key_matchup && (
                      <div className="mb-6">
                        <h3 className="text-xl font-semibold mb-4 text-emerald-400 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Key Offensive Matchup
                        </h3>
                        <p className="text-xs text-gray-500 mb-2 ml-3.5">
                          Part of Offensive Matchup
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 leading-7">
                          {content.offensive_matchup_edges.key_matchup}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Defensive Matchup */}
              {hasDefensiveEdges && (
                <div className="mb-8">
                  <Separator className="my-8 bg-emerald-500/20" />
                  <div className="mb-6">
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white border-b border-emerald-500/50 bg-emerald-500/5 -mx-4 px-4 py-3 rounded-t-lg">
                      Defensive Matchup
                    </h2>
                    <p className="text-sm text-emerald-400/70 mt-2 px-4">
                      Analysis of defensive strengths, weaknesses, and key matchups
                    </p>
                  </div>
                  
                  <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-6 -mx-4">
                    {content.defensive_matchup_edges.home_advantage && (
                      <div className="mb-6 border-b border-emerald-500/10 pb-6 last:border-0 last:pb-0">
                        <h3 className="text-xl font-semibold mb-4 text-emerald-400 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Home Team Advantages
                        </h3>
                        <p className="text-xs text-gray-500 mb-2 ml-3.5">
                          Part of Defensive Matchup
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 leading-7">
                          {content.defensive_matchup_edges.home_advantage}
                        </p>
                      </div>
                    )}
                    
                    {content.defensive_matchup_edges.away_advantage && (
                      <div className="mb-6 border-b border-emerald-500/10 pb-6 last:border-0 last:pb-0">
                        <h3 className="text-xl font-semibold mb-4 text-emerald-400 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Away Team Advantages
                        </h3>
                        <p className="text-xs text-gray-500 mb-2 ml-3.5">
                          Part of Defensive Matchup
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 leading-7">
                          {content.defensive_matchup_edges.away_advantage}
                        </p>
                      </div>
                    )}
                    
                    {content.defensive_matchup_edges.key_matchup && (
                      <div className="mb-6">
                        <h3 className="text-xl font-semibold mb-4 text-emerald-400 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Key Defensive Matchup
                        </h3>
                        <p className="text-xs text-gray-500 mb-2 ml-3.5">
                          Part of Defensive Matchup
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 leading-7">
                          {content.defensive_matchup_edges.key_matchup}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Key Stats */}
              {content.key_stats && content.key_stats.length > 0 && (
                <div className="mb-8">
                  <Separator className="my-8 bg-emerald-500/20" />
                  <h2 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white border-b border-emerald-500/30 pb-3">
                    Performance Metrics
                  </h2>
                  <ul className="space-y-3">
                    {content.key_stats.map((stat, index) => (
                      <li key={index} className="flex items-start gap-3 text-gray-700 dark:text-gray-300 leading-7">
                        <span className="text-emerald-400 mt-1.5">•</span>
                        <span>{stat}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
