import { redirect } from 'next/navigation'

type PageProps = {
  params: Promise<{ sport: string }> | { sport: string }
}

export default async function Page({ params }: PageProps) {
  const resolved = await Promise.resolve(params)
  redirect(`/games/${resolved.sport}/today`)
}
