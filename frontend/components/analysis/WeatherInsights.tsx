"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cloud, Wind, Thermometer, Droplets, Gauge } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface WeatherData {
  temperature?: number
  feels_like?: number
  condition?: string
  description?: string
  wind_speed?: number
  wind_direction?: number
  humidity?: number
  precipitation?: number
  is_outdoor?: boolean
  affects_game?: boolean
}

interface WeatherInsightsProps {
  weatherText: string
  weatherData?: WeatherData
}

function getWindDirection(degrees?: number): string {
  if (!degrees) return "N/A"
  const directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
  return directions[Math.round(degrees / 22.5) % 16]
}

export function WeatherInsights({ weatherText, weatherData }: WeatherInsightsProps) {
  // Parse weather text for better formatting
  const parseWeatherText = (text: string) => {
    if (!text || text === "Weather should not significantly impact this game") {
      return null
    }
    
    // Split by sentences for better readability
    const sentences = text.split(/\. (?=[A-Z])/).filter(s => s.trim())
    
    return sentences.map((sentence, index) => {
      // Check for specific weather indicators
      const hasWind = /wind/i.test(sentence)
      const hasTemp = /temperature|freezing|hot|cold/i.test(sentence)
      const hasPrecip = /rain|snow|precipitation/i.test(sentence)
      
      let icon = <Cloud className="h-4 w-4" />
      if (hasWind) icon = <Wind className="h-4 w-4" />
      else if (hasTemp) icon = <Thermometer className="h-4 w-4" />
      else if (hasPrecip) icon = <Droplets className="h-4 w-4" />
      
      return (
        <div key={index} className="flex items-start gap-3 mb-3 last:mb-0">
          <div className="text-amber-400 mt-0.5 flex-shrink-0">
            {icon}
          </div>
          <p className="text-gray-700 dark:text-gray-200 leading-7 flex-1">
            {sentence.trim()}
            {!sentence.endsWith('.') && '.'}
          </p>
        </div>
      )
    })
  }

  const parsedContent = parseWeatherText(weatherText)
  const hasWeatherData = weatherData && (weatherData.temperature !== undefined || weatherData.wind_speed !== undefined)

  if (!parsedContent && !hasWeatherData) {
    return null
  }

  return (
    <Card className="border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-orange-500/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-400">
          <Cloud className="h-5 w-5" />
          Weather Impact Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Game Time Weather Conditions */}
        {hasWeatherData && (
          <div className="bg-black/20 rounded-lg p-4 border border-amber-500/20">
            <h4 className="text-sm font-semibold text-amber-300 mb-4 flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Game Time Weather Conditions
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {weatherData.temperature !== undefined && (
                <div className="flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <Thermometer className="h-4 w-4 text-amber-400" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">Temperature</span>
                  </div>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {Math.round(weatherData.temperature)}°F
                  </span>
                  {weatherData.feels_like && weatherData.feels_like !== weatherData.temperature && (
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      Feels like {Math.round(weatherData.feels_like)}°F
                    </span>
                  )}
                </div>
              )}
              
              {weatherData.wind_speed !== undefined && weatherData.wind_speed > 0 && (
                <div className="flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <Wind className="h-4 w-4 text-amber-400" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">Wind</span>
                  </div>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {Math.round(weatherData.wind_speed)} mph
                  </span>
                  {weatherData.wind_direction !== undefined && (
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {getWindDirection(weatherData.wind_direction)}
                    </span>
                  )}
                </div>
              )}
              
              {weatherData.humidity !== undefined && (
                <div className="flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <Droplets className="h-4 w-4 text-amber-400" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">Humidity</span>
                  </div>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {Math.round(weatherData.humidity)}%
                  </span>
                </div>
              )}
              
              {weatherData.condition && (
                <div className="flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <Cloud className="h-4 w-4 text-amber-400" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">Conditions</span>
                  </div>
                  <Badge variant="outline" className="text-xs border-amber-500/30 text-amber-300 w-fit">
                    {weatherData.description || weatherData.condition}
                  </Badge>
                </div>
              )}
              
              {weatherData.precipitation !== undefined && weatherData.precipitation > 0 && (
                <div className="flex flex-col col-span-2 md:col-span-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Droplets className="h-4 w-4 text-amber-400" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">Precipitation</span>
                  </div>
                  <span className="text-sm text-gray-900 dark:text-white">
                    {weatherData.precipitation.toFixed(2)} inches expected
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Weather Impact Analysis */}
        {parsedContent && parsedContent.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-amber-300 mb-3">Impact Analysis</h4>
            <div className="space-y-2">
              {parsedContent}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

