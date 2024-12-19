import xml.etree.ElementTree as ET
import os
import numpy as np
import torch

def extract_method_names(coverage_file):
    not_welcome = ['<init>', '<clinit>']

    tree = ET.parse(coverage_file)
    coverage = tree.getroot()

    packages_list = coverage.findall('packages')
    methods_list = []
    classes_list = []

    for packages in packages_list:
        package_list = packages.findall('package')  # 각 packages의 모든 package
        for package in package_list:
            classes = package.find('classes')  # 각 package의 classes
            if classes is None:
                continue  # classes가 없는 경우 건너뜀
            for class_element in classes:
                class_name = class_element.attrib['name']
                classes_list.append(class_name)
                methods = class_element.find('methods')  # 각 클래스의 methods
                if methods is None:
                    continue  # methods가 없는 경우 건너뜀
                for method in methods:
                    methods_list.append([class_name, method])

    all_methods = []
    covered_methods = []

    for class_name, method in methods_list:
        method_name = method.attrib['name']
        method_name = f"{class_name}::{method_name}"
        method_line = method.find('lines').find('line')
        if method_line is not None:
            method_line = int(method_line.attrib['number']) # 주석 없으면 -1, 주석 있으먄 그만큼 더 -
            method_name = f"{method_name}::{str(method_line)}"
            if method.attrib['name'] not in not_welcome \
            and "$" not in method.attrib['name'] \
            and "$" not in class_name: # removing synthetic methods (accessing nested class)
                all_methods.append(method_name)
                if float(method.attrib['line-rate']):
                    covered_methods.append(method_name)

    return all_methods, covered_methods

def save_method_names(method_names, output_file):
    with open(output_file, 'w') as f:
        for name in method_names:
            name = name.replace(".", "/") # replace . with /
            f.write(f"{name}\n")

if __name__ == "__main__":
    print("=" * 80)

    test_case_path = 'test_cases.txt'
    with open(test_case_path, 'r') as file:
        lines = [line.strip() for line in file.readlines()]
    
    total_test_case = len(lines)
    max_bug_id = 66 # 프로젝트마다 직접 수정
    check_bug_id = 1 # 프로젝트마다 직접 수정
    check_test_case = 1 # 프로젝트마다 직접 수정

    all_output_dir = "all_methods"
    os.makedirs(all_output_dir, exist_ok=True)

    covered_output_dir = "covered_methods"
    os.makedirs(covered_output_dir, exist_ok=True)

    for bug_id in range(1, max_bug_id + 1):

        if not os.path.exists(f"./{bug_id}b"): # skip non-existing bugs
            continue

        print(f"Processing {bug_id}b")

        # initialize coverage matrix for each bug
        all_methods = []
        input_dir = f"./coverage_1t"
        coverage_file = os.path.join(input_dir, f"coverage_{bug_id}b.xml")
        all_methods, _ = extract_method_names(coverage_file)
        coverage_matrix = np.zeros((len(all_methods), total_test_case * 2), dtype=np.int8)

        for test_case in range(total_test_case):

            input_dir = f"./coverage_{test_case + 1}t"
            coverage_file = os.path.join(input_dir, f"coverage_{bug_id}b.xml")
        
            # extract all and covered methods
            all_methods, covered_methods = extract_method_names(coverage_file)
            all_methods = sorted(all_methods, key = lambda x: int(x.split("::")[-1])) # sort by line number
            covered_methods = sorted(covered_methods, key = lambda x: int(x.split("::")[-1])) # sort by line number

            # (optional) save all and covered method names for a specific test case
            # if test_case + 1 == check_test_case and bug_id == check_bug_id:
            all_output_file = os.path.join(all_output_dir, f'all_method_names_{bug_id}.txt')
            covered_output_file = os.path.join(covered_output_dir, f'covered_method_names_{bug_id}.txt')
            save_method_names(all_methods, all_output_file)
            save_method_names(covered_methods, covered_output_file)
            print(f"All method names have been exported to {all_output_file}")
            print(f"Covered method names have been exported to {covered_output_file}")

            # fill the coverage information
            for i, method in enumerate(all_methods):
                if method in covered_methods:
                    coverage_matrix[i, test_case] = 1

            # fill the passing/failing information
            failing_file = os.path.join(input_dir, f"failing_tests_{bug_id}b")
            with open(failing_file, 'r') as f:
                stack_traces = f.read().strip()
            if not stack_traces:
                coverage_matrix[:, test_case + total_test_case] = 1
            else:
                if "No tests found" in stack_traces or "not found" in stack_traces or "ClassNotFound" in stack_traces:
                    coverage_matrix[:, test_case + total_test_case] = 1
                else:
                    coverage_matrix[:, test_case + total_test_case] = 0

        # save the coverage matrix

        # coverage_output_dir = "./coverage_matrices"
        # os.makedirs(coverage_output_dir, exist_ok=True)

        # output_file = os.path.join(coverage_output_dir, f"coverage_matrix_{bug_id}.npy")
        # np.save(output_file, coverage_matrix)

        coverage_output_dir = "./coverage_matrices_torch"
        os.makedirs(coverage_output_dir, exist_ok=True)

        output_file = os.path.join(coverage_output_dir, f"coverage_matrix_{bug_id}.pt")
        torch.save(coverage_matrix, output_file)

        print(f"Coverage matrix has been saved to {output_file}")
        
        print("=" * 80)
