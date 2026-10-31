# 0003: Unified offshore finance rule set without regional splitting

Status: accepted, 2026-10-30

## Context

Homelab users maintain accounts across international multi-currency fintechs (Wise, Revolut) as well as offshore banking accounts in Singapore (OCBC), the United Kingdom (iFast, HSBC Expat), and Hong Kong (ZA Bank, Mox). Downstream templates (such as Rovan in `docs/template-parameters.md`) define two financial policy groups: `🏦 离岸金融` and `🗽 美国金融`.

## Decision

Maintain a single, unified `offshore-finance.list` for non-US international finance and fintech services, and keep it separate from `us-finance.list`. Do not split `offshore-finance` into multiple regional lists (e.g. SG, UK, HK, EU).

- `us-finance.list` remains dedicated to US retail banking, credit unions, and brokerages due to strict US territorial IP verification and automated account closure risks.
- `offshore-finance.list` routes through a neutral, stable overseas outbound (e.g. Singapore landing, UK landing, or dedicated proxy). Multi-currency fintechs and international banks accept non-domestic logins as long as the exit IP remains stable and clean.
- Any bank with strict single-region enforcement (such as Hong Kong virtual banks requiring HK IPs) is handled via a targeted entry in `src/routing/landing-override.list`.

## Considered options

- **Splitting `offshore-finance` by region (SG, UK, HK, EU)**: Causes policy group bloat in downstream clients (Rovan, Nikki, Surge), adding 3-4 extra policy groups, and violates the template contract established in Rovan issue #68.
- **Merging `us-finance` into `offshore-finance`**: US banks (Chase, BoA, Citi, Capital One) have zero tolerance for non-US IP access and datacenter proxy hops, making an isolated US landing policy group mandatory.

## Consequences

- Downstream clients configure and maintain only two financial policy groups.
- Policy configuration stays manageable while preserving accounts from risk-control triggers.
