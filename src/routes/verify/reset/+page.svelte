<script>
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { verifyResetToken, resetPassword} from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';
	import PasswordInput from '$lib/components/common/PasswordInput.svelte';
	let email = sessionStorage.getItem('email');
	let newPassword = '';
	let confirmPassword = '';
	const i18n = getContext('i18n');

	onMount(async () => {
		const token = sessionStorage.getItem('rt');
		if (!token) {
			toast.error($i18n.t('Invalid session'));
			goto('/auth');
			return;
		}  
		try {
			const ok = await verifyResetToken(email, token);
			if (ok !== true) {
				toast.error($i18n.t('Session expired'));
				sessionStorage.removeItem('rt');
				sessionStorage.removeItem('email');
				goto('/auth');
			} else {
				toast.success($i18n.t('Token verification successful'));
			}
		} catch (e) {
			toast.error(`${e}`);
			goto('/auth');
		}
	});

	async function submitHandler() {
		let token = sessionStorage.getItem('rt');
		try {
			const ok = await resetPassword(email, newPassword, token);
			if (ok === true) {
				toast.success($i18n.t('Password reset successfully, please login again'));
				sessionStorage.removeItem('rt');
				sessionStorage.removeItem('email');
				goto('/auth');
			} else {
				toast.error($i18n.t('Password reset failed'));
			}
		} catch (e) {
			toast.error(`${e}`);
			}
	}


</script>

<div class="min-h-screen flex items-center justify-center bg-black text-white">
	<div class="w-full max-w-md p-8 text-center">
		<h2 class="text-xl font-semibold mb-2">{$i18n.t('Reset password')}</h2>
		<p class="text-sm mb-6">{$i18n.t('Your Email: ')}<span>{email}</span></p>
		<div class="space-y-3 text-left">
			<PasswordInput bind:value={newPassword} placeholder={$i18n.t('New Password')} id="new-password" showStrengthIndicator={true} />
			<PasswordInput bind:value={confirmPassword} placeholder={$i18n.t('Confirm Password')} id="confirm-password"/>
		</div>
		<div class="mt-5">
			<button
				class="bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition w-full rounded-full font-medium text-sm py-2.5"
				on:click={submitHandler}
			>
				{$i18n.t('Reset password')}
			</button>
		</div>
		<a href="/auth" class="block text-sm text-gray-400 hover:underline mt-2">{$i18n.t('Sign in')}</a>
	</div>
</div>