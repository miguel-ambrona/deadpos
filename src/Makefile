deadpos:
	g++ -o deadpos solver.cpp main.cpp -I/usr/local/include/stockfish -lstockfish -I/usr/local/include/cha -lcha

get-stockfish:
	if [ -d ../lib/stockfish/Stockfish ]; then rm -Rf ../lib/stockfish/Stockfish; fi
	cd ../lib/stockfish/ && make get-stockfish
	cd ../lib/stockfish/ && make

install-stockfish:
	cd ../lib/stockfish/ && make install

get-cha:
	if [ -d ../lib/cha/D3-Chess ]; then rm -Rf ../lib/cha/D3-Chess; fi
	cd ../lib/cha/ && make

install-cha:
	cd ../lib/cha/ && make install


test:
	cat ../test/positions.txt | ./deadpos

.PHONY: deadpos test
