const express = require('express');
const { createClient } = require('@supabase/supabase-js');

// dotenv is optional (but recommended)
try {
    require('dotenv').config();
} catch (e) {
    // ignore
}

const app = express();
app.use(express.json());

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY || !SUPABASE_SERVICE_ROLE_KEY) {
    console.warn(
        'Missing Supabase env vars. Set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY in api/.env'
    );
}

// Admin client is used for writes (bypasses RLS via service role)
const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false },
});

// Anon client is used for reads
const supabaseAnon = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: { persistSession: false },
});

function productRowToApi(p) {
    return {
        id: p.id,
        name: p.name,
        image: p.image_url,
        description: p.description,
        affiliateUrl: p.affiliate_link,
        category: p.category,
        categoryId: p.category_id,
        createdAt: p.created_at,
        updatedAt: p.updated_at,
    };
}

function apiToProductUpsert(body) {
    const {
        name,
        image,
        description,
        affiliateUrl,
        category,
        categoryId,
    } = body || {};

    return {
        name,
        image_url: image,
        description,
        affiliate_link: affiliateUrl,
        category,
        category_id: categoryId,
    };
}

// ---------- PRODUCTS CRUD ----------
app.get('/api/products', async(req, res) => {
    try {
        const { data, error } = await supabaseAnon
            .from('affiliate_products')
            .select(
                'id,name,category_id,category,image_url,affiliate_link,description,created_at,updated_at'
            )
            .order('created_at', { ascending: false });

        if (error) throw error;
        res.json({ items: (data || []).map(productRowToApi) });
    } catch (err) {
        res.status(500).json({ error: err.message || 'Failed to fetch products' });
    }
});

app.get('/api/products/:id', async(req, res) => {
    try {
        const { data, error } = await supabaseAnon
            .from('affiliate_products')
            .select(
                'id,name,category_id,category,image_url,affiliate_link,description,created_at,updated_at'
            )
            .eq('id', req.params.id)
            .single();

        if (error) return res.status(404).json({ error: 'Product not found' });

        res.json(productRowToApi(data));
    } catch (err) {
        res.status(500).json({ error: err.message || 'Failed to fetch product' });
    }
});

app.post('/api/products', async(req, res) => {
    try {
        const body = req.body || {};
        const required = ['name', 'image', 'description', 'affiliateUrl'];
        for (const k of required) {
            if (!body[k]) {
                return res.status(400).json({ error: `Missing required fields: ${required.join(', ')}` });
            }
        }

        const upsert = apiToProductUpsert(body);

        const { data, error } = await supabaseAdmin
            .from('affiliate_products')
            .insert(upsert)
            .select(
                'id,name,category_id,category,image_url,affiliate_link,description,created_at,updated_at'
            )
            .single();

        if (error) throw error;
        res.status(201).json(productRowToApi(data));
    } catch (err) {
        res.status(500).json({ error: err.message || 'Failed to create product' });
    }
});

app.put('/api/products/:id', async(req, res) => {
    try {
        const body = req.body || {};
        const required = ['name', 'image', 'description', 'affiliateUrl'];
        for (const k of required) {
            if (!body[k]) {
                return res.status(400).json({ error: `Missing required fields: ${required.join(', ')}` });
            }
        }

        const upsert = apiToProductUpsert(body);

        const { data, error } = await supabaseAdmin
            .from('affiliate_products')
            .update(upsert)
            .eq('id', req.params.id)
            .select(
                'id,name,category_id,category,image_url,affiliate_link,description,created_at,updated_at'
            )
            .single();

        if (error) return res.status(404).json({ error: 'Product not found' });

        res.json(productRowToApi(data));
    } catch (err) {
        res.status(500).json({ error: err.message || 'Failed to update product' });
    }
});

app.delete('/api/products/:id', async(req, res) => {
    try {
        const { error } = await supabaseAdmin
            .from('affiliate_products')
            .delete()
            .eq('id', req.params.id);

        if (error) return res.status(404).json({ error: 'Product not found' });

        res.status(204).send();
    } catch (err) {
        res.status(500).json({ error: err.message || 'Failed to delete product' });
    }
});

// ---------- CLICK TRACKING ----------
// Frontend should call this BEFORE opening affiliate link.
// Body:
// { productId, affiliateUrl, referrer?, utm_source?, utm_medium?, utm_campaign?, utm_term?, utm_content? }
app.post('/api/clicks', async(req, res) => {
    try {
        const {
            productId,
            affiliateUrl,
            referrer,
            utm_source,
            utm_medium,
            utm_campaign,
            utm_term,
            utm_content,
        } = req.body || {};

        if (!productId || !affiliateUrl) {
            return res.status(400).json({ error: 'Missing productId or affiliateUrl' });
        }

        const ip = req.ip;
        const userAgent = req.headers['user-agent'];

        const insertRow = {
            product_id: productId,
            affiliate_url: affiliateUrl,
            referrer: referrer || req.headers.referer || null,
            utm_source: utm_source || null,
            utm_medium: utm_medium || null,
            utm_campaign: utm_campaign || null,
            utm_term: utm_term || null,
            utm_content: utm_content || null,
            ip: ip || null,
            user_agent: userAgent || null,
        };

        const { error } = await supabaseAdmin.from('affiliate_clicks').insert(insertRow);
        if (error) throw error;

        res.json({ ok: true });
    } catch (err) {
        res.status(500).json({ error: err.message || 'Failed to record click' });
    }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`Affiliate Products API listening on http://localhost:${PORT}`);
});