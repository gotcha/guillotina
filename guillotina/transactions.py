from guillotina.exceptions import RequestNotFound
from guillotina.utils import get_current_request

import logging


logger = logging.getLogger('guillotina')


def _safe_get_request(request):
    if request is None:
        try:
            request = get_current_request()
        except RequestNotFound:
            pass
    return request


async def commit(request=None, warn=True):
    try:
        await get_tm(_safe_get_request(request)).commit()
    except AttributeError as e:
        if warn:
            logger.warn('Could not locate transaction manager to commit', exc_info=True)


async def abort(request=None):
    try:
        await _safe_get_request(request)._tm.abort()
    except AttributeError:
        # not part of transaction, ignore
        pass
        # logger.warn('Could not locate transaction manager to abort', exc_info=True)


def get_tm(request=None):
    """Return shared transaction manager (from request)

    This is used together with "with" syntax for wrapping mutating
    code into a request owned transaction.

    :param request: request owning the transaction

    Example::

        with get_tm(request) as txn:  # begin transaction txn

            # do something

        # transaction txn commits or raises ConflictError

    """
    return _safe_get_request(request)._tm


def get_transaction(request=None):
    return _safe_get_request(request)._tm.get()
