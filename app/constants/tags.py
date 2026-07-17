AUTH_TAG = "[AUTH] Authentication"
ADMIN_AFFILIATE_TAG = "[ADMIN] Affiliate Catalog"
PUBLIC_AFFILIATE_TAG = "[PUBLIC] Affiliate Catalog"
PUBLIC_HEALTH_TAG = "[PUBLIC] Health"
PUBLIC_TELEGRAM_TAG = "[PUBLIC] Telegram Webhook"

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": AUTH_TAG,
        "description": "Đăng nhập và thông tin tài khoản hiện tại.",
    },
    {
        "name": ADMIN_AFFILIATE_TAG,
        "description": "Thao tác catalog yêu cầu tài khoản quản trị.",
    },
    {
        "name": PUBLIC_AFFILIATE_TAG,
        "description": "Dữ liệu catalog được phép truy cập công khai.",
    },
    {
        "name": PUBLIC_HEALTH_TAG,
        "description": "Kiểm tra trạng thái ứng dụng và database.",
    },
    {
        "name": PUBLIC_TELEGRAM_TAG,
        "description": "Webhook công khai được bảo vệ bằng Telegram secret.",
    },
]
