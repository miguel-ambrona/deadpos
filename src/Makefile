deadpos:
	g++ -o deadpos solver.cpp main.cpp -I/usr/local/include/stockfish -lstockfish -I/usr/local/include/cha -lcha

test:
	cat ../test/positions.txt | ./deadpos

.PHONY: deadpos test
