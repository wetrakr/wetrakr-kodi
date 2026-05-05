"""
service.py — WeTrakr Scrobbler entry point for Kodi.

Runs as a background service (xbmc.service extension point).
On first launch, triggers Device Code authorization flow.
Then monitors playback events and periodically checks progress.
"""

import xbmc
import xbmcaddon

from resources.lib import auth
from resources.lib.player import WeTrakrPlayer

POLL_INTERVAL = 30  # seconds between progress checks


def run():
    addon = xbmcaddon.Addon("script.wetrakr")
    xbmc.log(
        "[WeTrakr] Service started (v{})".format(addon.getAddonInfo("version")),
        xbmc.LOGINFO
    )

    # Check if authenticated — if not, run device code flow
    if not auth.is_authenticated():
        xbmc.log("[WeTrakr] Not authenticated — starting device code flow", xbmc.LOGINFO)
        if not auth.run_device_auth_flow():
            xbmc.log("[WeTrakr] Auth flow cancelled or failed — service will wait for manual setup", xbmc.LOGINFO)

    monitor = xbmc.Monitor()
    player = WeTrakrPlayer()

    while not monitor.abortRequested():
        # Check progress if something is playing
        if player.isPlayingVideo() and player.current_item and not player.scrobbled:
            player.check_progress()

        # Wait for abort or next poll cycle
        if monitor.waitForAbort(POLL_INTERVAL):
            break

    xbmc.log("[WeTrakr] Service stopped", xbmc.LOGINFO)


if __name__ == "__main__":
    run()
