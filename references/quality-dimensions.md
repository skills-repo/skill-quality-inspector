# 质量维度与门禁对照（quality-dimensions）

> 把 `rules/quality-gates.md` 的抽象门禁翻译成一份"拿起来就能勾"的质检清单。脚本能查的归脚本，脚本查不了的归人工。

## 一、门禁 → 检查动作映射

| 门禁 | 查什么 | 怎么查 | 归谁 |
|------|--------|--------|------|
| Q1 Frontmatter 完整 | `name`/`description`/`metadata` 非空 | `quality_audit.py` 解析 frontmatter | 脚本 |
| Q2 技能名唯一 | 同仓 `name` 不重复 | 扫描 `skills/*/SKILL.md` | 脚本 |
| Q3 目录一致 | 子技能 `name` == 目录名 | 比对 | 脚本 |
| Q4 安装命令格式 | README 含 `npx skills add ...@<name>` | 正则 | 脚本 |
| Q5 来源标记 | 子技能 `source.type/repo/path` 完整 | 解析 | 脚本 |
| Q6 架构合规 | `audit_architecture.py --strict` 退出 0 | 架构脚本 | 脚本 |
| Q7 路由层完整 | 根 SKILL.md ≤150 行、无 TODO、`architecture: superpower` | grep + awk | 脚本 |
| Q8 路径稳定 | 既有 `skills/<name>/` 未被删/改名 | `git diff --name-status` | 脚本 |
| Q9 双安装命令 | README 含整库 + 单技能两种 | 正则 | 脚本 |
| Q10 注册表同步 | `registry/repos.json` 字段与实况一致 | 比对 | 人工 |
| W1 README 一致 | 清单表含全部 skills | 比对 | 脚本 |
| W2 中文内容 | 正文中文为主 | 采样 | 人工 |
| W6 references 增量 | 含决策/坑/清单而非复制 | 抽样读 | 人工 |
| W7 脚本可运行 | `scripts/*.py --help` 正常 | 遍历 | 脚本 |

## 二、脚本能查 vs 必须人工

**脚本已覆盖（确定性）**：frontmatter、命名、路由索引、安装命令、行数/TODO、双安装、README 清单、脚本 `--help`、跨文件数字对账（`quality_audit.py` + `contradiction_scan.py`）。

**必须人工（需判断）**：
- Q1 的 `description` 是否"具体、非废话"——脚本只查非空，不查信息量。
- W6 references 是否有增量信息——脚本无法判断是否"只是子技能复制"。
- W2 中文语境——技术术语保留英文是合理的，脚本容易误报。
- Q10 registry 同步——需对照 `registry/repos.json` 实况逐字段核对。

## 三、质检清单（提交前逐条过）

- [ ] `quality_audit.py --repo <r> --strict` 退出 0（无 fail）
- [ ] `audit_architecture.py --repo <r> --strict` 退出 0
- [ ] `audit_readme_gates.py --repo <r> --strict` 退出 0
- [ ] `contradiction_scan.py --repo <r>` findings 无阻断项
- [ ] 人工抽读 2 篇 references 确认有增量（W6）
- [ ] `registry/repos.json` 的 skills/architecture/updated 与实况一致（Q10）
- [ ] 下游 `skills-lock.json` 引用的路径仍有效（Q8）

## 四、常见坑

- **只看架构分不看内容门禁**：`audit_architecture.py` 只审结构，100 分也可能 Q4/Q9/W1 全挂（D32 实证）。
- **账实不符**：registry 基数滞后，永远以实时扫描为准再写，别在旧数上 +1（见 redundancy 与质量巡检历史事故）。
- **误报当 bug**：W2 中文检查对"技术术语保留英文"会误报，按上下文放行而非硬改。
