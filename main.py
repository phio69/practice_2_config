import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description= "Инструмент визуализации зависимости пакетов"
    )
    parser.add_argument(
        "--package",
        required= True,
        help= "Имя анализируемого пакета"
    )
    parser.add_argument(
        "--repo-url",
        required= True,
        help= "URL репозитория или путь к тестовому файлу"
    )
    parser.add_argument(
        "--version",
        required= True,
        help= "Версия пакета"
    )
    parser.add_argument(
        "--output",
        default= "graph.svg",
        help= "Имя для сохранения изображения"
    )
    parser.add_argument(
        "--test-mode",
        action ="store_true",
        help = "Режим тестирования"
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        print("Ошибка: не указаны обязательные параметры", file=sys.stderr)
        sys.exit(1)

    return args

def main():
    config = parse_args()

    #Вывод всех параметров в формате "ключ-значение"
    print("Конфигурация: ")
    for key, value in vars(config).items():
        print(f"    {key}: {value}")

if __name__ == "__main__":
    main()