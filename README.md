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
│       ├── offshore-finance.list # 离岸金融（Wise 等，v1 预留）
│       ├── us-finance.list       # 美国金融银行（v1 预留）
│       ├── ecommerce.list        # 跨境电商（Amazon/Shopify 等，v1 预留）
│       ├── ads-allow.list        # 广告投放管理放行名单（Google/Meta Ads，v1 预留）
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
