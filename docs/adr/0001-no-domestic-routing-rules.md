# 0001: Do not maintain domestic (CN) routing rules

Status: accepted, 2026-10-30

## Context

Downstream routing clients (Mihomo, sing-box, Surge) route traffic to distinct outbounds (DIRECT, PROXY, or dedicated landing nodes). Many domestic services (such as Taobao, JD, OceanEngine, Tencent Ads) require direct outbound connections to preserve domestic CDN acceleration, prevent captcha challenges, and avoid abnormal login risk controls.

## Decision

`homelab-rules` strictly maintains only non-domestic and cross-border routing rules. No mainland China domestic platforms or services are maintained as dedicated routing lists in this repository.

- Domestic routing traffic is delegated to upstream base sets (`geosite-cn`, `geoip-cn`) or default direct routing rules in client configurations.
- All service routing lists in `src/routing/` (e.g. `ecommerce`, `ads-allow`, `offshore-finance`, `us-finance`) are assumed to route via proxy or dedicated overseas landing outbounds.
- If a domestic service or domain is misclassified as non-domestic by upstream rule sets, it must be explicitly corrected via `src/routing/direct-override.list`.

## Considered options

- **Maintaining dedicated CN lists (`ecommerce-cn.list`, `ads-cn.list`)**: Duplicates upstream `geosite-cn` maintenance work, creates drift across repositories, and adds unnecessary rule sets.
- **Mixing domestic and non-domestic domains in the same category list**: Breaks client policy group assignment, where a rule set maps to a single outbound action (e.g. `RULE-SET,ecommerce,Residential-Proxy` would drag domestic shopping traffic into overseas residential proxies).

## Consequences

- Rule sets remain clean and action-aligned.
- Domestic services will not accidentally be proxied through overseas nodes.
