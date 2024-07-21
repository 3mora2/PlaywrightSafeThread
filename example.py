import logging
from PlaywrightSafeThread import ThreadsafeBrowser

format = '%(name)s:%(levelname)s:%(message)s'

logging.basicConfig(
    level=logging.NOTSET,
    format=format
)

Logger = logging.getLogger()

th = ThreadsafeBrowser(browser="chromium")
browser = th.run_threadsafe(th.browser_type.launch, channel="chrome", headless=False)
context = th.run_threadsafe(browser.new_context, no_viewport=True, bypass_csp=True)
page = th.run_threadsafe(context.new_page)
try:
    th.run_threadsafe(page.goto, "https://web.whatsapp.com/", wait_until="networkidle")
finally:
    th.sync_close()

# OR

# th = ThreadsafeBrowser(
#     install=False,
#     install_callback=print,
#     no_context=False,
#     browser="chromium", channel="chrome", headless=False,
#     no_viewport=True, bypass_csp=True
# )
# th.run_threadsafe(th.page.goto, "https://web.whatsapp.com/")
# th.sync_close()
