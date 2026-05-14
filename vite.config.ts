import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// Allow access via cloudflared quick tunnels and any other host (dev preview).
		allowedHosts: ['.trycloudflare.com', 'localhost']
	}
});
