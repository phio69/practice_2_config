import argparse
import sys
import ssl
import json
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Инструмент визуализации зависимости пакетов NuGet")
    parser.add_argument("--package", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo-url", required=True, help="URL репозитория или путь к тестовому файлу")
    parser.add_argument("--version", required=True, help="Версия пакета")
    parser.add_argument("--output", default="graph.svg", help="Имя файла для сохранения графа")
    parser.add_argument("--test-mode", action="store_true", help="Режим тестирования с графом из букв (A, B, C...)")
    return parser.parse_args()

#Загрузка .nuspec файла из NUGet API
def fetch_nuspec(package, version):
    url = f"https://api.nuget.org/v3-flatcontainer/{package.lower()}/{version}/{package.lower()}.nuspec"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urlopen(url, context=ctx) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"Ошибка загрузки .nuspec: {e}", file=sys.stderr)
        sys.exit(1)

#Извлечение прямых зависимостей из .nuspec файла
def extract_dependencies_from_nuspec(xml_content):
    root = ET.fromstring(xml_content)
    ns = {"ns": "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"}
    deps = []
    for dep in root.findall(".//ns:dependency", ns):
        name = dep.get("id")
        version = dep.get("version", "*")
        if name:
            deps.append((name, version))
    return deps

#Загрузка тестового файла из json
def load_test_graph(filepath):
    if not os.path.isfile(filepath):
        print(f"Ошибка: файл '{filepath}' не найден.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения тестового файла: {e}", file=sys.stderr)
        sys.exit(1)


#Получение прямых зависимостей
def get_direct_dependencies(package, version, is_test_mode, source):
    if is_test_mode:
        test_graph = load_test_graph(source)
        return test_graph.get(package, [])
    else:
        xml = fetch_nuspec(package, version)
        deps = extract_dependencies_from_nuspec(xml)
        return [name for name, _ in deps]


#Рекурсивный DFS для построения графа
def dfs_recursive(current, version_map, is_test_mode, source, visited, recursion_stack, full_graph, cycles):
    if current in recursion_stack:
        cycle = list(recursion_stack) + [current]
        cycles.append(cycle)
        return
    if current in visited:
        return

    visited.add(current)
    recursion_stack.add(current)

    direct_deps = get_direct_dependencies(current, version_map.get(current, "latest"), is_test_mode, source)
    full_graph[current] = direct_deps

    #Рекурсивный обход для тестового режима
    if is_test_mode:
        for dep in direct_deps:
            if dep not in version_map:
                version_map[dep] = "latest"
            dfs_recursive(dep, version_map, is_test_mode, source, visited, recursion_stack, full_graph, cycles)
    else:
        #nuspec в пользовательском
        pass

    recursion_stack.remove(current)


#Построение обратного графа зависимостей
def build_reverse_graph(forward_graph):
    reverse_graph = {}
    for pkg, deps in forward_graph.items():
        for dep in deps:
            if dep not in reverse_graph:
                reverse_graph[dep] = []
            reverse_graph[dep].append(pkg)
    return reverse_graph


#Сбор обратных зависимостей с использованием DFS
def collect_reverse_deps(target, reverse_graph, visited, result):
    if target in visited:
        return
    visited.add(target)
    for parent in reverse_graph.get(target, []):
        if parent not in result:
            result.append(parent)
        collect_reverse_deps(parent, reverse_graph, visited, result)

def generate_mermaid_code(graph):
    lines = ["graph TD"]
    for pkg, deps in graph.items():
        if deps:
            for dep in deps:
                lines.append(f'    {pkg} --> {dep}')
        else:
            lines.append(f'    {pkg}')
    return "\n".join(lines)


def main():
    config = parse_args()

    print("Конфигурация:")
    for k, v in vars(config).items():
        print(f"    {k}: {v}")
    print()

    #Построение полного графа для всех пакетов в тестовом режиме
    if config.test_mode:
        test_graph = load_test_graph(config.repo_url)
        #Строим полный граф: для каждого пакета в test_graph
        full_graph = {}
        for pkg in test_graph.keys():
            full_graph[pkg] = test_graph[pkg]
    else:
        #В реальном режиме — строим граф только от корневого пакета
        version_map = {config.package: config.version}
        visited = set()
        recursion_stack = set()
        full_graph = {}
        cycles = []

        dfs_recursive(
            config.package,
            version_map,
            config.test_mode,
            config.repo_url,
            visited,
            recursion_stack,
            full_graph,
            cycles
        )

    print("Полный граф зависимостей:")
    for pkg, deps in full_graph.items():
        if deps:
            print(f"  {pkg} → {', '.join(deps)}")
        else:
            print(f"  {pkg} → (нет зависимостей)")

    print("\nЭтап 4: Обратные зависимости")
    reverse_graph = build_reverse_graph(full_graph)
    reverse_deps = []
    collect_reverse_deps(config.package, reverse_graph, set(), reverse_deps)

    if reverse_deps:
        print(f"Пакеты, которые зависят от '{config.package}':")
        for pkg in reverse_deps:
            print(f"  - {pkg}")
    else:
        print(f"Нет пакетов, которые зависят от '{config.package}'.")

    #Генерация кода для 5 этапа
    mermaid_code = generate_mermaid_code(full_graph)
    output_file = config.output
    if output_file.endswith(".svg"):
        mmd_file = output_file.replace(".svg", ".mmd")
    else:
        mmd_file = output_file + ".mmd"

    try:
        with open(mmd_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        print(f"\nMermaid-код сохранён в файл: {mmd_file}")
        print("Чтобы получить SVG:")
        print("1. Перейдите на https://mermaid.live")
        print("2. Вставьте содержимое файла")
        print("3. Нажмите 'Download SVG'")
    except Exception as e:
        print(f"Ошибка при сохранении Mermaid-файла: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()