# Shopee Affiliate Catalog

Dịch vụ FastAPI quản lý một danh mục sản phẩm affiliate theo cửa hàng Shopee.

## Kiến trúc thư mục

Dự án sử dụng layered architecture đơn giản:

```text
app/
├── api/v1/routes/       # Khai báo endpoint và dependency FastAPI
├── controllers/         # Điều phối request/response, ánh xạ lỗi HTTP
├── services/            # Nghiệp vụ auth, catalog, metadata, URL, Telegram
├── repositories/        # Truy vấn SQLAlchemy và kiểm tra database
├── models/              # SQLAlchemy models, mỗi bảng một file
├── schemas/             # Pydantic request/response models
├── providers/           # Adapter affiliate Shopee/mock/official
├── core/                # Config, security, logging, exception
├── db/                  # Engine, session và declarative base
└── scripts/             # Entrypoint cho admin và Telegram polling
```

Hướng phụ thuộc chính:

```text
Route → Controller → Service → Repository → Model/Database
```

Route không chứa câu SQL hoặc nghiệp vụ. Service không tạo HTTP response; controller
chịu trách nhiệm chuyển lỗi nghiệp vụ thành HTTP status.

## Chức năng

- Nhập một URL sản phẩm Shopee và tự lấy `shop_id`, `item_id`, tên, ảnh.
- Tạo URL affiliate bằng publisher ID đã cấu hình.
- Lưu hoặc cập nhật sản phẩm và affiliate link trong PostgreSQL.
- Liệt kê các cửa hàng và sản phẩm affiliate của từng cửa hàng.
- Xác thực JWT cho thao tác nhập sản phẩm.
- Nhận URL qua Telegram, gọi API catalog và phản hồi affiliate link.

Các chức năng Facebook, voucher, campaign, short link, click, conversion,
Celery và Redis không thuộc phạm vi dịch vụ này.

## API

| Method | Path | Mô tả | Quyền |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/token` | Đăng nhập, lấy access token | Public |
| `GET` | `/api/v1/auth/me` | Xem tài khoản hiện tại | Đã đăng nhập |
| `POST` | `/api/v1/affiliate-products` | Nhập/cập nhật sản phẩm từ URL Shopee | Admin |
| `GET` | `/api/v1/affiliate-shops` | Danh sách cửa hàng affiliate | Public |
| `GET` | `/api/v1/affiliate-shops/{shop_id}/products` | Sản phẩm của cửa hàng | Public |
| `GET` | `/api/v1/health/live` | Liveness | Public |
| `GET` | `/api/v1/health/ready` | PostgreSQL readiness | Public |
| `POST` | `/api/v1/telegram/webhook` | Nhận Telegram update | Telegram secret |

Swagger UI: <http://localhost:8000/docs>

## Migration database

Mỗi bảng có một migration riêng và chạy tuần tự:

1. `001_users.py` tạo bảng `users`.
2. `002_products.py` tạo bảng `products`.
3. `003_affiliate_links.py` tạo bảng `affiliate_links`.
4. `004_products_add_url.py` thêm URL gốc người dùng gửi vào `products.url`.

Revision hiện tại: `004 (head)`.

## Chạy bằng Docker

```bash
cp .env.example .env
docker compose build api
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose up -d api
docker compose exec api python -m app.scripts.create_admin
```

Container API cũng tự chạy `alembic upgrade head` trước khi khởi động để model và
schema không bị lệch khi deploy image mới.

Cấu hình bắt buộc để tạo affiliate link thật:

```dotenv
AFFILIATE_PROVIDER=shopee_redirect
AFFILIATE_PUBLISHER_ID=17334630385
```

## Ví dụ nhập sản phẩm

Đăng nhập:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=change-me'
```

Nhập sản phẩm:

```bash
curl -X POST http://localhost:8000/api/v1/affiliate-products \
  -H 'Authorization: Bearer ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://shopee.vn/product/1052042348/40551700226"}'
```

Metadata tên và ảnh được đọc từ Open Graph công khai của trang sản phẩm. Nếu Shopee
thay đổi hoặc chặn preview, API trả lỗi rõ ràng và không lưu bản ghi thiếu metadata.

## Telegram bot

Tạo token mới bằng BotFather rồi cấu hình trong `.env`. Không tái sử dụng token đã
từng xuất hiện trong log hoặc hội thoại.

```dotenv
CATALOG_API_BASE_URL=http://api:8000
TELEGRAM_BOT_TOKEN=TOKEN_MOI_TU_BOTFATHER
TELEGRAM_POLLING_TIMEOUT_SECONDS=30
```

Khởi động bot:

```bash
docker compose --profile telegram up -d --force-recreate telegram_bot
docker compose logs -f telegram_bot
```

Sau đó gửi một URL như `https://vn.shp.ee/cMvxmJNm` cho bot. Bot sẽ đăng nhập API
nội bộ, gọi `POST /api/v1/affiliate-products` và trả tên, Shop ID, Product ID cùng
affiliate link. Nếu dùng trong group, cần cấu hình Privacy Mode phù hợp trong
BotFather để bot nhìn thấy tin nhắn thông thường.

### Telegram webhook trên Render

Production không cần container polling. Cấu hình các biến sau trên Render:

```dotenv
APP_BASE_URL=https://TEN_SERVICE.onrender.com
CATALOG_API_BASE_URL=https://TEN_SERVICE.onrender.com
TELEGRAM_BOT_TOKEN=TOKEN_MOI_TU_BOTFATHER
TELEGRAM_WEBHOOK_ENABLED=true
TELEGRAM_WEBHOOK_SECRET=CHUOI_HEX_NGAU_NHIEN
```

Tạo secret bằng `openssl rand -hex 32`. Khi FastAPI khởi động, ứng dụng tự đăng
ký `POST /api/v1/telegram/webhook` với Telegram. Telegram gửi secret trong header
`X-Telegram-Bot-Api-Secret-Token`; request sai secret bị từ chối.

Trước khi bật webhook, dừng polling local vì polling gọi `deleteWebhook`:

```bash
docker compose --profile telegram stop telegram_bot
```

Kiểm tra trạng thái webhook mà không ghi token vào source:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

## Kiểm tra chất lượng

```bash
docker compose run --rm api ruff check .
docker compose run --rm api mypy app
docker compose run --rm -e APP_ENV=test api pytest -q
```

## Kết nối DBeaver

- Host: `localhost`
- Port: giá trị `POSTGRES_PORT` (mặc định `5432`)
- Database/User/Password: lấy từ `.env`
- Các bảng nghiệp vụ: `users`, `products`, `affiliate_links`
