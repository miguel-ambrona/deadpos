const port = 6006;

const INIT_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR';

let board = null;
let enabledEdit = false;

$(document).ready(function() {

    let params = {
        fen: document.getElementById('fen').value,
        draggable: true,
        sparePieces: true,
        dropOffBoard: 'trash',
        onChange: function() { setTimeout(refresh_fen,20); }
    };

    board = ChessBoard('board', params);
    window.addEventListener('resize', resize);
    // document.getElementById('fen').value = INIT_FEN;

    let URLFEN = getParameterByName('FEN');

    if (URLFEN){
        document.getElementById('fen').value = URLFEN.replaceAll('_',' ');
        refresh_position();
    }

    let URLGOAL = getParameterByName('GOAL');

    if (URLGOAL){
        document.getElementById('stipulation').value = URLGOAL.replaceAll('m','#').replaceAll('d','=').replaceAll('_',' ');
    }

});

function api_request(cmd, onReceive) {

    // Performs a GET request to the endpoint, with the specified command
    // onReceive function will be executed after the response is received

    let ip = document.getElementById('ip').value;
    if (!ip) { ip = 'localhost'; }
    let endpoint = 'https://' + ip + ':' + port + '/deadpos/';
    let request = new XMLHttpRequest();
    cmd = cmd.replace(/\?/g, "u");
    request.open('GET', endpoint + cmd.replace(/ /g, "_"), true);
    request.onload = function () { if(onReceive) onReceive(JSON.parse(this.response)); };
    request.send();
};


function analyze() {

    $('#solve-btn').prop('disabled', true);
    $("body").css("cursor", "progress");
    let results = $('#results');
    let stipulation = document.getElementById('stipulation').value.replace(/#/g, "m");
    let options = document.getElementById('options').value;
    if (options) { turn = options; } else { turn = 'w - -' }
    let fen = document.getElementById('fen').value + ' ' + turn;
    let cmd = fen + '/' + stipulation;

    api_request(cmd, function(data){
        console.log(data);
        if (!data) {
            results.html('');
            $('#progress-bar').removeClass('bg-success');
            $('#progress-bar').addClass('bg-primary');
            $('#progress-bar').addClass('progress-bar-animated');
            $('#progress-bar').html(''); // comment
            $('#progress-bar').width("0%");
            $('#remaining-bar').width("100%"); // comment
        }
        if (data && data.progress) {
            let completed = 100*data.progress;
            $('#progress-bar').width(completed + "%");
            $('#remaining-bar').width((100-completed) + "%"); //comment
            if (completed < 98)
                $('#remaining-bar').html(data.remaining + " s"); //comment
            else
                $('#remaining-bar').html(''); //comment
        }
        if (data && data.solutions) {
            let results = '';
            for (let i = 0; i < data.solutions.length; i++) {
                results += data.solutions[i] + '<br>';
            }
            if (data.nsols) {
                results += "nsols " + data.nsols + "<br>";
            }
            $('#results').html(results);
        }
        if (data && (data.nsols || data.nsols == 0)) {
            $('#solve-btn').prop('disabled', false);
            $("body").css("cursor", "default");
            $('#progress-bar').removeClass('bg-primary');
            $('#progress-bar').addClass('bg-success');
            $('#progress-bar').removeClass('progress-bar-animated');
            $('#progress-bar').html('100%'); //comment
            $('#remaining-bar').width('0%'); //comment
        }
        else {
            // console.log(data);
            setTimeout(analyze, 400);
        }
    });
};

function resize() {
    setTimeout(board.resize, 100);
};

function reset_board() {
    document.getElementById('fen').value = INIT_FEN;
    refresh_position();
};

function clear_board() {
    document.getElementById('fen').value = '8/8/8/8/8/8/8/8';
    refresh_position();
};

function refresh_fen() {
    document.getElementById('fen').value = board.fen();
};

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
    results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function refresh_position() {
    board.highlight_clear();
    var fen = document.getElementById('fen').value;
    board.position(fen, false);
    refresh_fen();
};

function guess_options() {
    let stipulation = document.getElementById('stipulation').value;
    let parts = stipulation.split('>>=');
    let parity = 0;
    for (var i = 0; i < parts.length; i++) {
        if (parts[i].includes('h'))
            parity++;

        if (parts[i].includes('.5'))
            parity++;

        if (parts[i].trim()[0] == 'r')
            parity += parseInt(parts[i].trim().slice(1))
    }
    let options = parity % 2 == 0 ? 'w ? ?' : 'b ? ?';
    document.getElementById('options').value = options;
};
