# -*- encoding: utf-8 -*-
# flake8: noqa

import json


async def test_get_the_root(guillotina):
    requester = await guillotina
    response, status = await requester('GET', '/')
    assert response['static_directory'] == ['static', 'module_static']
    assert response['databases'] == ['db']
    assert response['static_file'] == ['favicon.ico']


async def test_get_db(guillotina):
    requester = await guillotina
    response, status = await requester('GET', '/db')
    assert response['containers'] == []


async def test_get_container(container_requester):
    async with await container_requester as requester:
        response, status = await requester('GET', '/db/guillotina')
        assert response['@type'] == 'Container'


async def test_get_content(container_requester):
    async with await container_requester as requester:
        response, status = await requester(
            'POST',
            '/db/guillotina',
            data=json.dumps({
                '@type': 'Item',
                'id': 'hello',
                'title': 'Hola'
            }))
        assert status == 201
        response, status = await requester(
            'GET',
            '/db/guillotina/hello')
        assert status == 200


async def test_content_paths_are_correct(container_requester):
    async with await container_requester as requester:
        response, status = await requester(
            'POST',
            '/db/guillotina',
            data=json.dumps({
                '@type': 'Item',
                'id': 'hello',
                'title': 'Hola'
            }))
        assert status == 201
        response, status = await requester(
            'GET',
            '/db/guillotina/hello')
        assert status == 200
        assert '/db/guillotina/hello' in response['@id']
