echo "Этап 3: Тест ациклического графа (A → B, C)"
python3 main.py --package A --repo-url test_data/test_graph_stage3.1.json --version 1.0.0 --test-mode

echo ""
echo "Этап 3: Тест циклического графа (A → B → C → A)"
python3 main.py --package A --repo-url test_data/test_graph_stage3.2.json --version 1.0.0 --test-mode

echo ""
echo "Этап 3: Тест реального пакета NuGet"
python3 main.py --package Newtonsoft.Json --repo-url https://api.nuget.org/v3/index.json --version 13.0.1