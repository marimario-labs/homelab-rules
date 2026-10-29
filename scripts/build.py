#!/usr/bin/env python3
"""
homelab-rules builder
Generates routing rule-sets for Surge (.list), Mihomo (text & .mrs), and sing-box (.json & .srs).
"""

import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

COMMON_TWO_PART_TLDS = {
    "com.cn", "net.cn", "org.cn", "gov.cn", "edu.cn",
    "co.uk", "org.uk", "me.uk", "ltd.uk", "plc.uk",
    "co.jp", "ne.jp", "or.jp", "ac.jp", "go.jp",
    "com.hk", "org.hk", "net.hk", "edu.hk", "gov.hk", "idv.hk",
    "com.tw", "org.tw", "net.tw", "idv.tw",
    "com.au", "net.au", "org.au",
}


def is_apex_domain(domain: str) -> bool:
    """Check if domain is a registered root/apex domain (e.g. example.com, example.com.cn)."""
    parts = domain.lower().split(".")
    if len(parts) <= 2:
        return True
    last_two = f"{parts[-2]}.{parts[-1]}"
    if last_two in COMMON_TWO_PART_TLDS and len(parts) == 3:
        return True
    return False


def is_ip_or_cidr(entry: str) -> bool:
    """Check if entry is a valid IPv4/IPv6 address or CIDR network."""
    try:
        ipaddress.ip_network(entry, strict=False)
        return True
    except ValueError:
        return False


def classify_entry(raw_line: str):
    """
    Parse and classify a single rule line.
    Returns (rule_type, cleaned_value)
    rule_type: 'cidr' | 'wildcard' | 'suffix' | 'full'
    """
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None, None

    # Classical Surge/Mihomo prefixes
    if line.startswith("IP-CIDR,"):
        parts = line.split(",")
        return "cidr", parts[1].strip()
    if line.startswith("DOMAIN-SUFFIX,"):
        return "suffix", line.split(",", 1)[1].strip()
    if line.startswith("DOMAIN,"):
        return "full", line.split(",", 1)[1].strip()
    if line.startswith("DOMAIN-KEYWORD,"):
        return "wildcard", line.split(",", 1)[1].strip()
    if line.startswith("DOMAIN-WILDCARD,"):
        return "wildcard", line.split(",", 1)[1].strip()

    # Domain syntax prefixes
    if line.startswith("+."):
        return "suffix", line[2:].strip().lower()
    if line.startswith("."):
        return "suffix", line[1:].strip().lower()
    if line.startswith("full:"):
        return "full", line[5:].strip().lower()

    # CIDR network or IP
    if is_ip_or_cidr(line):
        return "cidr", line

    # Wildcard domain
    if "*" in line:
        return "wildcard", line.lower()

    # Plain domain: check if apex (suffix) or FQDN host (full)
    domain = line.lower()
    if is_apex_domain(domain):
        return "suffix", domain
    return "full", domain


def parse_source_file(file_path: Path):
    """Read and parse all rules in a source file with deduplication and sorting."""
    cidrs = set()
    suffixes = set()
    full_domains = set()
    wildcards = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            rule_type, val = classify_entry(raw_line)
            if not rule_type:
                continue
            if rule_type == "cidr":
                cidrs.add(val)
            elif rule_type == "suffix":
                suffixes.add(val)
            elif rule_type == "full":
                full_domains.add(val)
            elif rule_type == "wildcard":
                wildcards.add(val)

    return {
        "cidr": sorted(cidrs),
        "suffix": sorted(suffixes),
        "full": sorted(full_domains),
        "wildcard": sorted(wildcards),
    }


