# -*- coding: utf-8 -*-
from guillotina import configure
from guillotina.api.service import Service
from guillotina.async import IQueueUtility
from guillotina.component import queryUtility
from guillotina.interfaces import ICatalogUtility
from guillotina.interfaces import IResource
from guillotina.utils import get_content_path


@configure.service(
    context=IResource, method='GET', permission='guillotina.SearchContent', name='@search',
    summary='Make search request',
    parameters=[{
        "name": "q",
        "in": "query",
        "required": True,
        "type": "string"
    }],
    responses={
        "200": {
            "description": "Search results",
            "type": "object",
            "schema": {
                "$ref": "#/definitions/SearchResults"
            }
        }
    })
async def search_get(context, request):
    q = request.GET.get('q')
    search = queryUtility(ICatalogUtility)
    if search is None:
        return {
            'items_count': 0,
            'member': []
        }

    return await search.get_by_path(
        container=request.container,
        path=get_content_path(context),
        query=q)


@configure.service(
    context=IResource, method='POST',
    permission='guillotina.RawSearchContent', name='@search',
    summary='Make a complex search query',
    parameters=[{
        "name": "body",
        "in": "body",
        "schema": {
            "properties": {}
        }
    }],
    responses={
        "200": {
            "description": "Search results",
            "type": "object",
            "schema": {
                "$ref": "#/definitions/SearchResults"
            }
        }
    })
async def search_post(context, request):
    q = await request.json()
    search = queryUtility(ICatalogUtility)
    if search is None:
        return {
            'items_count': 0,
            'member': []
        }

    return await search.query(context, q)


@configure.service(
    context=IResource, method='POST',
    permission='guillotina.ReindexContent', name='@catalog-reindex',
    summary='Reindex entire container content',
    responses={
        "200": {
            "description": "Successfully reindexed content"
        }
    })
class CatalogReindex(Service):

    def __init__(self, context, request, security=False):
        super(CatalogReindex, self).__init__(context, request)
        self._security_reindex = security

    async def __call__(self):
        search = queryUtility(ICatalogUtility)
        await search.reindex_all_content(self.context, self._security_reindex)
        return {}


@configure.service(
    context=IResource, method='POST',
    permission='guillotina.ReindexContent', name='@async-catalog-reindex',
    summary='Asynchronously reindex entire container content',
    responses={
        "200": {
            "description": "Successfully initiated reindexing"
        }
    })
class AsyncCatalogReindex(Service):

    def __init__(self, context, request, security=False):
        super(AsyncCatalogReindex, self).__init__(context, request)
        self._security_reindex = security

    async def __call__(self):
        util = queryUtility(IQueueUtility)
        if util:
            await util.add(CatalogReindex(
                self.context, self.request, self._security_reindex))
        return {}


@configure.service(
    context=IResource, method='POST',
    permission='guillotina.ManageCatalog', name='@catalog',
    summary='Initialize catalog',
    responses={
        "200": {
            "description": "Successfully initialized catalog"
        }
    })
async def catalog_post(context, request):
    search = queryUtility(ICatalogUtility)
    await search.initialize_catalog(context)
    return {}


@configure.service(
    context=IResource, method='DELETE',
    permission='guillotina.ManageCatalog', name='@catalog',
    summary='Delete search catalog',
    responses={
        "200": {
            "description": "Successfully deleted catalog"
        }
    })
async def catalog_delete(context, request):
    search = queryUtility(ICatalogUtility)
    await search.remove_catalog(context)
    return {}
