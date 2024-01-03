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

get-retractor:
	if [ -d ../lib/retractor ]; then rm -Rf ../lib/retractor; fi
	cd ../lib/ && curl https://chasolver.org/retractor.zip --output retractor.zip
	cd ../lib/ && unzip retractor.zip && rm retractor.zip
	cd ../lib/retractor && ./scripts/install_build_deps.sh
	cd ../lib/retractor && eval `(opam env)` && opam install -y ocamlgraph
	cd ../lib/retractor && eval `(opam env)` && dune build

test:
	cat ../test/positions.txt | python3 deadpos.py

.PHONY: solver test
