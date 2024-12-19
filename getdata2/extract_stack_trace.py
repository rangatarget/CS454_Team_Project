import os
import numpy as np

if __name__ == "__main__":
    print("=" * 80)

    # importing bug id
    modified_file_per_bug = {}
    with open('modified_class.txt', 'r') as modified:
        lines = [line.strip() for line in modified.readlines()]
        for line in lines:
            bug_id, modified_class = int(line.split(',')[0]), line.split(',')[1].strip('"')
            modified_file_per_bug[bug_id] = modified_class


    test_case_path = 'test_cases.txt'
    with open(test_case_path, 'r') as file:
        lines = [line.strip() for line in file.readlines()]
    
    total_test_case = len(lines)
    max_bug_id = 66 # 프로젝트마다 직접 수정

    output_dir = "./stack_traces"
    os.makedirs(output_dir, exist_ok=True)

    for bug_id in range(1, max_bug_id + 1):

        # skip non-existing bugs
        if not os.path.exists(f"./{bug_id}b"):
            continue

        print(f"Processing {bug_id}b")

        # extract stack traces
        extracted_stack_traces = []

        for test_case in range(total_test_case):

            input_dir = f"./coverage_{test_case + 1}t"
            failing_file = os.path.join(input_dir, f"failing_tests_{bug_id}b")

            with open(failing_file, 'r') as failing:
                stack_traces = [line.strip() for line in failing.readlines()]

            if len(stack_traces) == 0:
                continue

            if "No tests found" in stack_traces[1] or "not found" in stack_traces[1] or "ClassNotFound" in stack_traces[1]:
                continue
            
            pos = modified_file_per_bug[bug_id].rfind('/')
            identifier = modified_file_per_bug[bug_id][:pos] # extract the package name
            print(f"Identifier: {identifier}")
            # identifier = "org.apache.commons.lang" # include "org.apache.commons.lang3"
            for org_line in stack_traces[1:]:
                if identifier in org_line and not "test" in org_line and not "Test" in org_line:
                    line = org_line.split(" ")[1].strip()
                    line = line.split("(")[0].strip()
                    line_number = org_line.split(":")[-1]
                    line_number = line_number.split(")")[0].strip()
                    line = line + "::" + line_number
                    extracted_stack_traces.append(line)

            extracted_stack_traces.append("\n")

        # save the stack traces
        output_file = os.path.join(output_dir, f"stack_trace_{bug_id}.txt")
        with open(output_file, 'w') as out:
            for line in extracted_stack_traces:
                if not line == "\n":
                    line = line.replace(".", "/") # replace . with /
                    last_index = line.rfind('/')
                    line = line[:last_index] + "::" + line[last_index + 1:] # replace last / with ::
                    out.write(f"{line}\n")
                else:
                    out.write("\n")
        # np.save(output_file, extracted_stack_traces)
        print(f"Stack trace has been saved to {output_file}")
        
        print("=" * 80)