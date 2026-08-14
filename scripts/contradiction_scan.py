#!/usr/bin/env python3
"""
contradiction_scan.py — 技能仓库矛盾点扫描

检测仓库内部自相矛盾的地方：断链、重复标题、数字对账失败、术语漂移。
跨文件语义级"规则冲突"仍需人工，本脚本只标记可疑信号。

用法:
    python3 contradiction_scan.py --repo <path> [--json] [--strict]

退出码:
    0  无 fail（--strict 下也无 warn）
    1  存在 fail；或 --strict 且存在 warn
    2  参数/路径错误
"""
import argparse
import json
import os
import re
import sys

MD_RE = re.compile(r"\.md$")
LINK_RE = re.compile(r"\]\(((?:references|scripts|assets)/[^)]+)\)")
REF_RE = re.compile(r"(?:references|scripts|assets)/[A-Za-z0-9_./-]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$", re.MULTILINE)
NUMERIC_RE = re.compile(r"(\d+)\s*(?:个)?\s*(子技能|references|篇\s*references|脚本|assets|个子技能)")
# 规范词 → 同义写法（扫描非规范写法作为术语漂移信号）
TERM_MAP = {
    "Level A": [r"\bA\s*级\b", r"\bA级\b", r"\bLv\s*A\b"],
    "Level B": [r"\bB\s*级\b", r"\bB级\b", r"\bLv\s*B\b"],
    "能力索引": [r"路由表"],
    "参考手册": [r"playbook", r"Playbook"],
}


def iter_md(repo):
    for root, _, files in os.walk(repo):
        if ".git" in root:
            continue
        for f in files:
            if MD_RE.search(f):
                yield os.path.join(root, f)


def scan(repo):
    findings = []
    rel = lambda p: os.path.relpath(p, repo)

    # 1. 断链
    for p in iter_md(repo):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        for m in set(LINK_RE.findall(txt) + REF_RE.findall(txt)):
            if not os.path.exists(os.path.join(repo, m)):
                findings.append({"type": "broken_link", "file": rel(p), "detail": f"引用不存在: {m}", "severity": "fail"})

    # 2. 重复标题（同文件内）
    for p in iter_md(repo):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        seen = {}
        for m in HEADING_RE.finditer(txt):
            h = m.group(2).strip()
            if h in seen:
                findings.append({"type": "duplicate_heading", "file": rel(p), "detail": f"重复标题: '{h}'", "severity": "warn"})
            seen[h] = True

    # 3. 数字对账（README/SKILL.md 声称数 vs 实际目录数）
    def count_dir(layer):
        d = os.path.join(repo, layer)
        if not os.path.isdir(d):
            return 0
        return len([x for x in os.listdir(d) if not x.startswith(".")])

    actual = {
        "子技能": count_dir("skills"),
        "references": count_dir("references"),
        "脚本": count_dir("scripts"),
        "assets": count_dir("assets"),
    }
    for p in iter_md(repo):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        for m in NUMERIC_RE.finditer(txt):
            claimed = int(m.group(1))
            label = m.group(2).replace(" ", "")
            key = {"子技能": "子技能", "references": "references", "篇references": "references",
                   "脚本": "脚本", "assets": "assets", "个子技能": "子技能"}.get(label)
            if key and actual.get(key) is not None and claimed != actual[key]:
                findings.append({"type": "numeric_mismatch", "file": rel(p),
                                 "detail": f"声称 {claimed} 个{key}，实际目录 {actual[key]} 个", "severity": "fail"})

    # 4. 术语漂移
    for p in iter_md(repo):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        for canon, pats in TERM_MAP.items():
            for pat in pats:
                if re.search(pat, txt):
                    findings.append({"type": "term_drift", "file": rel(p),
                                     "detail": f"非规范写法命中（建议统一为 '{canon}'）: /{pat}/", "severity": "warn"})
                    break

    return findings


def main():
    ap = argparse.ArgumentParser(description="技能仓库矛盾点扫描")
    ap.add_argument("--repo", default=".", help="仓库路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--strict", action="store_true", help="有 warn 也退出 1")
    args = ap.parse_args()

    repo = os.path.abspath(os.path.expanduser(args.repo))
    if not os.path.isdir(repo):
        print(f"[ERROR] 仓库不存在: {repo}", file=sys.stderr)
        return 2

    findings = scan(repo)
    n_fail = sum(f["severity"] == "fail" for f in findings)
    n_warn = sum(f["severity"] == "warn" for f in findings)

    if args.json:
        print(json.dumps({"repo": repo, "summary": {"fail": n_fail, "warn": n_warn},
                          "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(f"== contradiction_scan: {os.path.basename(repo)} ==")
        if not findings:
            print("  无 findings")
        for f in findings:
            mark = "FAIL" if f["severity"] == "fail" else "WARN"
            print(f"  [{mark}] {f['type']} @{f['file']} — {f['detail']}")
        print(f"-- 汇总: fail={n_fail} warn={n_warn}")

    if n_fail > 0:
        return 1
    if args.strict and n_warn > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
