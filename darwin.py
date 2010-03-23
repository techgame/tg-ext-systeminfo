#!/usr/bin/env python
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2010  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the MIT style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os, sys
import platform

import ctypes
from ctypes.util import find_library
from ctypes import (POINTER, sizeof, byref, cast,
    c_int32, c_int64, c_size_t, c_char, 
    c_char_p, c_void_p)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ctlNamesDefault = [
    ('hw.model', c_char*256),

    'hw.memsize', 'hw.usermem',
    'hw.pagesize', 'hw.cachelinesize',

    'hw.l1dcachesize', 'hw.l1icachesize', 'hw.l2cachesize', 

    'hw.ncpu', 'hw.physicalcpu', 'hw.logicalcpu', 'hw.packages',
    'hw.cputype', 'hw.cpusubtype', 

    'hw.cpufrequency', 'hw.tbfrequency', 'hw.busfrequency', ]

libc = ctypes.cdll.LoadLibrary(find_library('libc'))

# sysctlbyname paths can be found in: /usr/include/sys/sysctl.h with names like CTL_.*NAMES
_sysctlbyname = libc.sysctlbyname
_sysctlbyname.restype = ctypes.c_int32
_sysctlbyname.argtypes = [c_char_p, 
    c_void_p, POINTER(c_size_t), 
    c_void_p, c_size_t]

typeMapBySiz = [c_int32, c_int64]
typeMapBySiz = dict((sizeof(t), t) for t in typeMapBySiz)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def iterQuerySysCtl(ctlNames=None):
    if ctlNames is None:
        ctlNames = ctlNamesDefault
    if hasattr(ctlNames, 'items'):
        ctlNames = ctlNames.items()

    buf = ctypes.create_string_buffer(1024)
    sz = c_size_t(sizeof(buf))
    for n in ctlNames:
        if isinstance(n, tuple):
            n, t = n
        else: t = None

        sz.value = sizeof(buf)
        if 0 > _sysctlbyname(n, byref(buf), byref(sz), None, 0):
            yield n, None
            continue

        if t is None:
            t = typeMapBySiz.get(sz.value)
        if t is not None:
            v = cast(buf, POINTER(t)).contents
        yield n, v.value

def querySysCtl(ctlNames=None):
    return dict(iterQuerySysCtl(ctlNames))

def gatherSystemInfo_darwin():
    ns = querySysCtl()

    r = {
      'hwmisc': {
        'machineModel': ns['hw.model'],
        'timebaseFrequency': ns['hw.tbfrequency'],
        'busFrequency': ns['hw.busfrequency'],
        'cpuFrequency': ns['hw.cpufrequency'],
        },

      'memory': {
        'total': ns['hw.memsize'],
        'user': ns['hw.usermem'],

        'L1_D': ns['hw.l1dcachesize'],
        'L1_I': ns['hw.l1icachesize'],
        'L2': ns['hw.l2cachesize'],

        'pageSize': ns['hw.pagesize'],
        'cacheLineSize': ns['hw.cachelinesize'],
        },

      'cpu': {
        'ncpu': ns['hw.ncpu'],
        'physical': ns['hw.physicalcpu'],
        'logical': ns['hw.logicalcpu'],
        'packages': ns['hw.packages'],

        'cputype': ns['hw.cputype'],
        'cpusubtype': ns['hw.cpusubtype'],
        },
      'platform': {
        'platform': platform.platform(),
        'version': platform.mac_ver()[0], 
        },
    }
    return r

gatherSystemInfo = gatherSystemInfo_darwin

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    from pprint import pprint
    pprint(gatherSystemInfo())

