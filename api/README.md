# Affiliate Products API (Express)

CRUD API for affiliate products backed by Supabase.

## Endpoints

- `GET /api/products`
  - returns `{ items: Product[] }`

- `GET /api/products/:id`
  - returns `Product`

- `POST /api/products`
  - body: `{ name, image, description, affiliateUrl, category?, categoryId? }`

- `PUT /api/products/:id`
  - body: `{ name, image, description, affiliateUrl, category?, categoryId? }`

- `DELETE /api/products/:id`
  - returns `204` if deleted

- `POST /api/clicks`
  - body: `{ productId, affiliateUrl, referrer?, utm_source?, utm_medium?, utm_campaign?, utm_term?, utm_content? }`
  - inserts a click record into `affiliate_clicks`

## Run

```bash
cd api
npm install
npm start
```

API listens on `http://localhost:3001` by default.

