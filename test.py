from PlaywrightSafeThread import ThreadsafeBrowser

th = ThreadsafeBrowser(browser="chromium", channel="chrome", install=False, headless=False, no_viewport=True, bypass_csp=True)
th.get("https://web.whatsapp.com/", wait_until="domcontentloaded")
print(th.page_evaluate("""() => {return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}"""))
th.page_wait_for_function("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
