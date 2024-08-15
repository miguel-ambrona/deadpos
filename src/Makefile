SHERLOCK_VERSION = 9f7faa81d5c6f01d9cce1c4eff8c0821614f92c8

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

get-sherlock:
	if [ -d ../lib/sherlock ]; then rm -Rf ../lib/sherlock; fi
	cd ../lib/ && git clone https://github.com/miguel-ambrona/sherlock-ocaml.git sherlock
	cd ../lib/sherlock && git checkout $(SHERLOCK_VERSION)
	cd ../lib/sherlock && ./scripts/install_build_deps.sh
	cd ../lib/sherlock && eval `(opam env)` && dune build

update-sherlock:
	cd ../lib/sherlock && git fetch && git checkout $(SHERLOCK_VERSION)
	cd ../lib/sherlock && eval `(opam env)` && dune build

test:
	cat ../test/test-vectors.txt | python3 deadpos.py --no-progress-bar > /tmp/test-vectors.out
	diff ../test/test-vectors.out /tmp/test-vectors.out

pdb-tests:
	cat ../test/PDB.txt | grep -v Slow | python3 deadpos.py --no-progress-bar > /tmp/PDB.out
	diff ../test/PDB.out /tmp/PDB.out

promote-tests:
	cp /tmp/test-vectors.out ../test/test-vectors.out
	cp /tmp/PDB.out ../test/PDB.out


.PHONY: solver test
