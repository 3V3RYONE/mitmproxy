import shutil
import subprocess
import tempfile
import typing

from mitmproxy import command
from mitmproxy import ctx


def get_firefox_executable() -> typing.Optional[str]:
    for browser in (
            "firefox"
    ):
        if shutil.which(browser):
            return browser

    return None


def get_firefox_flatpak() -> typing.Optional[str]:
    if shutil.which("flatpak"):
        for browser in (
            "org.mozilla.firefox"
        ):
            if subprocess.run(
                ["flatpak", "info", browser],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0:
                return browser

    return None


def get_browser_cmd() -> typing.Optional[typing.List[str]]:
    if browser := get_firefox_executable():
        return [browser]
    elif browser := get_firefox_flatpak():
        return ["flatpak", "run", "-p", browser]

    return None


class Browser:
    browser: typing.List[subprocess.Popen] = []
    tdir: typing.List[tempfile.TemporaryDirectory] = []

    @command.command("firefox_browser.start")
    def start(self) -> None:
        """
            Start an isolated instance of Firefox that points to the currently
            running proxy.
        """
        if len(self.browser) > 0:
            ctx.log.alert("Starting additional browser")

        cmd = get_browser_cmd()
        if not cmd:
            ctx.log.alert("Your platform is not supported yet - please submit a patch.")
            return

        tdir = tempfile.TemporaryDirectory()
        self.tdir.append(tdir)
        self.browser.append(subprocess.Popen(
            [
                *cmd,
                "--user-data-dir=%s" % str(tdir.name),
                "--proxy-server={}:{}".format(
                    ctx.options.listen_host or "127.0.0.1",
                    ctx.options.listen_port
                ),
                "--disable-fre",
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-extensions",

                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ))

    def done(self):
        for browser in self.browser:
            browser.kill()
        for tdir in self.tdir:
            tdir.cleanup()
        self.browser = []
        self.tdir = []
