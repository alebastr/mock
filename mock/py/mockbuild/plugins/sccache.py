# -*- coding: utf-8 -*-
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:textwidth=0:
# License: GPL-2.0-or-later see COPYING
# Written by Aleksei Bavshin
# Copyright (C) 2023 Aleksei Bavshin <alebastr@fedoraproject.org>

# python library imports

# our imports
from mockbuild.mounts import BindMountPoint
from mockbuild.trace_decorator import getLog, traceLog
from mockbuild import file_util

requires_api_version = "1.1"

SCCACHE_DIR = "/var/cache/sccache"


# plugin entry point
@traceLog()
def init(plugins, conf, buildroot):
    SCCache(plugins, conf, buildroot)


class SCCache():
    """enables sccache in buildroot/rpmbuild"""
    # pylint: disable=too-few-public-methods
    @traceLog()
    def __init__(self, plugins, conf, buildroot):
        if buildroot.is_bootstrap:
            return
        self.buildroot = buildroot
        self.config = buildroot.config
        self.state = buildroot.state
        self.sccache_opts = conf
        tmpdict = self.sccache_opts.copy()
        tmpdict.update({"chrootuid": self.buildroot.chrootuid})
        self.sccachePath = self.sccache_opts["dir"] % tmpdict
        buildroot.preexisting_deps.append("sccache")
        plugins.add_hook("preinit", self._sccachePreInitHook)
        buildroot.mounts.add(
            BindMountPoint(srcpath=self.sccachePath, bindpath=buildroot.make_chroot_path(SCCACHE_DIR)))

    # =============
    # 'Private' API
    # =============
    # set up the sccache dir.
    # we also set a few variables used by sccache to find the shared cache.
    @traceLog()
    def _sccachePreInitHook(self):
        getLog().info("enabled sccache")
        envupd = {
            "RUSTC_WRAPPER": "/usr/bin/sccache",
            "SCCACHE_DIR": SCCACHE_DIR,
            "SCCACHE_UMASK": "002",
            "SCCACHE_CACHE_SIZE": str(self.sccache_opts["max_cache_size"]),
        }
        self.buildroot.env.update(envupd)

        file_util.mkdirIfAbsent(self.buildroot.make_chroot_path(SCCACHE_DIR))
        file_util.mkdirIfAbsent(self.sccachePath)
        self.buildroot.uid_manager.changeOwner(self.sccachePath, recursive=True)
