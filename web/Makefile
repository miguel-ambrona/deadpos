get-board:
	if [ -d board ]; then rm -Rf board; fi
	git clone https://gitlab.com/ambrona/board.git
	sed -i 's+img/+board/img/+g' board/js/board.js
	sed -i 's+audio/+board/audio/+g' board/js/board.js
