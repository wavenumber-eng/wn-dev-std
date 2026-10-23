from __future__ import annotations

import io
import ssl
import urllib.request

import certifi
from pytest import MonkeyPatch

from wn_dev_std.version_check import check_pypi_version, latest_pypi_version


def test_pypi_request_uses_fixed_bundle_without_host_roots(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SSL_CERT_FILE", "missing-host-bundle.pem")
    monkeypatch.setenv("SSL_CERT_DIR", "missing-host-directory")
    contexts: list[ssl.SSLContext] = []

    def urlopen(
        request: urllib.request.Request, *, timeout: float, context: ssl.SSLContext
    ) -> io.BytesIO:
        assert request.full_url == "https://pypi.org/pypi/wn-dev-std/json"
        assert timeout == 3.0
        contexts.append(context)
        return io.BytesIO(b'{"info":{"version":"2026.10.22"}}')

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    assert latest_pypi_version("wn-dev-std") == "2026.10.22"
    context = contexts[0]
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    certificates = context.get_ca_certs()
    names = {
        value
        for certificate in certificates
        for rdn in certificate["subject"]
        for key, value in rdn
        if key == "commonName"
    }
    assert certificates
    assert not names.intersection({"emSign ECC Root CA - G3", "AAA Certificate Services"})
    expected = ssl.create_default_context(cafile=certifi.where())
    assert context.get_ca_certs(binary_form=True) == expected.get_ca_certs(binary_form=True)


def test_tls_failure_warns_without_retry_or_disabled_verification(monkeypatch: MonkeyPatch) -> None:
    calls = 0

    def urlopen(*_args: object, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise ssl.SSLCertVerificationError("untrusted certificate")

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    result = check_pypi_version("2026.10.22")
    assert result.latest is None
    assert result.warning is not None
    assert "untrusted certificate" in result.warning
    assert calls == 1