def generate_surge(parsed, out_path: Path, category: str, name: str):
    """Generate Surge format rule list."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Profile: {name} ({category})",
        f"# Source: https://github.com/marimario-labs/homelab-rules",
    ]
    count = sum(len(v) for v in parsed.values())
    lines.append(f"# Total: {count}")
    lines.append("")

    for item in parsed["suffix"]:
        lines.append(f"DOMAIN-SUFFIX,{item}")
    for item in parsed["full"]:
        lines.append(f"DOMAIN,{item}")
    for item in parsed["wildcard"]:
        lines.append(f"DOMAIN-WILDCARD,{item}")
    for item in parsed["cidr"]:
        lines.append(f"IP-CIDR,{item},no-resolve")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_mihomo_text(parsed, out_path: Path, category: str, name: str):
    """Generate Mihomo plain text format rule list."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Profile: {name} ({category})",
        f"# Source: https://github.com/marimario-labs/homelab-rules",
    ]
    count = sum(len(v) for v in parsed.values())
    lines.append(f"# Total: {count}")
    lines.append("")

    for item in parsed["suffix"]:
        lines.append(f"+.{item}")
    for item in parsed["full"]:
        lines.append(item)
    for item in parsed["wildcard"]:
        lines.append(item)
    for item in parsed["cidr"]:
        lines.append(item)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_singbox_json(parsed, out_path: Path):
    """Generate sing-box rule-set source JSON (version 2)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rule_obj = {}

    if parsed["full"]:
        rule_obj["domain"] = parsed["full"]
    if parsed["suffix"]:
        rule_obj["domain_suffix"] = parsed["suffix"]
    if parsed["wildcard"]:
        regexes = [
            f"^{re.escape(item).replace(r'\*', '.*')}$" for item in parsed["wildcard"]
        ]
        rule_obj["domain_regex"] = sorted(regexes)
    if parsed["cidr"]:
        rule_obj["ip_cidr"] = parsed["cidr"]

    payload = {
        "version": 2,
        "rules": [rule_obj] if rule_obj else [],
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def compile_mrs(text_path: Path, mrs_path: Path, has_cidr: bool, has_domain: bool):
    """Compile Mihomo MRS binary using mihomo convert-ruleset."""
    if not shutil.which("mihomo"):
        return False

    behavior = "ipcidr" if (has_cidr and not has_domain) else "domain"
    mrs_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["mihomo", "convert-ruleset", behavior, "text", str(text_path), str(mrs_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to compile MRS for {text_path}: {e.stderr.strip()}", file=sys.stderr)
        return False


def compile_srs(json_path: Path, srs_path: Path):
    """Compile sing-box SRS binary using sing-box rule-set compile."""
    if not shutil.which("sing-box"):
        return False

    srs_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to compile SRS for {json_path}: {e.stderr.strip()}", file=sys.stderr)
        return False


def main():
    root_dir = Path(__file__).resolve().parent.parent
    src_dir = root_dir / "src"
    dist_dir = root_dir / "dist"

    has_mihomo = bool(shutil.which("mihomo"))
    has_singbox = bool(shutil.which("sing-box"))

    print(f"Starting build from {src_dir}")
    print(f"Tools detected - mihomo: {has_mihomo}, sing-box: {has_singbox}")

    list_files = sorted(src_dir.glob("*/*.list"))
    if not list_files:
        print("No .list files found in src/", file=sys.stderr)
        sys.exit(1)

    built_counts = {"surge": 0, "text": 0, "singbox": 0, "mrs": 0, "srs": 0}

    for src_file in list_files:
        category = src_file.parent.name
        name = src_file.stem
        rel_path = f"{category}/{name}"

        parsed = parse_source_file(src_file)
        rule_count = sum(len(v) for v in parsed.values())

        # 1. Surge list
        surge_path = dist_dir / "surge" / category / f"{name}.list"
        generate_surge(parsed, surge_path, category, name)
        built_counts["surge"] += 1

        # 2. Mihomo text list
        text_path = dist_dir / "text" / category / f"{name}.list"
        generate_mihomo_text(parsed, text_path, category, name)
        built_counts["text"] += 1

        # 3. sing-box JSON
        json_path = dist_dir / "singbox" / category / f"{name}.json"
        generate_singbox_json(parsed, json_path)
        built_counts["singbox"] += 1

        has_domain = bool(parsed["suffix"] or parsed["full"] or parsed["wildcard"])
        has_cidr = bool(parsed["cidr"])

        # 4. Mihomo MRS
        if has_mihomo and rule_count > 0:
            mrs_path = dist_dir / "mrs" / category / f"{name}.mrs"
            if compile_mrs(text_path, mrs_path, has_cidr=has_cidr, has_domain=has_domain):
                built_counts["mrs"] += 1

        # 5. sing-box SRS
        if has_singbox and rule_count > 0:
            srs_path = dist_dir / "srs" / category / f"{name}.srs"
            if compile_srs(json_path, srs_path):
                built_counts["srs"] += 1

        print(f"Built {rel_path} ({rule_count} rules)")

    print("\nBuild summary:")
    for fmt, count in built_counts.items():
        print(f"  {fmt.upper()}: {count} files generated")


if __name__ == "__main__":
    main()
