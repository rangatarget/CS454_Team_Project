#!/bin/bash

# 현재 디렉토리 설정
BASE_DIR=~/Lang

# BASE_DIR 내 coverage 저장 폴더 경로 기본 설정
COVERAGE_BASE_DIR=~/Lang

# 테스트 파일 경로 (여기에 테스트 케이스가 한 줄씩 저장되어 있음)
TEST_FILE="test_cases.txt"

# 테스트 파일 확인
if [ ! -f "$TEST_FILE" ]; then
    echo "Error: Test file '$TEST_FILE' not found."
    exit 1
fi

# 테스트 케이스 파일에서 한 줄씩 읽기
START_TEST=1
counter=1
while IFS= read -r TEST_CASE || [[ -n "$TEST_CASE" ]]; do
# while IFS= read -r TEST_CASE; do
    if [[ -z "$TEST_CASE" ]]; then
        continue  # 빈 줄 건너뛰기
    fi

    # 시작 번호보다 작으면 건너뛰기
    if [ "$counter" -lt "$START_TEST" ]; then
        counter=$((counter + 1))
        continue
    fi

    # 저장할 폴더 설정 (coverage_1t, coverage_2t, ...)
    COVERAGE_DIR="$COVERAGE_BASE_DIR/coverage_${counter}t"


    # 새로운 'coverage' 폴더 만들기
    mkdir -p "$COVERAGE_DIR"

    # 테스트 케이스에서 lang3과 lang 확인
    if [[ "$TEST_CASE" == *".lang3."* ]]; then
        TESTCASE_BELOW_40="$TEST_CASE"
        TESTCASE_ABOVE_40=$(echo "$TEST_CASE" | sed 's/\.lang3\./.lang./')
    elif [[ "$TEST_CASE" == *".lang."* ]]; then
        TESTCASE_BELOW_40=$(echo "$TEST_CASE" | sed 's/\.lang\./.lang3./')
        TESTCASE_ABOVE_40="$TEST_CASE"
    else
        echo "Error: The provided test case does not contain 'lang3' or 'lang'."
        exit 1
    fi

    echo "Processing test case: $TEST_CASE"
    echo "  Results will be saved in: $COVERAGE_DIR"

    # BASE_DIR 내 모든 폴더 순회
    for folder in "$BASE_DIR"/*; do
        if [ -d "$folder" ]; then
            # 폴더 이름 추출 (절대 경로 제외)
            folder_name=$(basename "$folder")
            
            # 숫자만 추출 (예: "1b" -> "1")
            folder_number=$(echo "$folder_name" | grep -oE '^[0-9]+')

            if [ -z "$folder_number" ]; then
                continue
            fi
        
            # 해당 폴더로 이동
            cd "$folder" || continue
        
            # defects4j coverage 실행 (숫자에 따라 다른 테스트 실행)
            if [ "$folder_number" -lt 40 ]; then
                echo "  Running coverage in $folder_name for test $counter: $TESTCASE_BELOW_40"
                defects4j coverage -t "$TESTCASE_BELOW_40"
            else
                echo "  Running coverage in $folder_name for test $counter: $TESTCASE_ABOVE_40"
                defects4j coverage -t "$TESTCASE_ABOVE_40"
            fi
        
            # 결과 파일이 존재하는지 확인
            if [ -f "coverage.xml" ]; then
                # 파일 이름을 폴더 이름 기반으로 변경
                new_name="coverage_${folder_name}.xml"
                mv coverage.xml "$COVERAGE_DIR/$new_name"
            fi

            # failing_tests 파일 처리
            if [ -f "failing_tests" ]; then
                new_name="failing_tests_${folder_name}"
                mv failing_tests "$COVERAGE_DIR/$new_name"
            fi
        fi
    done

    # 다음 테스트 케이스로 이동
    counter=$((counter + 1))
done < "$TEST_FILE"

echo "All test cases processed."