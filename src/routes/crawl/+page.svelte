<script lang="ts">
import { crawlWeb } from '$lib/apis/crawl';


  let inputText = 'https://example.com, https://httpbin.org/html';
  let loading = false;
  let error: string | null = null;
  let results: Array<{url:string; title?:string; success:boolean; markdown?:string; error?:string|null}> = [];

  async function handleCrawl() {
    loading = true; error = null; results = [];
    const urls = inputText.split(',').map(s => s.trim()).filter(Boolean);
    if (urls.length === 0) { error = '请输入至少一个 URL'; loading = false; return; }
    try {
      results = await crawlWeb(urls);
    } catch (e: any) {
      error = String(e?.message ?? e);
    } finally {
      loading = false;
    }
  }
</script>

<div class="p-6 max-w-5xl mx-auto">
  <h1 class="text-xl font-semibold mb-4">🌐 Parallel Web Crawl</h1>

  <div class="flex gap-2">
    <input
      class="flex-1 border rounded px-3 py-2"
      bind:value={inputText}
      placeholder="输入多个 URL，逗号分隔"
    />
    <button class="px-4 py-2 rounded bg-blue-600 text-white" on:click={handleCrawl}>
      {loading ? '抓取中…' : '抓取'}
    </button>
  </div>

  {#if error}
    <p class="mt-3 text-red-500">{error}</p>
  {/if}

  {#if results.length > 0}
    <div class="mt-4 space-y-4">
      {#each results as r}
        <div class="border rounded p-4 bg-gray-50 dark:bg-gray-900/30">
          <div class="font-medium">{r.title || r.url}</div>
          {#if r.success}
            <details class="mt-2">
              <summary class="cursor-pointer select-none">查看 Markdown</summary>
              <pre class="whitespace-pre-wrap text-sm mt-2">{r.markdown}</pre>
            </details>
          {:else}
            <div class="text-red-500 mt-2">抓取失败：{r.error}</div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
