class ApplicationError(Exception):
    """Base exception for expected application failures."""


class InvalidShopeeUrlError(ApplicationError):
    """Raised when a URL is not a supported public Shopee URL."""


class ShopeeUrlResolutionError(ApplicationError):
    """Raised when a supported short URL cannot be resolved safely."""
