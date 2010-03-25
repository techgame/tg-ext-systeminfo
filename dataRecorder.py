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

import os, sys
import uuid
import sqlite3

from . import gatherSystemInfo
from .tracebackData import TracebackDataEntry

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def iterFlatNS(ns):
    queue = [('', ns)]
    while queue:
        prefix, each = queue.pop()
        for k,v in each.items():
            if prefix: 
                k = prefix + '.' + k

            if not isinstance(v, (basestring, int, long, float)):
                if isinstance(v, list):
                    if v:
                        v = '", "'.join(str(e) for e in v)
                        v = '["%s"]' % v
                    else: v = '[]'
                else:
                    queue.append((k, v))
                    continue

            yield k, v

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class FlightDataRecorder(object):
    db = None
    nodeid = uuid.getnode()

    def __init__(self, path=None):
        self.open(path)
        
    def getDefaultPath(self):
        return os.path.join(sys.exec_prefix, 'flightData.db')

    def open(self, path=None):
        if path is None:
            path = self.getDefaultPath()

        if isinstance(path, basestring):
            db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
            self.db = db
            self._initSqliteDb(db)
        elif not hasattr(path, 'executemany'):
            raise TypeError("Expected a valid path or a db2api compatible DB")
        else: 
            db = path
            path = None

        self.db = db
        self._initDbTables(db)

    def _initSqliteDb(self, db):
        db.row_factory = sqlite3.Row
        r = db.execute('PRAGMA database_list;').fetchone()
        self.dbname = r[2]

    def _initDbTables(self, db):
        with db:
            db.execute('''
                create table if not exists flightDataInfo (
                    nodeId INTEGER,
                    key TEXT,
                    value TEXT,
                    primary key (nodeId, key) on conflict replace);''')
            db.execute('''
                create table if not exists flightDataExceptionTable (
                    exc_hash TEXT primary key on conflict ignore, 
                    exc_hashPartial TEXT,
                    exc_type TEXT,
                    exc_msg TEXT,
                    exc_tb TEXT);''')
            db.execute('''
                create table if not exists flightDataExceptionLog (
                    nodeId INTEGER,
                    exc_hash TEXT,
                    exc_type TEXT,
                    exc_msg TEXT,
                    exc_ts INTEGER,
                    exc_ts0 INTEGER,
                    primary key (nodeId, exc_hash) on conflict replace);''')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def install(self, bAddInfo=True):
        if self.db is None:
            self.open()

        if bAddInfo:
            self.addSystemInfo()

        self._next_excepthook = sys.excepthook
        sys.excepthook = self.exceptHook

    def addSystemInfo(self, si=None):
        if si is None:
            si = self._gatherSystemInfo()

        node = self.nodeid
        with self.db as db:
            for k,v in self._iterFlatNS(si):
                db.execute(
                    'replace into flightDataInfo \n'
                    '  values (?, ?, ?)', (node, k, v))

    _gatherSystemInfo = staticmethod(gatherSystemInfo)
    _iterFlatNS = staticmethod(iterFlatNS)

    def exceptHook(self, etype, evalue, etb):
        tde = TracebackDataEntry(etype, evalue, etb)
        print >> sys.stderr, tde

        rec = tde.getJsonExceptionRecord(node=self.nodeid)
        with self.db as db:
            db.execute(
                'insert or ignore into flightDataExceptionTable\n'
                '  values (:exc_hash, :exc_hashPartial, :exc_type, :exc_msg, :exc_tb)', rec)
            db.execute(
                'insert into flightDataExceptionLog\n'
                '  values (:node, :exc_hash, :exc_type, :exc_msg, :exc_ts, :exc_ts0)', rec)

