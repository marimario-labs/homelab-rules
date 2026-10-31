# 0002: E-commerce subdomain precedence over consumer TikTok

Status: accepted, 2026-10-30

## Context

Cross-border sellers operate stores on TikTok Shop across regions (US, UK, Southeast Asia). Store operations require clean, static residential IP addresses to avoid risk control account suspension. At the same time, network clients also consume regular TikTok short videos and live streams, which tolerate dynamic proxy pool rotation and non-residential proxies.

## Decision

`src/routing/ecommerce.list` matches only seller portals, partner consoles, and shop APIs (`seller*.tiktok.com`, `tiktokshop.com`, `partner.tiktokshop.com`). It does not match the apex domain `tiktok.com`.

In routing rule order, `ecommerce` is evaluated before the consumer TikTok rule set (`geosite-tiktok`):
- Seller and shop traffic matches `ecommerce` first and routes through dedicated residential or landing nodes.
- Consumer video and live stream traffic bypasses `ecommerce` and falls through to the downstream consumer TikTok policy group.

## Considered options

- **Including `tiktok.com` in `ecommerce.list`**: Pulls all daily video and streaming traffic into high-cost or bandwidth-limited residential proxy nodes.
- **Relying on `geosite-tiktok` for all TikTok traffic**: Exposes TikTok Shop seller portals to rotating proxy pools and dirty datacenter IPs, causing merchant account suspension.

## Consequences

- Shop management and video consumption are completely decoupled at the network layer.
- Consumer traffic does not consume static residential proxy bandwidth.
