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
from contextlib import contextmanager

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
    nodeid = uuid.getnode()
    dbname = None

    def __init__(self, path=None):
        self.openDB(path)
        
    def getDefaultPath(self):
        return os.path.join(sys.exec_prefix, 'flightData.db')

    def openDB(self, path=None):
        if path is None:
            path = self.dbname or self.getDefaultPath()
        else: self.dbname = None

        if isinstance(path, basestring):
            db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        elif not hasattr(path, 'executemany'):
            raise TypeError("Expected a valid path or a db2api compatible DB")
        else: 
            db = path
            path = None

        if self.dbname is None:
            self._initSqliteDb(db)
            self._initDbTables(db)

        return db

    @contextmanager
    def usingDB(self):
        if self.dbname is None:
            raise RuntimeError("DBName is not initialized. Call openDB first.")

        db = sqlite3.connect(self.dbname, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            with db:
                yield db
        finally:
            db.close()

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
        if bAddInfo:
            self.addSystemInfo()

        self._next_excepthook = sys.excepthook
        sys.excepthook = self.exceptHook

    def addSystemInfo(self):
        si = self._gatherSystemInfo()
        return self.addInfo(si)

    def addInfo(self, info):
        node = self.nodeid
        with self.usingDB() as db:
            for k,v in self._iterFlatNS(info):
                db.execute(
                    'replace into flightDataInfo \n'
                    '  values (?, ?, ?)', (node, k, v))

    _gatherSystemInfo = staticmethod(gatherSystemInfo)
    _iterFlatNS = staticmethod(iterFlatNS)

    def exceptHook(self, etype, evalue, etb):
        tde = TracebackDataEntry(etype, evalue, etb)
        print >> sys.stderr, tde

        rec = tde.getJsonExceptionRecord(node=self.nodeid)
        with self.usingDB() as db:
            db.execute(
                'insert or ignore into flightDataExceptionTable\n'
                '  values (:exc_hash, :exc_hashPartial, :exc_type, :exc_msg, :exc_tb)', rec)
            db.execute(
                'insert into flightDataExceptionLog\n'
                '  values (:node, :exc_hash, :exc_type, :exc_msg, :exc_ts, :exc_ts0)', rec)

