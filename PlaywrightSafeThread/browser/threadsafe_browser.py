# from: https://github.com/medialab/minet/blob/master/minet/browser/threadsafe_browser.py

import inspect
import logging
import os
import subprocess
import sys
import tempfile
from concurrent.futures import Future
from typing import (
    Callable,
    Awaitable,
    Set,
    Optional,
    Literal,
)
import asyncio
import platform
from threading import Thread, Event, Lock
from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
    BrowserType
)
from playwright._impl._driver import compute_driver_executable, get_driver_env

sys_os = platform.system()

UNIX = "windows" not in sys_os.lower()
LTE_PY37 = platform.python_version_tuple()[:2] <= ("3", "7")

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")
BrowserName = Literal["chromium", "firefox", "webkit"]
# T = TypeVar("T")
# P = ParamSpec("P")
PageCallable = Callable  # [Concatenate[Page, P], Awaitable[T]]
BrowserCallable = Callable  # [Concatenate[Browser, P], Awaitable[T]]
Logger = logging.getLogger("PlaywrightSafeThread")


class ThreadsafeBrowser:
    PLAYWRIGHT_BROWSERS_PATH = os.path.join(tempfile.gettempdir(), "PLAYWRIGHT_BROWSERS_PATH")

    def __init__(
            self,
            no_context=True,
            browser: BrowserName = "chromium",
            stealthy: bool = False,
            install: bool = False,
            install_callback= None,
            check_open_dir=True,
            close_already_profile=True,
            loop=None,
            playwright_path_env=True,
            **kwargs
    ) -> None:
        """
        Browser Parameters
        ----------
        executable_path : Union[pathlib.Path, str, None]
            Path to a browser executable to run instead of the bundled one. If `executablePath` is a relative path, then it is
            resolved relative to the current working directory. Note that Playwright only works with the bundled Chromium,
            Firefox or WebKit, use at your own risk.
        channel : Union[str, None]
            Browser distribution channel.  Supported values are "chrome", "chrome-beta", "chrome-dev", "chrome-canary",
            "msedge", "msedge-beta", "msedge-dev", "msedge-canary". Read more about using
            [Google Chrome and Microsoft Edge](../browsers.md#google-chrome--microsoft-edge).
        args : Union[List[str], None]
            Additional arguments to pass to the browser instance. The list of Chromium flags can be found
            [here](http://peter.sh/experiments/chromium-command-line-switches/).
        ignore_default_args : Union[List[str], bool, None]
            If `true`, Playwright does not pass its own configurations args and only uses the ones from `args`. If an array is
            given, then filters out the given default arguments. Dangerous option; use with care. Defaults to `false`.
        handle_sigint : Union[bool, None]
            Close the browser process on Ctrl-C. Defaults to `true`.
        handle_sigterm : Union[bool, None]
            Close the browser process on SIGTERM. Defaults to `true`.
        handle_sighup : Union[bool, None]
            Close the browser process on SIGHUP. Defaults to `true`.
        timeout : Union[float, None]
            Maximum time in milliseconds to wait for the browser instance to start. Defaults to `30000` (30 seconds). Pass `0`
            to disable timeout.
        env : Union[Dict[str, Union[bool, float, str]], None]
            Specify environment variables that will be visible to the browser. Defaults to `process.env`.
        headless : Union[bool, None]
            Whether to run browser in headless mode. More details for
            [Chromium](https://developers.google.com/web/updates/2017/04/headless-chrome) and
            [Firefox](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Headless_mode). Defaults to `true` unless the
            `devtools` option is `true`.
        devtools : Union[bool, None]
            **Chromium-only** Whether to auto-open a Developer Tools panel for each tab. If this option is `true`, the
            `headless` option will be set `false`.
        proxy : Union[{server: str, bypass: Union[str, None], username: Union[str, None], password: Union[str, None]}, None]
            Network proxy settings.
        downloads_path : Union[pathlib.Path, str, None]
            If specified, accepted downloads are downloaded into this directory. Otherwise, temporary directory is created and
            is deleted when browser is closed. In either case, the downloads are deleted when the browser context they were
            created in is closed.
        slow_mo : Union[float, None]
            Slows down Playwright operations by the specified amount of milliseconds. Useful so that you can see what is going
            on.
        traces_dir : Union[pathlib.Path, str, None]
            If specified, traces are saved into this directory.
        chromium_sandbox : Union[bool, None]
            Enable Chromium sandboxing. Defaults to `false`.
        firefox_user_prefs : Union[Dict[str, Union[bool, float, str]], None]
            Firefox user preferences. Learn more about the Firefox user preferences at
            [`about:config`](https://support.mozilla.org/en-US/kb/about-config-editor-firefox).

        BrowserContext Parameters
        ----------
        viewport : Union[{width: int, height: int}, None]
            Sets a consistent viewport for each page. Defaults to an 1280x720 viewport. `no_viewport` disables the fixed
            viewport. Learn more about [viewport emulation](../emulation.md#viewport).
        screen : Union[{width: int, height: int}, None]
            Emulates consistent window screen size available inside web page via `window.screen`. Is only used when the
            `viewport` is set.
        no_viewport : Union[bool, None]
            Does not enforce fixed viewport, allows resizing window in the headed mode.
        ignore_https_errors : Union[bool, None]
            Whether to ignore HTTPS errors when sending network requests. Defaults to `false`.
        java_script_enabled : Union[bool, None]
            Whether or not to enable JavaScript in the context. Defaults to `true`. Learn more about
            [disabling JavaScript](../emulation.md#javascript-enabled).
        bypass_csp : Union[bool, None]
            Toggles bypassing page's Content-Security-Policy. Defaults to `false`.
        user_agent : Union[str, None]
            Specific user agent to use in this context.
        locale : Union[str, None]
            Specify user locale, for example `en-GB`, `de-DE`, etc. Locale will affect `navigator.language` value,
            `Accept-Language` request header value as well as number and date formatting rules. Defaults to the system default
            locale. Learn more about emulation in our [emulation guide](../emulation.md#locale--timezone).
        timezone_id : Union[str, None]
            Changes the timezone of the context. See
            [ICU's metaZones.txt](https://cs.chromium.org/chromium/src/third_party/icu/source/data/misc/metaZones.txt?rcl=faee8bc70570192d82d2978a71e2a615788597d1)
            for a list of supported timezone IDs. Defaults to the system timezone.
        geolocation : Union[{latitude: float, longitude: float, accuracy: Union[float, None]}, None]
        permissions : Union[List[str], None]
            A list of permissions to grant to all pages in this context. See `browser_context.grant_permissions()` for
            more details. Defaults to none.
        extra_http_headers : Union[Dict[str, str], None]
            An object containing additional HTTP headers to be sent with every request. Defaults to none.
        offline : Union[bool, None]
            Whether to emulate network being offline. Defaults to `false`. Learn more about
            [network emulation](../emulation.md#offline).
        http_credentials : Union[{username: str, password: str, origin: Union[str, None]}, None]
            Credentials for [HTTP authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication). If no
            origin is specified, the username and password are sent to any servers upon unauthorized responses.
        device_scale_factor : Union[float, None]
            Specify device scale factor (can be thought of as dpr). Defaults to `1`. Learn more about
            [emulating devices with device scale factor](../emulation.md#devices).
        is_mobile : Union[bool, None]
            Whether the `meta viewport` tag is taken into account and touch events are enabled. isMobile is a part of device,
            so you don't actually need to set it manually. Defaults to `false` and is not supported in Firefox. Learn more
            about [mobile emulation](../emulation.md#isMobile).
        has_touch : Union[bool, None]
            Specifies if viewport supports touch events. Defaults to false. Learn more about
            [mobile emulation](../emulation.md#devices).
        color_scheme : Union["dark", "light", "no-preference", "null", None]
            Emulates `'prefers-colors-scheme'` media feature, supported values are `'light'`, `'dark'`, `'no-preference'`. See
            `page.emulate_media()` for more details. Passing `'null'` resets emulation to system defaults. Defaults to
            `'light'`.
        reduced_motion : Union["no-preference", "null", "reduce", None]
            Emulates `'prefers-reduced-motion'` media feature, supported values are `'reduce'`, `'no-preference'`. See
            `page.emulate_media()` for more details. Passing `'null'` resets emulation to system defaults. Defaults to
            `'no-preference'`.
        forced_colors : Union["active", "none", "null", None]
            Emulates `'forced-colors'` media feature, supported values are `'active'`, `'none'`. See
            `page.emulate_media()` for more details. Passing `'null'` resets emulation to system defaults. Defaults to
            `'none'`.
        accept_downloads : Union[bool, None]
            Whether to automatically download all the attachments. Defaults to `true` where all the downloads are accepted.
        proxy : Union[{server: str, bypass: Union[str, None], username: Union[str, None], password: Union[str, None]}, None]
            Network proxy settings to use with this context. Defaults to none.

            **NOTE** For Chromium on Windows the browser needs to be launched with the global proxy for this option to work. If
            all contexts override the proxy, global proxy will be never used and can be any string, for example `launch({
            proxy: { server: 'http://per-context' } })`.
        record_har_path : Union[pathlib.Path, str, None]
            Enables [HAR](http://www.softwareishard.com/blog/har-12-spec) recording for all pages into the specified HAR file
            on the filesystem. If not specified, the HAR is not recorded. Make sure to call `browser_context.close()`
            for the HAR to be saved.
        record_har_omit_content : Union[bool, None]
            Optional setting to control whether to omit request content from the HAR. Defaults to `false`.
        record_video_dir : Union[pathlib.Path, str, None]
            Enables video recording for all pages into the specified directory. If not specified videos are not recorded. Make
            sure to call `browser_context.close()` for videos to be saved.
        record_video_size : Union[{width: int, height: int}, None]
            Dimensions of the recorded videos. If not specified the size will be equal to `viewport` scaled down to fit into
            800x800. If `viewport` is not configured explicitly the video size defaults to 800x450. Actual picture of each page
            will be scaled down if necessary to fit the specified size.
        storage_state : Union[pathlib.Path, str, {cookies: List[{name: str, value: str, domain: str, path: str, expires: float, httpOnly: bool, secure: bool, sameSite: Union["Lax", "None", "Strict"]}], origins: List[{origin: str, localStorage: List[{name: str, value: str}]}]}, None]
            Learn more about [storage state and auth](../auth.md).

            Populates context with given storage state. This option can be used to initialize context with logged-in
            information obtained via `browser_context.storage_state()`.
        base_url : Union[str, None]
            When using `page.goto()`, `page.route()`, `page.wait_for_url()`,
            `page.expect_request()`, or `page.expect_response()` it takes the base URL in consideration by
            using the [`URL()`](https://developer.mozilla.org/en-US/docs/Web/API/URL/URL) constructor for building the
            corresponding URL. Unset by default. Examples:
            - baseURL: `http://localhost:3000` and navigating to `/bar.html` results in `http://localhost:3000/bar.html`
            - baseURL: `http://localhost:3000/foo/` and navigating to `./bar.html` results in
              `http://localhost:3000/foo/bar.html`
            - baseURL: `http://localhost:3000/foo` (without trailing slash) and navigating to `./bar.html` results in
              `http://localhost:3000/bar.html`
        strict_selectors : Union[bool, None]
            If set to true, enables strict selectors mode for this context. In the strict selectors mode all operations on
            selectors that imply single target DOM element will throw when more than one element matches the selector. This
            option does not affect any Locator APIs (Locators are always strict). Defaults to `false`. See `Locator` to learn
            more about the strict mode.
        service_workers : Union["allow", "block", None]
            Whether to allow sites to register Service workers. Defaults to `'allow'`.
            - `'allow'`: [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API) can be
              registered.
            - `'block'`: Playwright will block all registration of Service Workers.
        record_har_url_filter : Union[Pattern[str], str, None]
        record_har_mode : Union["full", "minimal", None]
            When set to `minimal`, only record information necessary for routing from HAR. This omits sizes, timing, page,
            cookies, security and other types of HAR information that are not used when replaying from HAR. Defaults to `full`.
        record_har_content : Union["attach", "embed", "omit", None]
            Optional setting to control resource content management. If `omit` is specified, content is not persisted. If
            `attach` is specified, resources are persisted as separate files and all of these files are archived along with the
            HAR file. Defaults to `embed`, which stores content inline the HAR file as per HAR specification.

        """
        if browser not in SUPPORTED_BROWSERS:
            raise TypeError("unsupported browser")

        # NOTE: on unix python 3.7, child watching does not
        # work properly when asyncio is not running from the main thread
        # if UNIX and LTE_PY37:
        #     from PlaywrightSafeThread._future_.threaded_child_watcher import ThreadedChildWatcher
        #     asyncio.set_child_watcher(ThreadedChildWatcher())

        self.install_callback = install_callback
        self._stealthy = stealthy
        self._no_context = no_context
        self._browser_name = browser

        self._browser_option = {}
        self._browser_persistent_option = {}
        self._context_option = {}

        # get parameters foreach function
        __browser_option = inspect.getfullargspec(BrowserType.launch).kwonlyargs
        __browser_persistent_option = inspect.getfullargspec(BrowserType.launch_persistent_context).kwonlyargs + [
            "user_data_dir"]
        __context_option = inspect.getfullargspec(Browser.new_context).kwonlyargs

        for key in kwargs:
            if key in __browser_option:
                self._browser_option.update({key: kwargs[key]})
            if key in __browser_persistent_option:
                self._browser_persistent_option.update({key: kwargs[key]})
            if key in __context_option:
                self._context_option.update({key: kwargs[key]})

        if playwright_path_env:
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH",
                                  kwargs.get("PLAYWRIGHT_BROWSERS_PATH") or self.PLAYWRIGHT_BROWSERS_PATH
                                  )

        # if install:
        #     from PlaywrightSafeThread.browser.plawright_shim import run_playwright
        #     run_playwright("install", self._browser_name)
        if install and not self.check_is_install(self._browser_name):
            self.run_playwright("install", self._browser_name)

        self.__check_open_dir = check_open_dir
        self.__close_already_profile = close_already_profile

        self.loop = asyncio.new_event_loop()
        self.start_event = Event()
        # self.thread = Thread(target=self.__thread_worker, daemon=True)
        self.thread = Thread(
            name="Thread-browser-%i" % id(self), target=self.__thread_worker
        )

        # TODO::
        self.running_futures: Set[Future] = set()
        self.running_futures_lock = Lock()

        # Starting loop thread
        self.thread.start()
        # Wait Finish Thread
        self.start_event.wait()

    def __thread_worker(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.__start_playwright())
        self.start_event.set()

        # NOTE: we are now ready to accept tasks
        try:
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())

        self.loop.run_until_complete(self.__stop_playwright())

    async def create_task(self, task, *args, **kwargs):
        if not asyncio.iscoroutine(task):
            task = task(*args, **kwargs)

        if self.is_same_loop:
            # TODO :: use __handle_future
            return await self.loop.create_task(task)

        future = asyncio.run_coroutine_threadsafe(task, self.loop)
        return self.__handle_future(future)
        # return asyncio.run_coroutine_threadsafe(task, self.loop).result()

    @property
    def is_same_loop(self):
        try:
            return asyncio.get_event_loop() == self.loop
        except Exception as e:
            if 'There is no current event loop in thread' in str(e):
                return True
            raise e

    def run_threadsafe(self, task, *args, timeout_=120, **kwargs):
        if not asyncio.iscoroutine(task):
            task = task(*args, **kwargs)

        if not self.is_same_loop:
            future = asyncio.run_coroutine_threadsafe(task, self.loop)
            return self.__handle_future(future, timeout=timeout_)

            # def _on_completion(f):
            #     exception = f.exception()
            #
            #     if exception:
            #         raise exception
            #
            # future.add_done_callback(_on_completion)

            # result = future.result(timeout=timeout_)
            # return result

        # TODO :: use __handle_future
        start_event_task = Event()

        async def run_task(task_):
            r = await task_
            start_event_task.set()
            return r

        future = self.loop.create_task(
            run_task(task)
        )

        start_event_task.wait(timeout_)
        result = future.result()
        return result

    async def __start_playwright(self) -> None:
        self.playwright = await async_playwright().start()

        if self._browser_name == "chromium":
            self.browser_type = self.playwright.chromium
        elif self._browser_name == "firefox":
            self.browser_type = self.playwright.firefox
        elif self._browser_name == "webkit":
            self.browser_type = self.playwright.webkit
        elif self._no_context:
            # Not need create context or page
            pass
        else:
            raise TypeError("unsupported browser")
        if not self._no_context:
            # TODO: we need to find a way to force frozen executable to use the same
            # directory as non-frozen one, e.g. by mangling PLAYWRIGHT_BROWSERS_PATH
            # or sys.frozen
            if self._browser_persistent_option.get("user_data_dir"):
                # ToDo: check_profile
                if self.__check_open_dir:
                    self.check_close_profile(self._browser_persistent_option.get("user_data_dir"))
                self.context = await self.browser_type.launch_persistent_context(**self._browser_persistent_option)
                self.browser = self.context.browser or self.context
                self._api_request_context = self.context.request
            else:
                self.browser = await self.browser_type.launch(**self._browser_option)
                self.context = await self.browser.new_context(**self._context_option)
                self._api_request_context = self.context.request

            self.page = await self.first_page()

    # def stop(self) -> None:
    #     self.loop.call_soon_threadsafe(self.loop.stop)

    def stop(self) -> None:
        # NOTE: if we don't do this and some job sent
        # to a threadpool executor raises and triggers
        # the closing of the playwright driver, then a
        # catastrophic chain reaction of exception will
        # make some jobs hang up and block indefinitely
        # which will cause a deadlock.
        # TODO::
        with self.running_futures_lock:
            for fut in self.running_futures:
                if not fut.done():
                    fut.cancel()

        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    async def __stop_playwright(self) -> None:
        # NOTE: we need to make sure those were actually launched, in
        # case of a nasty race condition
        try:
            if hasattr(self, "page") and not self.page.is_closed():
                await self.page.close()
        except:
            pass
        try:
            if hasattr(self, "context"):
                if hasattr(self.context, "is_connected"):
                    if self.context.is_connected():
                        await self.context.close()
                else:
                    await self.context.close()
        except:
            pass
        try:
            if hasattr(self, "browser"):
                if hasattr(self.browser, "is_connected"):
                    if self.browser.is_connected():
                        await self.browser.close()
                else:
                    await self.browser.close()
        except:
            pass
        try:
            # NOTE: this hangs without the proper child watcher
            if hasattr(self, "playwright"):
                await self.playwright.stop()
        except:
            pass

    def check_close_profile(self, path):
        try:
            import psutil
            for proc in psutil.process_iter():
                name = proc.name()
                if "chrome.exe" in name:
                    cmd = proc.cmdline()
                    user = list(filter(lambda x: "--user-data-dir" in x, cmd))
                    if user:
                        # path_old.add(p)
                        p = os.path.normpath(user[0].split("=")[-1])
                        if os.path.normpath(path) == p and self.__close_already_profile:
                            proc.terminate()

                elif "firefox.exe" in name:
                    cmd = proc.cmdline()
                    user = list(filter(lambda x: "-profile" in x, cmd))
                    if user:
                        p = os.path.normpath(cmd[cmd.index(user[0]) + 1])
                        if os.path.normpath(path) == p and self.__close_already_profile:
                            proc.terminate()
        except:
            Logger.exception("check_close_profile")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()

    def check_is_install(self, browser):
        env = self.get_driver_env()
        driver_executable, driver_cli = compute_driver_executable()

        completed_process = subprocess.check_output([driver_executable, driver_cli, 'install', browser, '--dry-run'],
                                                    env=env,
                                                    **creation_flags_dict())

        locale_ = ":".join(next(filter(lambda x: "Install location" in x,
                                       completed_process.decode().split("\n")), "").split(":")[1:]).strip()

        return locale_ and os.path.exists(locale_)

    @staticmethod
    def get_driver_env():
        env = get_driver_env()

        # env["PLAYWRIGHT_BROWSERS_PATH"] =
        # NOTE: we do this to deal with pyinstaller
        if getattr(sys, "frozen", False):
            env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")
        return env

    def run_playwright(self, *args: str):
        env = self.get_driver_env()
        driver_executable, driver_cli = compute_driver_executable()

        with subprocess.Popen([driver_executable, driver_cli, *args], env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, **creation_flags_dict()) as process:
            for line in process.stdout:
                Logger.info(line.decode('utf-8'))
                if self.install_callback:
                    self.install_callback(line.decode('utf-8'))

    ####################################################################################################################
    async def first_page(self) -> "Page":
        page = self.context.pages[0] if self.context.pages else await self.context.new_page()

        if self._stealthy:
            from playwright_stealth import stealth_async
            await stealth_async(page)
        return page

    async def close(self):
        await self.create_task(self.__stop_playwright())
        self.stop()

    async def goto(self, url, *args, page=None, **kwargs):
        page = page or self.page
        return await self.create_task(page.goto(url, *args, **kwargs))

    async def add_script_tag(self, *args, page=None, **kwargs):
        page = page or self.page
        return await self.create_task(page.add_script_tag(*args, **kwargs))

    async def expose_function(self, *args, page=None, **kwargs):
        page = page or self.page
        return await self.create_task(page.expose_function(*args, **kwargs))

    async def page_wait_for_function(self, *args, page=None, **kwargs):
        page = page or self.page
        return await self.create_task(page.wait_for_function(*args, **kwargs))

    async def page_evaluate(self, *args, page=None, **kwargs):
        page = page or self.page
        return await self.create_task(page.evaluate(*args, **kwargs))

    ####################################################################################################################
    def sleep(self, val, timeout_=None):
        if timeout_ is None:
            timeout_ = val if val > 5 else 5
        self.run_threadsafe(asyncio.sleep(val), timeout_=timeout_)

    def goto_sync(self, url, *args, page=None, timeout_=60, **kwargs):
        page = page or self.page
        return self.run_threadsafe(page.goto(url, *args, **kwargs), timeout_=timeout_)

    def add_script_tag_sync(self, *args, page=None, timeout_=60, **kwargs):
        page = page or self.page
        return self.run_threadsafe(page.add_script_tag(*args, **kwargs), timeout_=timeout_)

    def expose_function_sync(self, *args, page=None, timeout_=60, **kwargs):
        page = page or self.page
        return self.run_threadsafe(page.expose_function(*args, **kwargs), timeout_=timeout_)

    def page_wait_for_function_sync(self, *args, page=None, timeout_=60, **kwargs):
        page = page or self.page
        return self.run_threadsafe(page.wait_for_function(*args, **kwargs), timeout_=timeout_)

    def page_evaluate_sync(self, *args, page=None, timeout_=60, **kwargs, ):
        page = page or self.page
        return self.run_threadsafe(page.evaluate(*args, **kwargs), timeout_=timeout_)

    def sync_close(self, timeout_=60):
        self.run_threadsafe(self.__stop_playwright(), timeout_=timeout_)
        self.stop()

    ###########################
    def __handle_future(self, future: Future, timeout=None):
        with self.running_futures_lock:
            self.running_futures.add(future)

        try:
            return future.result(timeout=timeout)
        finally:
            with self.running_futures_lock:
                self.running_futures.remove(future)

    def run_in_loop(self, task):
        # it to run Any task in self.loop
        future = asyncio.run_coroutine_threadsafe(task, self.loop)
        return self.__handle_future(future)

    async def to_do_with_callback_(self, task, callback: Optional[Callable[[Page], Awaitable[None]]] = None, ):
        # TODO::
        r = await task()
        if callback:
            callback(r)
        return r

    def to_do_with_callback(
            self,
            task,
            callback: Optional[Callable[[Page], Awaitable[None]]] = None,
    ):
        return self.run_threadsafe(self.to_do_with_callback_(task, callback=callback, ))


def creation_flags_dict():
    try:
        if sys_os == 'Windows':
            return {"creationflags": subprocess.CREATE_NO_WINDOW}
    except:
        Logger.exception("creation_flags_dict")
    return {}
