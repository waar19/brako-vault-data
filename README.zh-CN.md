# Brako Vault 离线泄漏密码数据

[English](README.md) | [Español](README.es.md) | [Português](README.pt.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [日本語](README.ja.md) | **[简体中文](README.zh-CN.md)**

本 **公开** 仓库包含 [Brako Vault](https://github.com/waar19/brako-vault-releases)
用来**在没有网络连接的情况下**检测泄漏密码的 Bloom 过滤器
(`.blf`)。每个过滤器都派生自 Have I Been Pwned 维护的公开
Pwned Passwords 语料库,并以 release 的形式发布,供 Brako Vault
的构建流水线 (CI) 下载,或由用户手动导入。

## 为什么需要单独的、公开的仓库?

Brako Vault 的 APK **从不声明 `INTERNET` 权限**(请参阅
[waar19/brako-vault-releases](https://github.com/waar19/brako-vault-releases/blob/master/SECURITY.md)
中的 `SECURITY.md`)。这意味着数据必须**放在 APK 内部**,或者
由用户从文件手动导入。

此外,完整的 Pwned Passwords 语料库重达数十 GB。生成过滤器
需要具有充足内存和时间的 runner。GitHub 上的 **公开** 仓库在
标准 runner 上享有 **免费且无限** 的 Actions 分钟数,而私有
仓库则会计入所有者的套餐。出于以上原因,本仓库是公开且自包含
的。

## 仓库内容

- **`tools/leaked-password-filter/`** — Python 3 生成器。
  `build_filter.py` 将语料库的 `HASH:COUNT` 输出转换为 `.blf`。
  `download_and_build.py` 以流式方式下载 Pwned Passwords 官方
  SHA-1 范围(不将完整语料库写入磁盘)并并行构建过滤器。
  `test_build_filter.py` 验证格式。`measure_fpr.py` 测量经验
  误报率。
- **`.github/workflows/build-data.yml`** — 手动工作流
  (`workflow_dispatch`),在 GitHub Actions runner 上运行生成器
  并将工件发布为 release。

## 归属与许可

本仓库中的泄漏密码过滤器是 Pwned Passwords 语料库的 Bloom filter
派生形式。Pwned Passwords 由 Have I Been Pwned 创建并维护,后者
是 Troy Hunt 运营的一项服务。

- **Pwned Passwords 服务**: <https://haveibeenpwned.com/Passwords>
- **运营者**: Troy Hunt — <https://www.troyhunt.com>
- **服务**: Have I Been Pwned — <https://haveibeenpwned.com>
- **构建时使用的公开 API**:
  `https://api.pwnedpasswords.com/range/{prefix}` — 参见
  <https://haveibeenpwned.com/API/v3#PwnedPasswords>
- **官方下载器参考**:
  <https://github.com/HaveIBeenPwned/PwnedPasswordsDownloader>

Pwned Passwords API **不附带任何许可或归属要求**。Have I Been
Pwned 的官方文档原文如此表述: *"In order to help maximise
adoption, there is no licencing or attribution requirements on
the Pwned Passwords API, although it is welcomed if you would
like to include it."*(请参阅
<https://haveibeenpwned.com/API/v3#PwnedPasswords>)。
HIBP 的 breach 和 paste API 分别采用 CC BY 4.0 许可,但
**该许可不适用于 Pwned Passwords**,本仓库也不使用那些
端点。

Brako Vault 加入本归属章节是为了让数据来源清楚可查,不是因为
它被要求。如果您再分发本仓库中的 `.blf` 文件,请保留本节
原样。

### 本仓库包含什么 — 不包含什么

- Pwned Passwords 语料库本身: **不包含**。本仓库仅包含由
  SHA-1 哈希派生的 Bloom filter。
- 明文密码: **不包含**。只包含 Bloom 过滤器的位。
- **构建时** 与 HIBP 的网络通信: **存在**。
  `download_and_build.py` 向
  `api.pwnedpasswords.com/range/{prefix}` 发起 GET 请求,
  以流式方式下载 SHA-1 范围。脚本不将语料库写入本地;它
  处理每个范围,保留前 N 个哈希的堆,丢弃其余部分。
- **Brako Vault 应用的运行时** 与 HIBP 的网络通信:
  **不存在**。APK 不声明 `INTERNET` 权限。

## `.blf` 格式

每个 `.blf` 文件都是对泄漏密码的 SHA-1 进行 Bloom 过滤的结果。
**它不包含明文密码**,只包含过滤器的位。客户端应用:

1. 计算候选密码的 `SHA-1`。
2. 对这 20 字节应用 SHA-256,推导出两个 64 位 lane 索引
   (Kirsch-Mitzenmacher 双哈希方案)。
3. 在 `.blf` 中检查对应的位。

过滤器的阳性结果表示"该密码**可能**已泄漏";应用会将其标记。
过滤器的尺寸使得经验误报率保持在万分之一或更低
(由 `measure_fpr.py` 校准和测量)。

## Release

每次工作流成功执行,会发布一个 release,标签为
`leaked-passwords-YYYY-MM-DD-N`(执行者提供的语料库标签 +
运行序号),包含以下资源:

| 文件 | 大致大小 | 用途 |
|---|---|---|
| `brako-vault-leaked-passwords-base-1m.blf` | 约 2-3 MB | 嵌入 APK。覆盖最常见的 100 万条泄漏密码。 |
| `brako-vault-leaked-passwords-base-1m.blf.sha256` | 约 100 B | 基础库的 SHA-256 校验和,用于独立验证和 CI 验证。 |
| `brako-vault-leaked-passwords-10m.blf` | 约 20-30 MB | 可选的 1000 万条数据包。**不**随 APK 一起分发;用户从 GitHub Releases 下载并在设置中选择。 |
| `brako-vault-leaked-passwords-10m.blf.sha256` | 约 100 B | 数据包的 SHA-256 校验和,用于独立验证和 CI 验证。应用导入时不读取此 sidecar。 |

## 应用如何使用这些数据

### 100 万条基础库(嵌入 APK)

[Brako Vault](https://github.com/waar19/brako-vault-releases) 的
私有发布工作流从本仓库下载 `.blf` 文件,并在编译或发布前将每个
文件与其 `.sha256` sidecar 核对。它还会在编译前将
`brako-vault-leaked-passwords-base-1m.blf` 放入
`androidApp/src/main/assets/leaked-passwords/base.blf`。如果
任一校验和不匹配,构建会失败。

### 1000 万条数据包(手动导入)

用户从本仓库的 GitHub Releases 页面下载
`brako-vault-leaked-passwords-10m.blf`,然后在应用内打开
**设置 → 泄漏密码数据库 → 导入扩展**,并在系统文件选择器
(SAF)中选择下载的 `.blf`。应用导入时不读取 `.sha256`
sidecar;它会在激活扩展库之前,验证 `.blf` 头部所存储的文件
正文内部 SHA-256 摘要。sidecar 仍可用于独立验证,CI 也会使用
它。如果内部摘要不匹配,扩展库不会被激活。

## 如何生成新的 release

1. 转到本仓库的 **Actions** 选项卡。
2. 选择工作流 **"Build offline breach database"**。
3. 点击 **Run workflow** 并填写:
   - `corpus_date`: 由执行者提供的 `YYYY-MM-DD` 标签,用于描述
     该次执行期间从 Pwned Passwords 实时 API 查询的数据。它
     不会选择或固定语料库快照。
   - `base_limit`: 嵌入基础库中可配置的哈希数量
     (默认 `1000000`)。
   - `expansion_limit`: 扩展中可配置的哈希数量
     (默认 `10000000`)。
   正式 release 必须恰好使用 `1000000` 和 `10000000`,因为
   `base-1m` 与 `10m` 文件名以及应用都依赖这些数量。输入值
   可以配置,本身并不保证使用这些正式数值。
4. 等待。生成可能需要 1-2 小时(由于仓库是公开的,所以免费)。
   日志显示每个 SHA-1 范围的进度。
5. 完成后,release 出现在 **Releases** 选项卡中,包含 4 个资源。

有关生成器的技术细节(Kirsch-Mitzenmacher 方案、Content-MD5
验证、基于堆的 top-N 选取、bootstrap 模式),请参阅
[`tools/leaked-password-filter/README.md`](tools/leaked-password-filter/README.md)。

## 本地验证

如果您不想等待工作流而想先试用生成器:

```bash
git clone https://github.com/waar19/brako-vault-data.git
cd brako-vault-data
python -m unittest discover -s tools/leaked-password-filter -p "test_*.py"
```

测试使用一个小的合成语料库,不需要网络,并验证 `.blf` 格式
和生成器 API。

## 隐私

本仓库不包含任何个人数据。它只包含由公开的泄漏密码 SHA-1 哈希
派生的 Bloom 过滤器位。不存储任何 Brako Vault 用户数据、email
地址、breach 内容或明文密码。
