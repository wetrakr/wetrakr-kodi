"""
service_runner.py — main loop of the WeTrakr Scrobbler background service.

Handles the device-code authentication on first launch, then runs the
periodic playback progress checks and the library sync scheduler until Kodi
requests an abort.
"""

import xbmc
import xbmcaddon

from resources.lib import auth
from resources.lib.player import WeTrakrPlayer
from resources.lib.notification import notify as _notify
from resources.lib.sync_monitor import SyncMonitor
from resources.lib.scheduler import Scheduler

POLL_INTERVAL = 30  # seconds between progress checks


def run():
    addon = xbmcaddon.Addon("script.wetrakr")
    xbmc.log(
        "[WeTrakr] Service started (v{})".format(addon.getAddonInfo("version")),
        xbmc.LOGINFO
    )

    if not auth.is_authenticated():
        xbmc.log("[WeTrakr] Not authenticated — starting device code flow", xbmc.LOGINFO)
        if not auth.run_device_auth_flow():
            xbmc.log(
                "[WeTrakr] Auth flow cancelled or failed — service will wait for manual setup",
                xbmc.LOGINFO
            )

    player = WeTrakrPlayer()
    # The monitor listens to library events (manual marks, scans, wake) and
    # the scheduler decides when the library sync runs. The player tells them
    # what is playing so its own plays are not uploaded twice.
    monitor = SyncMonitor(player)
    scheduler = Scheduler(monitor, player)
    player.sync_monitor = monitor
    player.scheduler = scheduler
    warned_reauth = False

    while not monitor.abortRequested():
        # If a scrobble was rejected with 401/403, the saved token is stale and
        # the user must reconnect. Never open the auth dialog while a video is
        # playing — a WindowDialog mid-playback renegotiates the renderer and can
        # freeze passthrough audio. Warn once (non-blocking) and re-login only
        # once playback has stopped.
        if auth.token_was_rejected():
            if not warned_reauth:
                _notify("WeTrakr", "Connection expired — please reconnect", 8000)
                warned_reauth = True
            if not player.isPlayingVideo():
                xbmc.log("[WeTrakr] Stale token — re-running device code flow", xbmc.LOGINFO)
                auth.run_device_auth_flow()
                warned_reauth = False
        else:
            warned_reauth = False
            if player.isPlayingVideo() and player.current_item and not player.scrobbled:
                player.check_progress()
            try:
                scheduler.tick()
            except Exception as e:
                xbmc.log("[WeTrakr] Scheduler tick error: {}".format(e), xbmc.LOGERROR)

        if monitor.waitForAbort(POLL_INTERVAL):
            break

    xbmc.log("[WeTrakr] Service stopped", xbmc.LOGINFO)
