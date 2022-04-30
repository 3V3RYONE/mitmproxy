import shutil
import subprocess
import tempfile
import typing

from mitmproxy import command
from mitmproxy import ctx


def get_firefox_executable() -> typing.Optional[str]:
    for browser in (
            r"/usr/bin/firefox",
            r"/usr/lib/firefox"
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


class Firefoxstart:
    browser: typing.List[subprocess.Popen] = []
    tdir: typing.List[tempfile.TemporaryDirectory] = []

    @command.command("firefox.start")
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
                "--preferences",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ))
        print(str(self.browser))

    def done(self):
        for browser in self.browser:
            browser.kill()
        for tdir in self.tdir:
            tdir.cleanup()
        self.browser = []
        self.tdir = []
