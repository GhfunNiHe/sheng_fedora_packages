#!/bin/bash

# --- 配置 ---
# 如果您想操作的仓库不是当前目录下的仓库，
# 请取消下面这行的注释，并替换为您的仓库地址，例如："owner/repo"
# REPO="OWNER/REPO"

# --- 脚本开始 ---

# 函数：打印错误信息并退出
function print_error() {
  echo "错误: $1" >&2
  exit 1
}

# 检查 gh 命令是否存在
if ! command -v gh &> /dev/null; then
  print_error "GitHub CLI (gh) 未安装。请访问 https://cli.github.com/ 安装。"
fi

# 检查 git 命令是否存在
if ! command -v git &> /dev/null; then
  print_error "Git 未安装。"
fi

# 检查 gh 是否已通过身份验证
if ! gh auth status &> /dev/null; then
  print_error "您尚未使用 'gh auth login' 登录 GitHub CLI。"
fi

echo "将要删除仓库中所有的 release 和 tag。"
echo -n "请再次确认是否继续 (y/n)? "
read answer
if [ "$answer" != "${answer#[Yy]}" ] ;then
    echo "操作继续..."
else
    echo "操作已取消。"
    exit 0
fi

# 如果指定了 REPO 变量，则在 gh 命令中使用 -R 参数
REPO_FLAG=""
if [ -n "$REPO" ]; then
  REPO_FLAG="--repo $REPO"
  echo "目标仓库: $REPO"
fi

# --- 第一步：删除所有 Release 及其关联的 Tag ---
echo "正在获取所有 release 列表..."
RELEASES=$(gh release list $REPO_FLAG --limit 5000 | awk -F '\t' '{print $3}')

if [ -z "$RELEASES" ]; then
  echo "未找到任何 release。"
else
  echo "开始删除所有 release 及其关联的 tag..."
  echo "$RELEASES" | while read -r tag; do
    if [ -n "$tag" ]; then
      echo "正在删除 release 和 tag: $tag"
      gh release delete "$tag" $REPO_FLAG --cleanup-tag --yes || echo "删除 release '$tag' 失败，可能已被删除。"
    fi
  done
  echo "所有 release 删除完毕。"
fi

# --- 第二步：删除所有剩余的远程 Tag ---
echo "正在获取所有远程 tag 列表..."
REMOTE_TAGS=$(git ls-remote --tags origin | awk '{print $2}' | sed 's/refs\/tags\///')

if [ -z "$REMOTE_TAGS" ]; then
  echo "未找到任何剩余的远程 tag。"
else
  echo "开始删除所有剩余的远程 tag..."
  echo "$REMOTE_TAGS" | while read -r tag; do
    if [ -n "$tag" ]; then
      echo "正在删除远程 tag: $tag"
      git push --delete origin "$tag" || echo "删除远程 tag '$tag' 失败，可能已被删除。"
    fi
  done
  echo "所有远程 tag 删除完毕。"
fi

# --- 第三步：删除所有本地 Tag ---
echo "正在获取所有本地 tag 列表..."
LOCAL_TAGS=$(git tag)

if [ -z "$LOCAL_TAGS" ]; then
  echo "未找到任何本地 tag。"
else
  echo "开始删除所有本地 tag..."
  git tag -d $LOCAL_TAGS
  echo "所有本地 tag 删除完毕。"
fi

echo "所有操作完成！"