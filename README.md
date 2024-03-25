# PlaywrightSafeThread
use [playwright](https://github.com/microsoft/playwright-python) as async and sync safe thread

used in [WPP_Whatsapp](https://github.com/3mora2/WPP_Whatsapp)

use sync in only one at time, else use async

in events like `page.on` use async and wait

from [minet](https://github.com/medialab/minet/blob/master/minet/browser/threadsafe_browser.py)

### Installation
```
pip install PlaywrightSafeThread
```
```
pip install git+https://www.github.com/3mora2/PlaywrightSafeThread@main
```



### Example

- to run async method in like page, user `await th.create_task` or `th.run_threadsafe`
- can't run async method from page outside ThreadsafeBrowser Loop, use `await th.create_task`
- can't run method `run_threadsafe` in ThreadsafeBrowser Loop

#### Sync

```python
from PlaywrightSafeThread import ThreadsafeBrowser


th = ThreadsafeBrowser(
    install=False,
    no_context=False,
    browser="chromium", channel="chrome", headless=False,
    no_viewport=True, bypass_csp=True
)
th.goto_sync("https://web.whatsapp.com/", wait_until="networkidle")
# or
th.run_threadsafe(th.page.goto("https://web.whatsapp.com/", wait_until="networkidle"))
th.sync_close()
```

#### Async

Use asyncio.run
```python
import asyncio
from PlaywrightSafeThread import ThreadsafeBrowser




async def main():
    
    th = ThreadsafeBrowser(
        install=False,
        no_context=False,
        browser="chromium", channel="chrome", headless=False,
        no_viewport=True, bypass_csp=True,  # loop=loop
    )
    
    # Work Only When start from th loop, not in (asyncio.run(main()))
    # await th.page.goto("https://web.whatsapp.com/", wait_until="networkidle")

    await th.goto("https://web.whatsapp.com/")
    # or 

    await th.create_task(
        th.page.goto("https://web.whatsapp.com/")
    )


    # Not Work when start from th loop, work in only (asyncio.run(main()))
    th.goto_sync("https://web.whatsapp.com/", wait_until="networkidle")

    await th.close()

asyncio.run(main())
```

Use ThreadsafeBrowser.loop
```python
import asyncio
from PlaywrightSafeThread import ThreadsafeBrowser


th = ThreadsafeBrowser(
    install=False,
    no_context=False,
    browser="chromium", channel="chrome", headless=False,
    no_viewport=True, bypass_csp=True,  # loop=loop
)
loop = th.loop


async def main():
    
    await th.page.goto("https://web.whatsapp.com/", wait_until="networkidle")

    await th.create_task(
        th.page.goto("https://web.whatsapp.com/")
    )
    await th.goto("https://web.whatsapp.com/")

    # Not Work when start from th loop, work in only (asyncio.run(main()))
    # th.goto_sync("https://web.whatsapp.com/", wait_until="networkidle")

    await th.close()


task = asyncio.run_coroutine_threadsafe(main(), loop=loop)
task.result()
```