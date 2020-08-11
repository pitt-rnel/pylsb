@echo off
echo nats-python bench tests:
echo.

echo "1 Producer, No Consumers:"
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 0 -ms 100
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 0 -ms 1000
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 0 -ms 1000000
echo.

echo "1 Producer, 1 Consumers:"
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 1 -ms 100
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 1 -ms 1000
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 1 -ms 1000000
echo.

echo "1 Producer, 5 Consumers:"
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 5 -ms 100
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 5 -ms 1000
echo.
python nats_python_bench.py -n 10000 -np 1 -ns 5 -ms 1000000
echo.

echo "5 Producer, 5 Consumers:"
echo.
python nats_python_bench.py -n 10000 -np 5 -ns 5 -ms 100
echo.
python nats_python_bench.py -n 10000 -np 5 -ns 5 -ms 1000
echo.
python nats_python_bench.py -n 10000 -np 5 -ns 5 -ms 1000000
echo.
