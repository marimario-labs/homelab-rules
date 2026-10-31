# homelab-rules

家庭实验室（Homelab）统一路由分流与网络过滤规则集，支持 **Mihomo (Clash.Meta)**、**sing-box** 与 **Surge**。

源规则集中维护在 `src/`，通过 CI 自动清洗、去重、排序并转换为各客户端专用的文本与二进制规则集格式，发布至 `release` 分支，配合 jsDelivr CDN 免翻墙极速分发。

---

## 目录结构

```text
.
├── src/                          # 规则源文件（按分类维护）
│   ├── sniffer/                  # SNI 嗅探规则
│   │   ├── force-domain.list     # 强制嗅探名单（流媒体、特定平台）
│   │   └── skip-domain.list      # 嗅探绕过名单（米家 IoT、厂商推送、远程控制、国内媒体 CDN）
│   ├── dns/                      # DNS 解析规则
│   │   └── fakeip-filter.list    # Fake-IP 过滤名单（NTP、内网、穿透控制等排除域名）
│   └── routing/                  # 路由分流规则
│       ├── cloud-console.list    # 云厂商控制台（AWS / Cloudflare 控制台与 API）
│       ├── remote-control.list   # 远程桌面与控制服务（Tailscale, ToDesk, 向日葵, GameViewer 等）
│       ├── offshore-finance.list # 离岸金融（Wise, OCBC, iFast, HSBC Expat 等全球离岸与数字银行）
│       ├── us-finance.list       # 美国金融（Chase, BoA, Citi, Capital One, Schwab, Fidelity 等美国本土金融）
│       ├── ecommerce.list        # 跨境电商（Amazon, Shopify, eBay, Etsy, TikTok Shop 等平台与卖家后台）
│       ├── ads-allow.list        # 广告投放放行名单（Google Ads, Meta Business/Pixel, TikTok Ads 投放与转化追踪）
│       ├── landing-override.list # 强制住宅/落地出站名单
│       └── direct-override.list  # 强制直连出站名单
├── scripts/
│   └── build.py                  # 多格式转换与编译脚本
├── dist/                         # 导出产物（发布至 release 分支）
│   ├── surge/                    # Surge 格式 (.list)
│   ├── text/                     # Mihomo 纯文本格式 (.list)
│   ├── singbox/                  # sing-box 源码格式 (.json)
│   ├── mrs/                      # Mihomo 规则集二进制 (.mrs)
│   └── srs/                      # sing-box 规则集二进制 (.srs)
└── .github/workflows/
    └── build.yml                 # GitHub Actions 自动构建与发布流水线
```

---

## 客户端配置示例 (jsDelivr CDN)

发布产物镜像基准路径为：
`https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/<format>/<category>/<name>.<ext>`

### 1. Mihomo (Clash.Meta)

#### 推荐方式：MRS 二进制规则集 (`format: mrs`)
```yaml
rule-providers:
  fakeip-filter:
    type: http
    behavior: domain
    format: mrs
    path: ./rules/fakeip-filter.mrs
    url: "https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/mrs/dns/fakeip-filter.mrs"
    interval: 86400

  remote-control:
    type: http
    behavior: domain
    format: mrs
    path: ./rules/remote-control.mrs
    url: "https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/mrs/routing/remote-control.mrs"
    interval: 86400

rules:
  - RULE-SET,remote-control,DIRECT
```

#### 纯文本规则集 (`format: text`)
```yaml
rule-providers:
  force-domain:
    type: http
    behavior: domain
    format: text
    path: ./rules/force-domain.list
    url: "https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/text/sniffer/force-domain.list"
    interval: 86400
```

---

### 2. sing-box

#### 推荐方式：SRS 二进制规则集 (`format: binary`)
```json
{
  "route": {
    "rule_set": [
      {
        "tag": "remote-control",
        "type": "remote",
        "format": "binary",
        "url": "https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/srs/routing/remote-control.srs",
        "download_detour": "direct"
      },
      {
        "tag": "cloud-console",
        "type": "remote",
        "format": "binary",
        "url": "https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/srs/routing/cloud-console.srs",
        "download_detour": "direct"
      }
    ],
    "rules": [
      {
        "rule_set": "remote-control",
        "outbound": "direct"
      }
    ]
  }
}
```

