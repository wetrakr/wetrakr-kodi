"""
script.py — entry point of RunScript(script.wetrakr, <action>), used by the
buttons in the add-on settings. The work happens in the background service,
which listens to these notifications (resources/lib/sync_monitor.py).

  sync        full library sync now (with a progress dialog)
  sync_reset  forget the local sync state and start over
"""

import sys

import xbmc
import xbmcgui

ACTIONS = {
    "sync": ("wetrakr_sync_now", "Library sync started"),
    "sync_reset": ("wetrakr_sync_reset", "Sync state reset, syncing again"),
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "sync"
    signal, message = ACTIONS.get(action, ACTIONS["sync"])
    xbmc.executebuiltin('NotifyAll(script.wetrakr, {})'.format(signal))
    xbmcgui.Dialog().notification("WeTrakr", message, xbmcgui.NOTIFICATION_INFO, 3000, False)
