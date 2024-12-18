# Create new file
<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let show = false;

	let url = '';

	// Basic URL validation
	function isValidUrl(url: string) {
		try {
			new URL(url);
			return true;
		} catch (e) {
			return false;
		}
	}
</script>

<Modal size="md" className="bg-white dark:bg-gray-900" bind:show>
	<div class="absolute top-0 right-0 p-5">
		<button
			class="self-center dark:text-white"
			type="button"
			on:click={() => {
				show = false;
			}}
		>
			<XMark className="size-3.5" />
		</button>
	</div>

	<div class="flex flex-col w-full h-full md:space-x-4 dark:text-gray-200">
		<form
			class="flex flex-col w-full h-full"
			on:submit|preventDefault={() => {
				if (!url.trim()) {
					toast.error($i18n.t('Please enter a URL.'));
					return;
				}

				if (!isValidUrl(url.trim())) {
					toast.error($i18n.t('Please enter a valid URL.'));
					return;
				}

				dispatch('submit', { url: url.trim() });
				show = false;
				url = '';
			}}
		>
			<div class="flex-1 w-full h-full flex justify-center overflow-auto px-5 py-4">
				<div class="max-w-md py-2 md:py-10 w-full flex flex-col gap-4">
					<h2 class="text-xl font-semibold">{$i18n.t('Add URL')}</h2>
					<div class="w-full">
						<input
							class="w-full p-2 border rounded dark:border-gray-700 bg-transparent"
							type="text"
							bind:value={url}
							placeholder={$i18n.t('Enter URL')}
							required
						/>
					</div>
				</div>
			</div>

			<div class="flex flex-row items-center justify-end text-sm font-medium flex-shrink-0 mt-1 p-4 gap-1.5">
				<div class="flex-shrink-0">
					<Tooltip content={$i18n.t('Add')}>
						<button
							class="px-3.5 py-2 bg-black text-white dark:bg-white dark:text-black transition rounded-full"
							type="submit"
						>
							{$i18n.t('Add')}
						</button>
					</Tooltip>
				</div>
			</div>
		</form>
	</div>
</Modal> 