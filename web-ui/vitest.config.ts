import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST, compilerOptions: { dev: true } })],
	test: {
		globals: true,
		environment: 'jsdom',
		setupFiles: ['./src/test/setup.ts'],
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	resolve: {
		alias: {
			$lib: path.resolve('./src/lib'),
			'$app/navigation': path.resolve('./src/test/mocks/app-navigation.ts'),
			'$app/stores': path.resolve('./src/test/mocks/app-stores.ts')
		},
		conditions: ['browser']
	}
});
