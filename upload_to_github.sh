#!/bin/bash
# ============================================
# 해피테일즈 리뷰봇 GitHub 업로드 스크립트
# ============================================
#
# 사용법:
# 1. 새 GitHub 계정으로 레포 생성: happytails-reviewbot (Public)
# 2. 아래 변수에 본인 정보 입력
# 3. 이 스크립트 실행
#
# ============================================

# ▼▼▼ 여기에 본인 정보 입력 ▼▼▼
GITHUB_USER="여기에_깃헙_유저네임"
GITHUB_TOKEN="여기에_깃헙_토큰"
REPO_NAME="happytails-reviewbot"
# ▲▲▲

echo "=== 해피테일즈 리뷰봇 GitHub 업로드 ==="
echo ""

# 1. git 초기화
cd happytails-reviewbot
git init
git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_USER@users.noreply.github.com"

# 2. 파일 추가
git add -A
git commit -m "🎉 초기 업로드 - 리뷰봇 전체 파일 (v5)"

# 3. 리모트 추가 & 푸시
git remote add origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git branch -M main
git push -u origin main

echo ""
echo "=== 업로드 완료! ==="
echo ""
echo "레포 URL: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "=== 다음 단계 ==="
echo "1. 시스템 프롬프트에서 {GITHUB_USER}를 ${GITHUB_USER}로 바꾸세요"
echo "2. Claude 프로젝트에 prompts/system_prompt_v5.md 내용을 붙여넣기"
echo "3. 기존 프로젝트 knowledge 파일은 제거해도 됩니다"
