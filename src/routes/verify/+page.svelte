<script>
	import { onMount, onDestroy, getContext } from 'svelte';
	import { page } from '$app/stores';
	import { verifyOtp, verifyToken, sendEmail } from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';

	let code = ['', '', '', '', '', ''];
	let email = sessionStorage.getItem('email');
	let resendSeconds = 10;
	let input0, input1, input2, input3, input4, input5;
	let inputs;
    const i18n = getContext('i18n');

	onMount(() => {
		inputs = [input0, input1, input2, input3, input4, input5];
		if (inputs[0]) inputs[0].focus();
		if (email == null){
			goto('/auth');
			return;
		}
		if (sessionStorage.getItem('rt') != null){
			sessionStorage.removeItem('rt');
		}
		let token = sessionStorage.getItem('token');
		verifySessionHandler(email, token);
		startCountdown();
	});

	onDestroy(() => {
		clearInterval(resendTimer);
	});

	const verifySessionHandler = async (email,token) => {
		console.log("验证session：", email, token);
		console.log("开始检查token...");
		if (!token) {
			console.log("token为空");
			toast.error("Invalid session");
			goto('/auth');
			return;
		}
		const res = await verifyToken(email,token);
		console.log("验证token结果：",res);
		if(res == true){
			toast.success("Token验证成功");
		}else{
			toast.error("会话过期");
			goto('/auth');
		}	
	}
	// 验证otp
	const verifyOtpHandler = async (email, code) => {
		let token = sessionStorage.getItem('token');
		console.log("验证otp：",email, code,token);
		if (!validateCode(code)){
			console.log("校验检查：",validateCode(code));
			toast.error($i18n.t('Code is not valid')); 
			return;
		}
		try {
			const res = await verifyOtp(email, code, token);
			console.log("验证otp结果：",res);
			if (res[0] == true){
				sessionStorage.setItem('rt', res[1]);
				goto(`/verify/reset`)
			} else {
				toast.error("验证失败");
			}
			
		} catch (error) {
			console.log(error);
			toast.error(`${error}`);
		}
	}

	const resendHandler = async () => { 
		startCountdown(); 
		try {
			console.log("email:",email);
			const res = await sendEmail(email);
			if (sessionStorage.getItem('token')!==null) {
				sessionStorage.removeItem('token');
			}
			sessionStorage.setItem('token', res.token);
			console.log(res);
		} catch (error) {
			console.log(error);
			toast.error(`${error}`);
		}
	}
	// 验证otp格式是否为6位数字
	function validateCode(code) {
		return code.length === 6 && /^\d+$/.test(code)
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
		if (resendSeconds <= 0) resendSeconds = 10;
		resendTimer = setInterval(() => {
		if (resendSeconds > 0){
			resendSeconds -= 1;
			} else {
			clearInterval(resendTimer);
			}	
		}, 1000);
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-black text-white">
	<div class="w-full max-w-md p-8 text-center">
		<h2 class="text-xl font-semibold mb-2">Account Email Verification</h2>
		<p class="text-gray-400 text-sm mb-6">
			We have sent a verification code to your email<br />
			Please verify your email address to continue.
		</p>

		<p class="text-sm mb-6">
			Your Email: <span class="text-sm mb-6">{email}</span>
		</p>

		<div class="flex justify-center gap-2 mb-4">
			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[0]}
				bind:this={input0}
				on:input={(e) => handleInput(e, 0)}
				on:keydown={(e) => handleKeyDown(e, 0)}
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[1]}
				bind:this={input1}
				on:input={(e) => handleInput(e, 1)}
				on:keydown={(e) => handleKeyDown(e, 1)}
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[2]}
				bind:this={input2}
				on:input={(e) => handleInput(e, 2)}
				on:keydown={(e) => handleKeyDown(e, 2)}
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[3]}
				bind:this={input3}
				on:input={(e) => handleInput(e, 3)}
				on:keydown={(e) => handleKeyDown(e, 3)}
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[4]}
				bind:this={input4}
				on:input={(e) => handleInput(e, 4)}
				on:keydown={(e) => handleKeyDown(e, 4)}
			/>

			<input
				class="w-10 h-14 text-center text-xl font-bold rounded-lg border border-gray-500 bg-black focus:outline-none focus:ring-2 focus:ring-gray-400"
				maxlength="1"
				bind:value={code[5]}
				bind:this={input5}
				on:input={(e) => handleInput(e, 5)}
				on:keydown={(e) => handleKeyDown(e, 5)}
			/>
		</div>

		<p class="text-xs text-gray-500 mb-4">Enter the 6-character code sent to your email</p>

		<div class="mt-5">
			<button
				class="bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition w-full rounded-full font-medium text-sm py-2.5"
				on:click={() => {
					verifyOtpHandler(email, String(code.join('')));
				}}
			>
				Verify Email
			</button>

			<button
				class="bg-gray-700/5 hover:bg-gray-700/10 dark:bg-gray-100/5 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition w-full rounded-full font-medium text-sm py-2.5 mt-2"
				disabled={resendSeconds > 0}
				on:click={resendHandler}
			>
				{#if resendSeconds > 0}
					Resend in {resendSeconds}s
				{:else}
					Resend
				{/if}
			</button>
		</div>

		<a href="/auth" class="block text-sm text-gray-400 hover:underline">{$i18n.t('Sign in')}</a>
	</div>
</div>
