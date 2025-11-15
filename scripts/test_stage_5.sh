echo "Этап 5: тестирования"
echo "Линейная зависимость"
python main.py --package A --repo-url test_data/example1.json --version 1.0.0 --test-mode --output graph1.svg

echo ""
echo "Ветвление"
python main.py --package A --repo-url test_data/example2.json --version 1.0.0 --test-mode --output graph2.svg

echo ""
echo "С циклом"
python main.py --package A --repo-url test_data/example3.json --version 1.0.0 --test-mode --output graph3.svg