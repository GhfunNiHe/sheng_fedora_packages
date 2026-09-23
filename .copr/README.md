# Copr 构建

`copr` 分支是构建分支：往它推送 spec 改动，只会重建受影响的包，按依赖顺序跑在
[Copr](https://copr.fedorainfracloud.org/) 上。`main` 继续用 `build-sheng-rpms.yml`，
本地 `rpmbuild` 构建全部包。

## 工作方式

`.github/workflows/copr-build.yml` 先挑出要构建的包，然后对每个包执行：

    copr-cli buildscm <project> --clone-url <repo> --commit <sha> --type git \
        --subdir <pkg> --spec <pkg>.spec --method make_srpm

Copr 的 `make_srpm` 方式把 SRPM 生成交回给我们，所以 `.copr/make-srpm.sh` 干的正是
CI 里那套手工步骤：

- 下载 spec 里声明的 `SourceN`/`PatchN` URL；
- 收集仓库内的本地源（`extra-sm8550.config`、`scripts/mkbootimg`、`libssc`/`hexagonrpc`
  的补丁、udev 规则等）；
- 用 `alsa-xiaomi-sheng`、`sheng-sensors`、`sheng-fedora-configs` 的 `etc/`、`usr/`
  树现场打出 payload tarball；
- 对着这个源码目录跑 `rpmbuild -bs`。

因为这些都发生在 Copr 侧，spec 文件一个字都不用改：从普通 checkout 直接 `rpmbuild -ba`
照旧可用。

构建是逐个提交并等待结果的，因为 Copr 是从项目自己的仓库解析 `BuildRequires` 的：
`fastrpc`、`libssc` 必须先构建出来，`iio-sensor-proxy`、`xiaomi-sheng-thp`、
`xiaomi-sheng-keyboard-helper`、`hexagonrpc` 才能构建。`kernel-sm8550` 单独一个 job：
没有包依赖它，它的 `%prep` 要联网（`git ls-remote`），而且它是最慢的一个。

## 构建跑在哪

构建在 Copr 那边执行，workflow 只负责提交任务。两边对照：

| | Copr（`copr` 分支） | Actions（`ubuntu-24.04-arm`） |
| --- | --- | --- |
| 构建机 | 共享 aarch64 builder，磁盘 140 GB；核数见构建日志里的 `-j<N>` | `ubuntu-24.04-arm`：4 vCPU / 16 GB |
| 构建环境 | 无状态 mock chroot（`fedora-44-aarch64`） | `fedora:latest` 容器 + 本地 `rpmbuild -ba` |
| ccache | 没有，Copr builder 不跨构建保留 | 用 `actions/cache` 缓存 |
| 时间上限 | 项目默认 5 小时，Fedora 实例最高 50 小时；内核 job 申请 6 小时 | job 上限 6 小时 |
| 内核冷构建 | 与 4 vCPU runner 同量级，约一小时 | 约一小时 |

chroot 列表和超时上限属于项目设置；workflow 只覆盖超时和网络开关，而且只对内核覆盖——
这两项必须和项目默认值不同。

Copr 有更快的构建机（支持 aarch64，约 8 倍，磁盘 280 GB），但要走 issue 申请，官方口径是
"普通机上预计超过约 2 小时"才值得申请。先看第一次内核构建的 `-j<N>` 和实际耗时再决定。

## 一次性配置

1. 建项目（默认名 `sheng_fedora_packages`，可用 repository variable `COPR_PROJECT`
   覆盖），只开 aarch64 chroot，并打开构建期网络：

       copr-cli create sheng_fedora_packages --chroot fedora-44-aarch64 \
           --enable-net on \
           --description "Fedora packages for the Xiaomi Pad 6S Pro (sheng)"

   只开 aarch64 就够：所有编译包都是 `ExclusiveArch: aarch64`，多开一个 chroot 只会让
   noarch 那几个包白建一遍。以后要改可以用
   `copr-cli modify sheng_fedora_packages --chroot ...`。

2. 把项目的构建超时调高。Copr 默认 5 小时，内核 job 申请 6 小时（`--timeout 21600`）。

3. 在 <https://copr.fedorainfracloud.org/api/> 建一个 API token。Copr 给的配置块长这样——
   workflow 会把同样的内容写进 runner 上的 `~/.config/copr`，值取自仓库 secret：

       [copr-cli]
       login = <API login>
       username = <Copr username>
       token = <API token>
       copr_url = https://copr.fedorainfracloud.org

   把四个值存成 repository secret：

   | Secret | 值 |
   | --- | --- |
   | `COPR_LOGIN` | API login |
   | `COPR_USERNAME` | Copr 用户名 |
   | `COPR_TOKEN` | API token |
   | `COPR_API_URL` | 可选，默认 `https://copr.fedorainfracloud.org` |

4. 推送 `copr` 分支（本地已经有这个分支和 workflow）：

       git push -u origin copr

   第一次推送会构建全部包，之后的推送只构建改动过的。`workflow_dispatch` 可以传一个
   空格分隔的包目录列表，留空表示构建全部。

## 备注

- `sheng-sensors` 打包的是高通 sensor 配置 blob，`xiaomi-sheng-firmware` 打包的是厂商固件，
  两者的再分发条款都不符合 Copr 的服务条款。想把这两个排除在 Copr 之外，把 repository
  variable `SKIP_PACKAGES` 设为 `sheng-sensors xiaomi-sheng-firmware` 即可，它们继续留在
  GitHub release 里。
- Copr builder 是无状态的，每次构建都是冷构建（ccache 也一样）：内核耗时和 4 vCPU 的
  Actions runner 差不多（约 1 小时），但重复构建不会变快。
- `COPR_STUB_SOURCES=1 .copr/make-srpm.sh <spec> <outdir>` 会用占位文件代替下载，适合在
  不拉内核 tarball 的情况下检查打包逻辑。
