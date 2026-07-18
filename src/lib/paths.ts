/** Join a path with the configured Astro base URL. */
export function withBase(path = '') {
	const base = import.meta.env.BASE_URL;
	const prefix = base.endsWith('/') ? base : `${base}/`;
	const suffix = path.replace(/^\//, '');
	return suffix ? `${prefix}${suffix}` : prefix;
}
