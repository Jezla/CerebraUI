<script>
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { verifyResetToken, resetPassword} from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';

	let email = sessionStorage.getItem('email');
	let newPassword = '';
	let confirmPassword = '';
	const i18n = getContext('i18n');

	onMount(async () => {
		const token = sessionStorage.getItem('rt');
		if (!token) {
			toast.error('Invalid session');
			goto('/auth');
			return;
		}  
		try {
			const ok = await verifyResetToken(email, token);
			if (ok !== true) {
				toast.error('会话过期');
				goto('/auth');
			} else {
				toast.success('Token验证成功');
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
				toast.success('密码已重置，请重新登录');
				goto('/auth');
			} else {
				toast.error('密码重置失败');
			}
		} catch (e) {
			toast.error(`${e}`);
			}
	}


</script>

<div class="min-h-screen flex items-center justify-center bg-black text-white">
	<div class="w-full max-w-md p-8 text-center">
		<h2 class="text-xl font-semibold mb-2">Reset Password</h2>
		<p class="text-sm mb-6">Your Email: <span>{email}</span></p>

		<div class="space-y-3 text-left">
			<input
				type="password"
				class="w-full px-3 py-2 rounded bg-gray-800 text-white"
				placeholder="New Password"
				bind:value={newPassword}
			/>
			<input
				type="password"
				class="w-full px-3 py-2 rounded bg-gray-800 text-white"
				placeholder="Confirm New Password"
				bind:value={confirmPassword}
			/>
		</div>

		<div class="mt-5">
			<button
				class="bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition w-full rounded-full font-medium text-sm py-2.5"
				on:click={submitHandler}
			>
				Reset Password
			</button>
		</div>

		<a href="/auth" class="block text-sm text-gray-400 hover:underline mt-2">{$i18n.t('Sign in')}</a>
	</div>
</div>