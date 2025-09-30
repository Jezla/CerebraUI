import { get } from 'svelte/store';
import { getBackendConfig } from '$lib/apis';
import { user, config, socket as socketStore } from '$lib/stores';

export async function finalizeSession(sessionUser: any) {
  if (sessionUser?.token) localStorage.token = sessionUser.token;

  const sock = get(socketStore);
  sock?.emit('user-join', { auth: { token: sessionUser.token } });

  await user.set(sessionUser);
  await config.set(await getBackendConfig());
}