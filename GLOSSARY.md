# 术语表 (GLOSSARY)

本文档定义 `homelab-rules` 项目中的核心网络分流术语及规则集分类边界。

---

### 出站与策略组 (Outbounds & Policy Groups)

- **Landing Override（落地强制出站）**
  用于将高风控、强地域依赖的指定域名强制路由到特定的专属落地出口（如静态住宅 IP 或专用商用 VPS），优先级高于通用业务分流规则。
- **Direct Override（直连强制出站）**
  用于将误判为海外或需要严格走本地物理宽带的域名直接路由到 `DIRECT` 出站，不经过任何代理网络。
- **Residential Proxy / Static ISP（静态住宅代理）**
  由当地家庭宽带网络运营商（ISP）分配的静态公网 IP 地址。常用于跨境电商卖家后台与敏感金融网银，用于规避机房数据中心（IDC）IP 引发的高欺诈分判定与风控封禁。

---

### 规则分类与流量边界 (Rule Classification & Traffic Boundaries)

- **Cross-border E-Commerce（跨境电商）**
  专指面向海外市场的电商平台买家站、卖家中心（Seller Central）以及店铺运营 CDN。仅包含跨境平台，不收录中国大陆境内电商（如淘宝、京东、拼多多，后者默认走直连）。
- **Ad Console（广告投放控制台）**
  广告投放优化师用于管理广告账户、投放计划与预算的 Web 管理后台（如 Google Ads、Meta Business Suite、TikTok for Business）。
- **Pixel / Attribution Tracking（转化打点与归因追踪）**
  用于在独立站和落地页上报购买事件、转化数据与用户回传的跟踪代码（如 `connect.facebook.net`、`googleadservices.com`）。在开启通用广告拦截时，需要通过白名单放行，以保证投放归因调试不被中断。
- **Offshore Finance（离岸金融）**
  面向跨国用户或海外多币种账户的银行与金融科技（Fintech）服务（如 Wise、Revolut、新加坡华侨银行 OCBC、英属 iFast）。通常要求稳定、洁净的出口，但不强制要求走美国原生网络。
- **US Finance（美国金融）**
  受美国严格银行监管与信用审查体系约束的本土商业银行、大型券商与征信机构（如 Chase、Bank of America、Charles Schwab、Experian）。对 IP 属地具有极端严格的同地合规要求，通常必须固定走美国本土出口，且禁止在动态测速节点池中漂移。

---

### 匹配引擎与语法 (Rule Matching & Syntax)

- **Apex Domain（根域名）**
  不包含具体主机名前缀的注册域名（如 `amazon.com`、`wise.com`，以及 `amazon.co.uk` 这类两级公共后缀根域）。在规则编译时默认作为 `domain_suffix` 处理，匹配自身及所有深层子域名。
- **Subdomain Precedence（子域名优先匹配）**
  更具体的子域名规则排在通配根域或通用分类规则之前生效。例如：`seller.tiktok.com` 归入 `ecommerce` 并排在前面，优先走住宅出口；通配 `tiktok.com` 归入普通消费端规则并排在后面，走普通流媒体出口。
- **Fake-IP Filter / Real-Address List（真实地址解析名单）**
  在采用 Fake-IP 模式的透明代理网关中，必须排除在 Fake-IP 虚拟地址池之外、强制获取上游真实解析 IP 的域名集合。常见于 NTP 时间同步、STUN 网络打洞、系统网络连通性探测以及 P2P 远程桌面直连服务。
