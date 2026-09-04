"""
KisanAI OS
OTP Provider Base

Replaceable SMS/OTP delivery contract (Phase 3). The auth layer never
depends on a specific SMS gateway: it talks only to the ``OtpProvider``
interface. Swapping in a real gateway (MSG91, Twilio, AWS SNS, ...)
later means implementing this interface and wiring it through
``get_otp_provider()`` - no API changes required.

Security notes:
  - The code is delivered to the *user's* phone, never echoed back over
    the API - except in mock mode (development only), where the code is
    returned as ``dev_otp`` so local/test flows can complete.
  - Provider failures must not leak gateway internals to the client.
"""

from abc import ABC, abstractmethod

from config.core.logger import logger


class OtpProviderError(Exception):
    """OTP delivery could not be completed."""


class OtpProvider(ABC):
    """Interface every OTP delivery provider must implement."""

    @abstractmethod
    def send(self, mobile: str, code: str, purpose: str) -> None:
        """Deliver ``code`` to ``mobile`` for ``purpose``.

        Raises ``OtpProviderError`` on delivery failure. Never returns
        the code.
        """


class MockOtpProvider(OtpProvider):
    """Development-only provider.

    Logs the code and marks it as deliverable. The caller decides
    whether to echo it back as ``dev_otp`` (mock mode only).
    """

    def send(self, mobile: str, code: str, purpose: str) -> None:
        logger.info(
            "MOCK OTP for mobile=%s purpose=%s code=%s",
            mobile,
            purpose,
            code,
        )


class ConsoleOtpProvider(OtpProvider):
    """Development/provider-fallback provider.

    Prints the code to the server log. Safe for production-ish
    environments that have no SMS gateway configured but still need a
    human-readable delivery path.
    """

    def send(self, mobile: str, code: str, purpose: str) -> None:
        logger.info(
            "CONSOLE OTP for mobile=%s purpose=%s code=%s",
            mobile,
            purpose,
            code,
        )


class TwilioOtpProvider(OtpProvider):
    """Production SMS/OTP delivery provider backed by Twilio's Messages API.

    Delivers codes over HTTPS to the stable Twilio Messages endpoint::

        POST /2010-04-01/Accounts/{account_sid}/Messages.json

    Delivery is reported as successful only when Twilio answers HTTP
    200/201. Anything else - transport/network errors, throttling or a
    non-2xx response - raises ``OtpProviderError`` so the service responds
    honestly ("Unable to send OTP") instead of claiming a delivery that
    did not happen.

    Security:
      - credentials (Account SID / Auth Token / sender) are read through
        the settings layer (server-controlled), never from client input,
        and never logged or leaked in error messages;
      - the OTP code is never logged;
      - gateway internals and Twilio error bodies never reach the caller.
    """

    MESSAGES_URL = (
        "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    )

    def __init__(
        self,
        account_sid,
        auth_token,
        messaging_service_sid=None,
        from_number=None,
        timeout=10,
        http_client=None,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.messaging_service_sid = messaging_service_sid
        self.from_number = from_number
        self.timeout = timeout
        # Optional injected HTTP client (used by tests); when None a real
        # ``httpx.Client`` is created lazily per send.
        self._http_client = http_client

    def send(self, mobile: str, code: str, purpose: str) -> None:
        if not (self.account_sid and self.auth_token):
            raise OtpProviderError(
                "Twilio OTP provider is not configured"
            )

        if not (self.messaging_service_sid or self.from_number):
            raise OtpProviderError(
                "Twilio OTP provider is not configured"
            )

        payload = {
            "To": (mobile or "").strip(),
            "Body": f"Your KisanAI verification code is {code}.",
        }

        if self.messaging_service_sid:
            payload["MessagingServiceSid"] = self.messaging_service_sid
        else:
            payload["From"] = self.from_number

        url = self.MESSAGES_URL.format(sid=self.account_sid)

        try:
            response = self._post(url, payload)
        except OtpProviderError:
            raise
        except Exception as error:  # network / transport failure
            logger.warning(
                "Twilio OTP delivery failed (purpose=%s)", purpose
            )
            raise OtpProviderError(
                "Unable to send OTP. Please try again later."
            ) from error

        if response.status_code not in (200, 201):
            logger.warning(
                "Twilio OTP delivery rejected "
                "(status=%s, purpose=%s)",
                response.status_code,
                purpose,
            )
            raise OtpProviderError(
                "Unable to send OTP. Please try again later."
            )

        logger.info("OTP delivered via Twilio (purpose=%s)", purpose)

    def _post(self, url, payload):
        """POST the payload to Twilio, returning the response.

        ``httpx`` is imported lazily so importing this module (and the
        whole providers package) never requires the optional runtime
        dependency; only an actual real Twilio send needs it, and a
        missing/broken client degrades to ``OtpProviderError``.
        """
        if self._http_client is not None:
            return self._http_client.post(url, data=payload)

        try:
            import httpx
        except ImportError as error:
            raise OtpProviderError(
                "Unable to send OTP. Please try again later."
            ) from error

        with httpx.Client(
            auth=(self.account_sid, self.auth_token),
            timeout=self.timeout,
        ) as client:
            return client.post(url, data=payload)
