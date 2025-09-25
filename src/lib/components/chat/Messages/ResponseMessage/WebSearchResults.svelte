<script lang="ts">
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import MagnifyingGlass from '$lib/components/icons/MagnifyingGlass.svelte';
	import Collapsible from '$lib/components/common/Collapsible.svelte';

	// Enhanced interface for search results
	export let status = {
		urls: [],
		query: '',
		search_results: [],
		search_engine: '',
		filenames: []
	};
	let state = false;

	// Use enhanced search results if available, fallback to old format
	$: searchResults = status.search_results && status.search_results.length > 0
		? status.search_results
		: (status.urls || status.filenames || []).map(url => ({
			url,
			title: url,
			engine: status.search_engine || '',
			favicon_url: null,
			domain: null
		}));

	// Display search engine name with proper capitalization
	$: searchEngineName = status.search_engine
		? status.search_engine.charAt(0).toUpperCase() + status.search_engine.slice(1)
		: 'Search';
</script>

<Collapsible bind:open={state} className="w-full space-y-1">
	<div
		class="flex items-center gap-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
	>
		<slot />

		{#if state}
			<ChevronUp strokeWidth="3.5" className="size-3.5 " />
		{:else}
			<ChevronDown strokeWidth="3.5" className="size-3.5 " />
		{/if}
	</div>
	<div
		class="text-sm border border-gray-300/30 dark:border-gray-700/50 rounded-xl mb-1.5"
		slot="content"
	>
		<!-- Search Engine Header -->
		<div class="flex items-center justify-between p-3 px-4 border-b border-gray-300/30 dark:border-gray-700/50 bg-gray-50 dark:bg-gray-900 rounded-t-xl">
			<div class="flex items-center gap-2">
				<MagnifyingGlass className="size-4" />
				<span class="text-xs font-medium text-gray-600 dark:text-gray-400">
					Searched {searchResults.length} sites using {searchEngineName}
				</span>
			</div>
		</div>

		<!-- Search Query -->
		{#if status?.query}
			<a
				href="https://www.google.com/search?q={status.query}"
				target="_blank"
				class="flex w-full items-center p-3 px-4 border-b border-gray-300/30 dark:border-gray-700/50 group/item hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
			>
				<div class="flex items-center gap-3 flex-1">
					<div class="flex-shrink-0">
						<svg class="size-4 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
							<path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
						</svg>
					</div>
					<div class="flex-1 min-w-0">
						<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
							{status.query}
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400">
							Search query
						</div>
					</div>
				</div>
				<div class="flex-shrink-0">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 16 16"
						fill="currentColor"
						class="size-4 text-gray-400 group-hover/item:text-gray-600 dark:group-hover/item:text-gray-300 transition"
					>
						<path
							fill-rule="evenodd"
							d="M4.22 11.78a.75.75 0 0 1 0-1.06L9.44 5.5H5.75a.75.75 0 0 1 0-1.5h5.5a.75.75 0 0 1 .75.75v5.5a.75.75 0 0 1-1.5 0V6.56l-5.22 5.22a.75.75 0 0 1-1.06 0Z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
			</a>
		{/if}

		<!-- Search Results -->
		{#each searchResults as result, resultIdx}
			<a
				href={result.url}
				target="_blank"
				class="flex w-full items-center p-3 px-4 {resultIdx === searchResults.length - 1
					? 'rounded-b-xl'
					: 'border-b border-gray-300/30 dark:border-gray-700/50'} group/item hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors no-underline"
			>
				<div class="flex items-center gap-3 flex-1 min-w-0">
					<!-- Website Favicon -->
					<div class="flex-shrink-0">
						{#if result.favicon_url}
							<img
								src={result.favicon_url}
								alt="Favicon"
								class="size-4 rounded-sm"
								on:error={(e) => {
									// Fallback to generic icon on error
									e.currentTarget.style.display = 'none';
									e.currentTarget.nextElementSibling.style.display = 'block';
								}}
							/>
							<div class="size-4 bg-gray-200 dark:bg-gray-700 rounded-sm items-center justify-center hidden">
								<svg class="size-3 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
									<path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
									<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
								</svg>
							</div>
						{:else}
							<div class="size-4 bg-gray-200 dark:bg-gray-700 rounded-sm flex items-center justify-center">
								<svg class="size-3 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
									<path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
									<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
								</svg>
							</div>
						{/if}
					</div>

					<!-- Title and Domain -->
					<div class="flex-1 min-w-0">
						<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
							{result.title || 'Untitled'}
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400 truncate">
							{result.domain || result.url}
						</div>
					</div>
				</div>

				<!-- External Link Icon -->
				<div class="flex-shrink-0">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 16 16"
						fill="currentColor"
						class="size-4 text-gray-400 group-hover/item:text-gray-600 dark:group-hover/item:text-gray-300 transition"
					>
						<path
							fill-rule="evenodd"
							d="M4.22 11.78a.75.75 0 0 1 0-1.06L9.44 5.5H5.75a.75.75 0 0 1 0-1.5h5.5a.75.75 0 0 1 .75.75v5.5a.75.75 0 0 1-1.5 0V6.56l-5.22 5.22a.75.75 0 0 1-1.06 0Z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
			</a>
		{/each}
	</div>
</Collapsible>
