#  CHA is free software provided under the GNU General Public License.
#  The full source code of CHA can be found here:
#  <https://github.com/miguel-ambrona/D3-Chess>.

cha:
	git clone https://github.com/miguel-ambrona/D3-Chess.git
	cd D3-Chess/src/ && make cha-lib

install:
	cd D3-Chess/src/ && make install

test:
	g++ -o test test.cpp -I/usr/local/include/stockfish -lstockfish -I/usr/local/include/cha -lcha

.PHONY: cha test
