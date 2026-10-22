import io
import logging
import zipfile
from unittest.mock import Mock, PropertyMock

import pytest
from requests import HTTPError, Response

from modules.common import req


@pytest.mark.parametrize('content_type', ['application/zip', 'application/octet-stream', '', 'text/plain'])
def test_zip_response_logs_metadata_without_decoding_or_changing_body(requests_mock, caplog, content_type):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as handle:
        handle.writestr('vehicle.json', '{"soc": 55}')
    body = archive.getvalue()
    requests_mock.get('https://example.org/data', content=body, headers={'Content-Type': content_type})
    caplog.set_level(logging.DEBUG, logger=req.__name__)
    with req.get_http_session() as session:
        response = session.get('https://example.org/data')
    assert response.content == body
    assert 'binary data' in caplog.text
    assert f'{len(body)} bytes' in caplog.text
    assert 'vehicle.json' not in caplog.text
    assert '"soc"' not in caplog.text


@pytest.mark.parametrize('content_type', ['application/json', 'text/html; charset=utf-8', ''])
def test_text_response_is_still_logged(requests_mock, caplog, content_type):
    body = '{"soc": 55}'
    requests_mock.get('https://example.org/data', text=body, headers={'Content-Type': content_type})
    caplog.set_level(logging.DEBUG, logger=req.__name__)
    with req.get_http_session() as session:
        response = session.get('https://example.org/data')
    assert response.json() == {'soc': 55}
    assert 'Get-Response: ' + body in caplog.text


def test_binary_content_type_does_not_access_response_text(caplog):
    response = Mock(spec=Response, headers={'Content-Type': 'application/octet-stream'}, content=b'\x00\xff')
    type(response).text = PropertyMock(side_effect=AssertionError('Binary body must not be decoded'))
    caplog.set_level(logging.DEBUG, logger=req.__name__)
    req._log_response(response)
    assert 'binary data (application/octet-stream, 2 bytes)' in caplog.text


def test_disabled_debug_does_not_read_response(caplog):
    caplog.set_level(logging.INFO, logger=req.__name__)
    req._log_response(object())


def test_error_status_still_raises_with_full_response(requests_mock):
    requests_mock.get('https://example.org/data', status_code=429, text='Too many requests')
    with req.get_http_session() as session:
        with pytest.raises(HTTPError) as error:
            session.get('https://example.org/data')
    assert error.value.response.status_code == 429
    assert error.value.response.text == 'Too many requests'
