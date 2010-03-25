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
from ctypes import (POINTER, sizeof, byref, cast, c_void_p)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kernel32 = ctypes.windll.Kernel32

# http://msdn.microsoft.com/en-us/library/ms724958(v=VS.85).aspx
# http://msdn.microsoft.com/en-us/library/ms724340(v=VS.85).aspx

WORD = ctypes.c_uint16
DWORD = ctypes.c_uint32
DWORDLONG = ctypes.c_uint64

_GetSystemInfo = Kernel32.GetSystemInfo
class _SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ('wProcessorArchitecture', WORD),
        ('wReserved', WORD),

        ('dwPageSize', DWORD),
        ('lpMinimumApplicationAddress', c_void_p),
        ('lpMaximumApplicationAddress', c_void_p),
        ('dwActiveProcessorMask', DWORD),
        ('dwNumberOfProcessors', DWORD),
        ('dwProcessorType', DWORD),
        ('dwAllocationGranularity', DWORD),
        ('wProcessorLevel', WORD),
        ('wProcessorRevision', WORD),]

def GetSystemInfo():
    si = _SYSTEM_INFO()
    _GetSystemInfo(byref(si))
    return si

_GlobalMemoryStatusEx = Kernel32.GlobalMemoryStatusEx
class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', DWORD),
        ('dwMemoryLoad', DWORD),
        ('ullTotalPhys', DWORDLONG),
        ('ullAvailPhys', DWORDLONG),
        ('ullTotalPageFile', DWORDLONG),
        ('ullAvailPageFile', DWORDLONG),
        ('ullTotalVirtual', DWORDLONG),
        ('ullAvailVirtual', DWORDLONG),
        ('ullAvailExtendedVirtual', DWORDLONG), ]

def GlobalMemoryStatusEx():
    ms = _MEMORYSTATUSEX()
    ms.dwLength = sizeof(ms)
    if _GlobalMemoryStatusEx(byref(ms)):
        return ms

def gatherSystemInfo_win32():
    ms = GlobalMemoryStatusEx()
    si = GetSystemInfo()

    r = {
      'memory': {
        'total': ms.ullTotalPhys,
        'available': ms.ullAvailPhys,

        'swapTotal': ms.ullTotalVirtual,
        'swapAvailable': ms.ullAvailVirtual,
        'pageSize': si.dwPageSize,},

      'cpu': {
        'ncpu': si.dwNumberOfProcessors,

        'cputype': si.dwProcessorType,
        'cpurevision': si.wProcessorRevision,
        'cpulevel': si.wProcessorLevel,
        },
      'platform': {
        'platform': platform.platform(),
        'version': platform.win32_ver()[0],
        },
    }
    return r

gatherSystemInfo = gatherSystemInfo_win32

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    from pprint import pprint
    pprint(gatherSystemInfo())

