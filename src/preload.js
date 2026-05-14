// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

// Disable text selection and tab focusing inside the renderer.
// This injects a small stylesheet and adds event listeners to prevent
// tab navigation and remove focus caused by mouse clicks.
window.addEventListener('DOMContentLoaded', () => {
	try {
		const style = document.createElement('style')
		style.id = 'disable-selection-and-focus'
		style.textContent = `
			/* disable text selection */
			* { -webkit-user-select: none !important; user-select: none !important; }
			/* hide the mouse cursor globally inside the app */
			html, body, * { cursor: none !important; }
			/* remove selection highlight color */
			*::selection { background: transparent !important; }
			/* remove focus outlines */
			*:focus { outline: none !important; box-shadow: none !important; }
		`
		document.head.appendChild(style)

		// Prevent Tab key from moving focus
		window.addEventListener('keydown', (e) => {
			if (e.key === 'Tab') {
				e.preventDefault()
				// blur any focused element to avoid visible focus state
				if (document.activeElement && typeof document.activeElement.blur === 'function') {
					document.activeElement.blur()
				}
			}
		}, true)

		// Prevent mouse clicks from giving focus (keeps interactions like clicks working)
		document.addEventListener('mousedown', (e) => {
			const el = e.target
			if (el && typeof el.blur === 'function') {
				// schedule blur after click to allow click handlers to run
				setTimeout(() => el.blur(), 0)
			}
		}, true)
	} catch (err) {
		// swallow errors to avoid breaking the preload
		// eslint-disable-next-line no-console
		console.error('preload: failed to apply selection/focus overrides', err)
	}
})
