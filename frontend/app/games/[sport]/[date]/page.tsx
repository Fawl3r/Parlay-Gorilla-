import { GamesListPage } from "@/components/games/GamesListPage"

type PageProps = {
  params: Promise<{ sport: string; date: string }> | { sport: string; date: string }
}

export default async function Page({ params }: PageProps) {
  const resolved = await Promise.resolve(params)
  return <GamesListPage sport={resolved.sport} date={resolved.date} />
}

