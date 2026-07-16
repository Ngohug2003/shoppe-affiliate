import httpx
import pytest

from app.services.product_metadata_service import (
    ProductMetadataError,
    ShopeeOpenGraphMetadataProvider,
)


async def test_open_graph_provider_extracts_title_and_shopee_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr(
        "app.services.product_metadata_service.ensure_public_host", allow_public_host
    )
    html = """
    <html><head>
      <meta content="Sản phẩm thử nghiệm" property="og:title">
      <meta property="og:image"
            content="https://down-vn.img.susercontent.com/file/example">
    </head></html>
    """
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, text=html, headers={"content-type": "text/html"})
    )

    async with httpx.AsyncClient(transport=transport) as client:
        metadata = await ShopeeOpenGraphMetadataProvider().fetch(
            "https://shopee.vn/product/123/456", client=client
        )

    assert metadata.title == "Sản phẩm thử nghiệm"
    assert metadata.image_url.startswith("https://down-vn.img.susercontent.com/")
    assert metadata.source == "shopee_open_graph"


async def test_open_graph_provider_rejects_non_shopee_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr(
        "app.services.product_metadata_service.ensure_public_host", allow_public_host
    )
    html = """
    <meta property="og:title" content="Sản phẩm">
    <meta property="og:image" content="https://evil.example/image.jpg">
    """
    transport = httpx.MockTransport(lambda _: httpx.Response(200, text=html))

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProductMetadataError, match="title or image"):
            await ShopeeOpenGraphMetadataProvider().fetch(
                "https://shopee.vn/product/123/456", client=client
            )
