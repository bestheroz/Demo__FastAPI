#!/bin/bash

# Poetry 업데이트 가능한 패키지를 pyproject.toml에 자동 반영하는 스크립트

set -e

echo "📦 업데이트 가능한 패키지 확인 중..."

# poetry show -o 실행하여 업데이트 가능한 패키지 목록 가져오기
outdated_packages=$(poetry show -o)

if [ -z "$outdated_packages" ]; then
    echo "✅ 모든 패키지가 최신 버전입니다."
    exit 0
fi

echo ""
echo "🔍 발견된 업데이트 가능한 패키지:"
echo "$outdated_packages"
echo ""

# 각 패키지를 순회하며 업데이트
while IFS= read -r line; do
    # 빈 줄 건너뛰기
    if [ -z "$line" ]; then
        continue
    fi

    # 패키지명, 현재 버전, 최신 버전 파싱
    package_name=$(echo "$line" | awk '{print $1}')
    current_version=$(echo "$line" | awk '{print $2}')
    latest_version=$(echo "$line" | awk '{print $3}')

    if [ -n "$package_name" ] && [ -n "$latest_version" ]; then
        echo "⬆️  $package_name: $current_version -> $latest_version"

        # pyproject.toml에서 해당 패키지 버전 업데이트
        # macOS의 sed는 -i 옵션에 백업 확장자가 필요
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/\"$package_name (==$current_version)\"/\"$package_name (==$latest_version)\"/" pyproject.toml
            sed -i '' "s/$package_name = \"$current_version\"/$package_name = \"$latest_version\"/" pyproject.toml
        else
            sed -i "s/\"$package_name (==$current_version)\"/\"$package_name (==$latest_version)\"/" pyproject.toml
            sed -i "s/$package_name = \"$current_version\"/$package_name = \"$latest_version\"/" pyproject.toml
        fi
    fi
done <<< "$outdated_packages"

echo ""
echo "✅ pyproject.toml 업데이트 완료"
echo ""
echo "📝 변경사항 확인:"
git diff pyproject.toml

echo ""
echo "🔄 Poetry lock 파일 업데이트 중..."
poetry lock --no-update

echo ""
echo "📦 패키지 설치 중..."
poetry install

echo ""
echo "✨ 모든 업데이트가 완료되었습니다!"
