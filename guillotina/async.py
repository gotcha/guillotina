# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.tz import tzlocal
from guillotina import logger
from guillotina.browser import ErrorResponse
from guillotina.browser import UnauthorizedResponse
from guillotina.browser import View
from guillotina.exceptions import Unauthorized
from guillotina.interfaces import SHARED_CONNECTION
from guillotina.transactions import abort
from guillotina.transactions import commit
from zope.interface import Interface

import asyncio


_zone = tzlocal()


class IAsyncUtility(Interface):

    async def initialize(self):
        pass


class IQueueUtility(IAsyncUtility):
    pass


class QueueUtility(object):

    def __init__(self, settings):
        self._queue = asyncio.PriorityQueue()
        self._exceptions = False
        self._total_queued = 0

    async def initialize(self, app=None):
        # loop
        self.app = app
        while True:
            got_obj = False
            try:
                priority, view = await self._queue.get()
                got_obj = True
                if view.request.conn.transaction_manager is None:
                    # Connection was closed
                    # Open DB
                    db = view.request.application[view.request._db_id]
                    if SHARED_CONNECTION:
                        view.request.conn = db.conn
                    else:
                        # Create a new conection
                        view.request.conn = db.open()
                    view.context = view.request.conn.get(view.context._p_oid)

                txn = view.request.conn.transaction_manager.begin(view.request)
                try:
                    view_result = await view()
                    if isinstance(view_result, ErrorResponse):
                        await abort(txn, view.request)
                    elif isinstance(view_result, UnauthorizedResponse):
                        await abort(txn, view.request)
                    else:
                        await commit(txn, view.request)
                except Unauthorized:
                    await abort(txn, view.request)
                except Exception as e:
                    logger.error(
                        "Exception on writing execution",
                        exc_info=e)
                    await abort(txn, view.request)
            except KeyboardInterrupt or MemoryError or SystemExit or asyncio.CancelledError:
                self._exceptions = True
                raise
            except Exception as e:  # noqa
                self._exceptions = True
                logger.error('Worker call failed', exc_info=e)
            finally:
                if SHARED_CONNECTION is False and hasattr(view.request, 'conn'):
                    view.request.conn.close()
                if got_obj:
                    self._queue.task_done()

    @property
    def exceptions(self):
        return self._exceptions

    @property
    def total_queued(self):
        return self._total_queued

    async def add(self, view, priority=3):
        await self._queue.put((priority, view))
        self._total_queued += 1
        return self._queue.qsize()

    async def finalize(self, app):
        pass


class QueueObject(View):

    def __init__(self, context, request):
        # not sure if we need proxy object here...
        # super(QueueObject, self).__init__(context, TransactionProxy(request))
        super(QueueObject, self).__init__(context, request)
        self.time = datetime.now(tz=_zone).timestamp()

    def __lt__(self, view):
        return self.time < view.time
