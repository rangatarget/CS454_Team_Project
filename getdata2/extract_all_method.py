import xml.etree.ElementTree as ET
import os

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
        method_line = method.find('lines').find('line').attrib['number'] - 1
        method_name = f"{method_name}::{method_line}"
        # print(method_name, end=' -> ')
        if method.attrib['name'] not in not_welcome:
            all_methods.append(method_name)
            if float(method.attrib['line-rate']):
                covered_methods.append(method_name)
                # print('covered')
            else:
                # print('not covered')
                pass
        else:
            # print('not welcome')
            pass

    return all_methods, covered_methods

def save_method_names(method_names, output_file):
    with open(output_file, 'w') as f:
        for name in method_names:
            f.write(f"{name}\n")

if __name__ == "__main__":
    print("=" * 80)

    input_dir = "./coverage"
    all_output_dir = "all_methods"
    os.makedirs(all_output_dir, exist_ok=True)
    covered_output_dir = "covered_methods"
    os.makedirs(covered_output_dir, exist_ok=True)
    
    index = 1
    while True:
        coverage_file = os.path.join(input_dir, f"coverage_{index}b.xml")
        if not os.path.exists(coverage_file):
            continue

        all_output_file = os.path.join(all_output_dir, f'all_method_names_{index}.txt')
        covered_output_file = os.path.join(covered_output_dir, f'covered_method_names_{index}.txt')
    
        # extract all and covered methods
        all_methods, covered_methods = extract_method_names(coverage_file)
        print("=" * 80)
        save_method_names(all_methods, all_output_file)
        print(f"All method names have been exported to {all_output_file}")
        save_method_names(covered_methods, covered_output_file)
        print(f"Covered method names have been exported to {covered_output_file}")

        index += 1

        if index > 70:
            break
    
    print("=" * 80)
