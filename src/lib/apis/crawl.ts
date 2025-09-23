export async function crawlWeb(urls: string[], timeoutSec: number = 15): Promise<any[]> {
  const params = new URLSearchParams();
  for (const u of urls) params.append("urls", u);
  params.append("timeout", String(timeoutSec));

  const res = await fetch(`/api/crawl?${params.toString()}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Crawl API error: ${res.status} ${text}`);
  }
  return await res.json();
}
