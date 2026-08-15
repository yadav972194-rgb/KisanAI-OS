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
