<script>
	import { onMount, onDestroy, getContext } from 'svelte';
	import {
		verifyOtp,
		verifyToken,
		sendEmail,
		getEmailType,
		getSessionUser,
		userSignOut
	} from '$lib/apis/auths';
	import { finalizeSession } from '$lib/services/session';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';

	let code = ['', '', '', '', '', ''];
	let email = sessionStorage.getItem('email');
	let resendSeconds = 10;
	let input0, input1, input2, input3, input4, input5;
	let inputs;
	let type;
	const querystringValue = (key) => {
		const querystring = window.location.search;
		const urlParams = new URLSearchParams(querystring);
		return urlParams.get(key);
	};
	const i18n = getContext('i18n');

	onMount(() => {
		inputs = [input0, input1, input2, input3, input4, input5];
		if (inputs[0]) inputs[0].focus();
		if (email == null) {
			goto('/auth');
			return;
		}
		if (sessionStorage.getItem('rt') != null) {
			sessionStorage.removeItem('rt');
		}
		let token = sessionStorage.getItem('token');
		verifySessionHandler(email, token);
		startCountdown();
	});

	onDestroy(() => {
		clearInterval(resendTimer);
	});

	const verifySessionHandler = async (email, token) => {
		console.log('Validatesession：', email, token);
		console.log('Start checking token...');
		if (!token) {
			console.log('token is empty');
			toast.warning($i18n.t('Please click "Resend code" to get a verification code'));
			return;
		}
		const res = await verifyToken(email, token);
		console.log('Verify token result：', res);
		if (res == true) {
			toast.success($i18n.t('Token verification successful'));
		} else {
			toast.error($i18n.t('Session expired, please login again'));
			sessionStorage.removeItem('token');
			sessionStorage.removeItem('email');
			await userSignOut();
			localStorage.removeItem('token');
		}
	};
	// Verify otp
	const verifyOtpHandler = async (email, code) => {
		type = await getEmailType(sessionStorage.getItem('token'));
		let token = sessionStorage.getItem('token');
		if (!validateCode(code)) {
			console.log('Verify check：', validateCode(code));
			toast.error($i18n.t('Code is not valid'));
			return;
		}
		try {
			const res = await verifyOtp(email, code, token);
			console.log('Verify otp result：', res);
			if (res.result == true) {
				console.log(res);
				
				if (type == 'signin') {
					let sessionUser = await getSessionUser(res.auth_token);
					await finalizeSession(sessionUser);
					toast.success($i18n.t('Email verification successful'));
					const redirectPath = querystringValue('redirect') || '/';
					if (redirectPath.includes('/verify') || redirectPath.includes('/reset')) {
						goto('/');
					} else {
						goto(redirectPath);
					}
				} else if (type == 'reset') {
					if (res.token) {
					sessionStorage.setItem('rt', res.token);
					sessionStorage.removeItem('token');
						goto(`/verify/reset`);
					} else {
						toast.error($i18n.t('No rt'));
					}
				} else if (type == 'signup') {
					toast.success($i18n.t('Email verification successful'));
					let sessionUser = await getSessionUser(res.auth_token);
					await finalizeSession(sessionUser);
					const redirectPath = querystringValue('redirect') || '/';
					if (redirectPath.includes('/verify') || redirectPath.includes('/reset')) {
						goto('/');
					} else {
						goto(redirectPath);
					}
				}
			} else {
				toast.error($i18n.t('Verification failed'));
			}
		} catch (error) {
			console.log(error);
			toast.error(`${error.detail}`);
		}
	};

	const resendHandler = async () => {
		startCountdown();
		try {
			console.log('Email:', email);
			let token = sessionStorage.getItem('token');
			console.log('Token:', token);
			type = await getEmailType(token);
			if (type == null) {
				toast.error('Type is missing');
				return;
			}
			console.log('Type:', type);
			const res = await sendEmail(email, type);
			if (res.status === 400) {
				toast.error(
					$i18n.t('You have reached the maximum number of attempts. Please try again later.')
				);
				return;
			}
			if (sessionStorage.getItem('token') !== null) {
				sessionStorage.removeItem('token');
			}
			sessionStorage.setItem('token', res.token);
		} catch (error) {
			console.log(error);
			toast.error(`${error.detail}`);
		}
	};
	// Verify otp format is 6 digits
	function validateCode(code) {
		return code.length === 6 && /^\d+$/.test(code);
	}

	function handleInput(e, i) {
		const value = e.target.value;
		if (value.length > 1) {
			code[i] = value[0];
			e.target.value = value[0];
		}
		if (value && i < inputs.length - 1) {
			inputs[i + 1].focus();
		}
	}

	function handleKeyDown(e, i) {
		if (e.key === 'Backspace' && !code[i] && i > 0) {
			inputs[i - 1].focus();
		}
	}

	let resendTimer;
	function startCountdown() {
		clearInterval(resendTimer);
		if (resendSeconds <= 0) resendSeconds = 120;
		resendTimer = setInterval(() => {
			if (resendSeconds > 0) {
				resendSeconds -= 1;
			} else {
				clearInterval(resendTimer);
			}
		}, 1000);
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-black text-white">
	<div class="w-full max-w-md p-8 text-center">
		<h2 class="text-xl font-semibold mb-2">{$i18n.t('Account Email Verification')}</h2>
		<p class="text-gray-400 text-sm mb-6">
			{$i18n.t('We sent you a 6-character code to verify your email address')}
		</p>

		<p class="text-sm mb-6">
			{$i18n.t('Your Email: ')}<span class="text-sm mb-6">{email}</span>
		</p>

		<div class="flex justify-center gap-2 mb-4">
			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[0]}
				bind:this={input0}
				on:input={(e) => handleInput(e, 0)}
				on:keydown={(e) => handleKeyDown(e, 0)}
				autocomplete="off"
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[1]}
				bind:this={input1}
				on:input={(e) => handleInput(e, 1)}
				on:keydown={(e) => handleKeyDown(e, 1)}
				autocomplete="off"
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[2]}
				bind:this={input2}
				on:input={(e) => handleInput(e, 2)}
				on:keydown={(e) => handleKeyDown(e, 2)}
				autocomplete="off"
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[3]}
				bind:this={input3}
				on:input={(e) => handleInput(e, 3)}
				on:keydown={(e) => handleKeyDown(e, 3)}
				autocomplete="off"
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[4]}
				bind:this={input4}
				on:input={(e) => handleInput(e, 4)}
				on:keydown={(e) => handleKeyDown(e, 4)}
				autocomplete="off"
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[5]}
				bind:this={input5}
				on:input={(e) => handleInput(e, 5)}
				on:keydown={(e) => handleKeyDown(e, 5)}
				autocomplete="off"
			/>
		</div>

		<p class="text-xs text-gray-500 mb-4">
			{$i18n.t('Enter the 6-character code sent to your email')}
		</p>

		<div class="mt-5">
			<button
				class="bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition w-full rounded-full font-medium text-sm py-2.5"
				on:click={() => {
					verifyOtpHandler(email, String(code.join('')));
				}}
			>
				{$i18n.t('Verify Email')}
			</button>

			<button
				class="bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition w-full rounded-full font-medium text-sm py-2.5 mt-2"
				disabled={resendSeconds > 0}
				on:click={resendHandler}
			>
				{#if resendSeconds > 0}
					{$i18n.t('Resend code')} {resendSeconds}s
				{:else}
					{$i18n.t('Resend code')}
				{/if}
			</button>
		</div>
	</div>
</div>
