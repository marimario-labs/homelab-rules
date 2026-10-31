# 0004: Ad allowlist serves as exception whitelist for ad blocking

Status: accepted, 2026-10-30

## Context

Homelab gateway deployments commonly enable DNS-level or rule-level ad blocking (e.g. `category-ads-all`, AdGuard Home, anti-AD, or sing-box/Clash reject rules). When operators manage ad accounts (Google Ads, Meta Business Suite, TikTok Ads) or test conversion pixels on landing pages, aggressive ad-blocking filters break dashboards and silently swallow attribution events.

## Decision

`src/routing/ads-allow.list` is maintained solely as an exception whitelist to be placed before ad-blocking `REJECT` rules, or as the negative condition in a logical AND filter.

- `ads-allow.list` includes campaign management portals (`ads.google.com`, `business.facebook.com`) and essential conversion tracking endpoints (`connect.facebook.net`, `googleadservices.com`, `bat.bing.com`).
- `homelab-rules` does not build or maintain an ad-blocking blocklist. Ad blocking relies on upstream geodata (`category-ads-all.srs` or community blocklists).

## Considered options

- **Maintaining an ad-blocking blocklist in this repository**: Upstream projects (SagerNet, AdRules, OISD) maintain tens of thousands of ad and telemetry domains with automated scrapers. Duplicating that effort in this repository creates unnecessary maintenance overhead.
- **Routing ad portals directly without an allowlist**: If ad blocking is evaluated earlier in the rule chain, requests to `googleadservices.com` or pixel endpoints are rejected before reaching routing evaluation.

## Consequences

- In client configurations, `ads-allow` must precede generic ad-blocking reject rules.
- Ad campaigns and pixel attribution debug sessions function without disabling network-wide ad blocking.
