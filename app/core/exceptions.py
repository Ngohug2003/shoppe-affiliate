class ApplicationError(Exception):
    """Base exception for expected application failures."""

    status_code = 422
    default_message = "Yêu cầu không thể xử lý"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    status_code = 404


class AuthenticationError(ApplicationError):
    status_code = 401


class AuthorizationError(ApplicationError):
    status_code = 403


class UpstreamServiceError(ApplicationError):
    status_code = 502


class ServiceUnavailableError(ApplicationError):
    status_code = 503


class InvalidCredentialsError(AuthenticationError):
    default_message = "Email hoặc mật khẩu không chính xác"


class InvalidAuthenticationError(AuthenticationError):
    default_message = "Thông tin xác thực không hợp lệ"


class AdministratorRequiredError(AuthorizationError):
    default_message = "Yêu cầu quyền quản trị viên"


class TelegramWebhookNotConfiguredError(ServiceUnavailableError):
    default_message = "Telegram webhook chưa được cấu hình"


class InvalidTelegramWebhookSecretError(AuthorizationError):
    default_message = "Telegram webhook secret không hợp lệ"


class AffiliateShopsNotFoundError(NotFoundError):
    default_message = "Chưa có cửa hàng affiliate nào"


class AffiliateShopProductsNotFoundError(NotFoundError):
    def __init__(self, shop_id: str) -> None:
        super().__init__(f"Không tìm thấy sản phẩm affiliate của shop {shop_id}")


class AffiliateProductsNotFoundError(NotFoundError):
    def __init__(self, *, page: int, total: int) -> None:
        message = (
            "Không tìm thấy sản phẩm affiliate phù hợp"
            if total == 0
            else f"Trang {page} không có dữ liệu"
        )
        super().__init__(message)


class ShopeeProductUrlRequiredError(ApplicationError):
    default_message = "URL Shopee không phải là URL sản phẩm"


class InvalidShopeeUrlError(ApplicationError):
    """Raised when a URL is not a supported public Shopee URL."""


class ShopeeUrlResolutionError(UpstreamServiceError):
    """Raised when a supported short URL cannot be resolved safely."""
