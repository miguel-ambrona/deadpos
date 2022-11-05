solver:
	g++ -o solver.exe solver.cpp main.cpp -I/usr/local/include/stockfish -lstockfish -I/usr/local/include/cha -lcha

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

get-chessml:
	if [ -d ../lib/chessml ]; then rm -Rf ../lib/chessml; fi
	cd ../lib/ && git clone https://gitlab.com/ambrona/chessml.git
	cd ../lib/chessml && cp -r ../cha/D3-Chess/ lib/
	cd ../lib/chessml/lib/D3-Chess/src && make
	cd ../lib/chessml && dune build

test-solver:
	cat ../test/positions.txt | ./solver

.PHONY: solver test
