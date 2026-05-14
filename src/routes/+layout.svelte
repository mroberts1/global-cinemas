<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="shell">
	<header>
		<a href="/" class="brand">
			<strong>Global Cinemas</strong>
			<span>an atlas of film movements</span>
		</a>
		<nav>
			<a href="/">Map</a>
			<a href="/timeline">Timeline</a>
			<a href="/graph">Influences</a>
			<a href="/regions">Regions</a>
			<a href="/about">About</a>
		</nav>
	</header>
	<main>
		{@render children()}
	</main>
	<footer>
		<small>
			Data from <a href="https://letterboxd.com" target="_blank" rel="noreferrer">Letterboxd</a>,
			<a href="https://cinemawavesblog.com" target="_blank" rel="noreferrer">Cinema Waves</a>, and
			Wikipedia. Built with SvelteKit + d3.
		</small>
	</footer>
</div>