#### JSON 源码规则集 (`format: source`)
```json
{
  "route": {
    "rule_set": [
      {
        "tag": "cloud-console",
        "type": "remote",
        "format": "source",
        "url": "https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/singbox/routing/cloud-console.json",
        "download_detour": "direct"
      }
    ]
  }
}
```

---

### 3. Surge

在 Surge 配置文件中的 `[Rule]` 区块引用：

```ini
[Rule]
# 远程运维直连
RULE-SET,https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/surge/routing/remote-control.list,DIRECT
# 云厂商控制台节点
RULE-SET,https://fastly.jsdelivr.net/gh/marimario-labs/homelab-rules@release/surge/routing/cloud-console.list,PROXY
```

---

## 规则链推荐优先级顺序 (Rule Precedence)

在各客户端（Mihomo, sing-box, Surge）配置完整分流规则时，各规则集推荐按以下顺序前置生效：

```text
1. direct-override       -> DIRECT                # 强制直连例外
2. landing-override      -> 住宅/固定落地          # 强制住宅/专用落地例外
3. ads-allow             -> 代理 / 白名单放行      # 必须置于通用 AdBlock (category-ads-all/REJECT) 之前
4. (广告拦截规则)        -> REJECT                # 可选：通用广告拦截
5. remote-control        -> DIRECT / 专线          # 远程桌面与运维穿透
6. cloud-console         -> 稳定代理              # 云厂商控制台（置于通用 CDN/S3 规则之前）
7. us-finance            -> 🇺🇸 美国落地           # 美国银行与券商（强风控，禁 urltest）
8. offshore-finance      -> 🇸🇬 狮城/欧洲落地      # 离岸与多币种金融
9. ecommerce             -> 住宅/专用落地          # 跨境电商卖家后台（必须置于通用 geosite-tiktok 之前）
10. (通用业务组)         -> 各对应策略组          # TikTok (消费端), Meta, Google, YouTube, Netflix 等
11. geosite-cn           -> DIRECT                # 国内域名直连
12. geoip-cn             -> DIRECT                # 国内 IP 直连
13. (兜底规则/FINAL)     -> 🚀 默认代理 / 漏网之鱼
```

---

## 规则编写规范 (Rule Syntax)

源文件集中在 `src/` 目录下，每行一条规则，语法规则由 `scripts/build.py` 自动化处理：

1. **根域名（Apex Domain）**：
   直接书写域名（如 `amazon.com`、`wise.com`）。构建脚本自动将其识别为根域名，并在各客户端编译为全子域匹配（Surge `DOMAIN-SUFFIX`、Mihomo `+.amazon.com`、sing-box `domain_suffix`）。
2. **精确子域名（Full Host）**：
   直接书写二级或多级域名（如 `console.aws.amazon.com`、`ads.google.com`）。构建脚本自动识别为非 Apex 域名，编译为完整主机名精确匹配（Surge `DOMAIN`、sing-box `domain`）。
3. **指定子域名及其下属所有子域**：
   使用 `+.` 前缀（如 `+.expat.hsbc.com`、`+.seller.tiktok.com`）。编译为该子域名及其所有更深层子域名的匹配，避免意外匹配顶级根域。
4. **IP 网段（CIDR）**：
   直接书写 IPv4 或 IPv6 CIDR（如 `192.168.1.0/24`、`10.0.0.0/8`），自动识别为 `IP-CIDR` 规则。

---

## 本地构建

无需任何额外依赖，只需 Python 3.8+ 即可生成 Surge、Mihomo Text 与 sing-box JSON：

```bash
python3 scripts/build.py
```

若本地 PATH 中安装了 `mihomo` 和 `sing-box` 二进制，脚本将自动编译生成 `.mrs` 和 `.srs` 二进制产物。若缺失上述命令，构建脚本会自动跳过二进制阶段并输出提示，不会中断。

---

## CI / CD 流程

每次向 `main` 分支提交或 PR 合并时，GitHub Actions 工作流将执行：
1. 接入 `marimario-labs/ci-shared` tree-reuse 门禁，合并 PR 时自动比对树状态并跳过无改动重复构建。
2. 自动拉取最新 `mihomo` 与 `sing-box` Linux 二进制。
3. 运行 `scripts/build.py` 完整编译所有规则。
4. 将编译好的 `dist/` 产物推送至 `release` 分支，实时刷新 jsDelivr 缓存。
