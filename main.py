import argparse
import sys
import ssl
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET


def parse_args():
    parser = argparse.ArgumentParser(description="Инструмент визуализации зависимости пакетов (NuGet, Этап 2)")
    parser.add_argument("--package", required=True, help="Имя пакета")
    parser.add_argument("--repo-url", required=True, help="URL репозитория (для совместимости)")
    parser.add_argument("--version", required=True, help="Версия пакета")
    parser.add_argument("--output", default="graph.svg", help="Имя файла вывода (для будущих этапов)")
    return parser.parse_args()


def fetch_nuspec(package, version):
    url = f"https://api.nuget.org/v3-flatcontainer/{package.lower()}/{version}/{package.lower()}.nuspec"
    print(f"Запрос: {url}")

    # Отключаем SSL-проверку
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urlopen(url, context=ctx) as response:
            return response.read().decode("utf-8")
    except HTTPError as e:
        if e.code == 404:
            print(f"Ошибка: пакет '{package}' версии '{version}' не найден.", file=sys.stderr)
        else:
            print(f"HTTP ошибка {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


def extract_dependencies(xml_content):
    root = ET.fromstring(xml_content)
    ns = {"ns": "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"}
    deps = []

    for dep in root.findall(".//ns:dependency", ns):
        name = dep.get("id")
        version = dep.get("version", "*")
        if name:
            deps.append((name, version))
    return deps


def main():
    config = parse_args()

    print("Конфигурация:")
    for k, v in vars(config).items():
        print(f"    {k}: {v}")
    print()

    xml = fetch_nuspec(config.package, config.version)
    dependencies = extract_dependencies(xml)

    print("Прямые зависимости:")
    if dependencies:
        for name, ver in dependencies:
            print(f"  - {name} ({ver})")
    else:
        print("  Нет прямых зависимостей.")


if __name__ == "__main__":
    main()