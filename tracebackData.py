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

from __future__ import with_statement

import os, sys, time
import traceback
import hashlib

try: import json
except ImportError:
    import simplejson as json

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def timestamp():
    return int(time.time())

def findCommonSystemPrefix():
    p = sys.exec_prefix
    for e in sys.path:
        n = os.path.commonprefix([e, p])
        if (n.count('/')+n.count('\\')) > 2: 
            p = n
    return p

class TracebackDataEntry(object):
    exc = tb = None
    ts_startup = timestamp()
    systemPrefix = findCommonSystemPrefix()

    def __init__(self, etype, evalue, etb):
        self.ts = timestamp()
        self.ts0 = self.ts - self.ts_startup

        self.exc_type = '.'.join([etype.__module__, etype.__name__])
        self.exc = self.format_exc(etype, evalue)
        if etb:
            self.tb = self.extract_tb(etb)

    def _boundary_(self, bndV, bndCtx):
        return True

    def __cmp__(self, other):
        return cmp(self.exc, other.exc) or cmp(self.tb, other.tb)

    def __repr__(self): return format(self)
    def __str__(self): return format(self)
    def __format__(self, spec):
        r = []
        if self.tb is not None:
            r.append('Traceback (most recent call last):\n')
            r.extend(self.format_list(self.tb))
        r.extend(self.exc)
        return ''.join(r)

    def fixupTBEntry(self, tbe):
        fn = tbe[0].split(self.systemPrefix)[-1]
        fn = fn.replace('\\', '/')
        return (fn,)+tbe[1:]

    extract_tb = staticmethod(traceback.extract_tb)
    format_exc = staticmethod(traceback.format_exception_only)
    format_list = staticmethod(traceback.format_list)

    def getExceptionRecord(self, **rec):
        rec.update(
            exc_type=self.exc_type, 
            exc_msg=''.join(self.exc),
            exc_tb=self.tb,
            exc_ts=self.ts, 
            exc_ts0=self.ts0,)
        return rec

    def getJsonExceptionRecord(self, **rec):
        rec = self.getExceptionRecord(**rec)

        # normalize the traceback so the hash has meaning
        exc_tb = rec.pop('exc_tb')
        if exc_tb is not None:
            exc_tb = [self.fixupTBEntry(tbe) for tbe in exc_tb]
        # encode it as json, so it's easy to manipulate
        exc_tb = json.dumps(exc_tb, True, 
            sort_keys=True, indent=2, separators=(',',':'))

        # now hash the exception message and the traceback 
        # to get a unique message identifer
        h = hashlib.md5()
        h.update(rec['exc_type'])
        h.update(exc_tb)
        exc_hashPartial = h.hexdigest()

        h.update(rec['exc_msg'])
        exc_hash = h.hexdigest()

        rec.update(
            exc_tb=exc_tb, 
            exc_hashPartial=exc_hashPartial, 
            exc_hash=exc_hash)
        return rec

