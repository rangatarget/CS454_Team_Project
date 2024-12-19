#!/bin/bash

# 결과를 저장할 파일
output_file="changed_lines.txt"

# 기존 결과 파일이 있다면 삭제
if [ -f "$output_file" ]; then
    rm "$output_file"
fi

# 1부터 65까지 반복
for i in {1..65}; do
    # 첫 번째 경로에서 diff 명령어 실행
    diff_output=$(diff -r "/home/dlgudwls/CS454/javaprojects/lang_${i}_buggy/src/main" "/home/dlgudwls/CS454/javaprojects/lang_${i}_fixed/src/main" 2>/dev/null)

    # 첫 번째 경로에서 diff 결과가 비어있지 않거나 오류가 발생한 경우 대체 경로로 시도
    if [ -z "$diff_output" ]; then
        diff_output=$(diff -r "/home/dlgudwls/CS454/javaprojects/lang_${i}_buggy/src/java" "/home/dlgudwls/CS454/javaprojects/lang_${i}_fixed/src/java" 2>/dev/null)
    fi

    # diff 결과가 비어있지 않은 경우
    if [ ! -z "$diff_output" ]; then
        # 변경된 파일 이름과 줄 번호를 추출하여 결과 파일에 저장
        echo "Changes in lang_${i}:" >> "$output_file"

        # - , < , >로 시작하는 줄을 제외하고 결과를 저장
        echo "$diff_output" | grep -v '^[<>-]' >> "$output_file"

        echo "" >> "$output_file"  # 구분을 위한 빈 줄 추가
    fi
done

echo "Diff results saved to $output_file"
