from PlaywrightSafeThread import ThreadsafeBrowser

th = ThreadsafeBrowser(browser="chromium", channel="chrome", install=False, headless=False, no_viewport=True,
                       bypass_csp=True, user_data_dir=r"C:\Users\ammar\New folder")


# async def on_load():
#     global th
#     result = await th.async_.evaluate(
#         """() => {return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}""")
#     print(result)
#     await th.async_.wait_for_function("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
#
#
# th.page.on("load", on_load)
#
# th.sync_.goto("https://web.whatsapp.com/")
# result = th.sync_.evaluate(
#     """() => {return (typeof window.WAPI !== 'undefined' &&typeof window.Store !== 'undefined');}""")
# print(result)
# th.sync_.wait_for_function("() => (window?.webpackChunkwhatsapp_web_client?.length || 0) > 3")
#
# th.sync_close()
