from flask import Flask, jsonify
from subprocess import Popen, PIPE, STDOUT
from time import time
import os
import chess

#ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

p = Popen(["../../cha/src/cha", "-limit", "1000000000", "-min"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
p.stdout.readline()

q = Popen(["../../cha/src/cha", "-quick"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
q.stdout.readline()

def parseFEN(r8,r7,r6,r5,r4,r3,r2,r1):

    fen = "/".join([r8,r7,r6,r5,r4,r3,r2,r1.replace("_"," ").replace("u","?")])
    try:
        actualFEN = ' '.join(fen.replace("?", "-").split(' ')[:4])
        print(actualFEN)
        board = chess.Board(actualFEN)
        assert board.is_valid()
        return fen

    except:
        return None

def CHA(process,r8,r7,r6,r5,r4,r3,r2,r1,quick):

    fen = parseFEN(r8,r7,r6,r5,r4,r3,r2,r1)
    if not fen:
        results = { 'error' : 'invalid FEN' }
        response = jsonify(results)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    cmd = (fen + "\n").encode("utf-8")
    process.stdin.write(cmd)
    process.stdin.flush()
    output = process.stdout.readline().strip().decode("utf-8")

    if "_" in r1:
        lastToMove = "b" if r1.split("_")[1] == "w" else "w"
    else:
        lastToMove = "b"

    intendedWinner = "w" if "white" in r1 else "b" if "black" in r1 else lastToMove
    winnable = "unwinnable" not in output
    tokens = output.split(" ")

    results = {
        'intendedWinner' : intendedWinner,
        'searchNodes' : int(tokens[tokens.index('nodes')+1]),
        'microseconds' : int(tokens[tokens.index('time')+1])
    }

    if not "undetermined" in output:
        results['winnable'] = winnable
        if winnable:
            results['helpmate'] = output.split('#')[0].replace('winnable', '').strip()

    else:
        results['interrupted'] = 'probably ' + ('un' if not quick else '') + 'winnable'

    response = jsonify(results)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

from time import sleep
import threading

queries = {}

def solve_query(fen, stipulation):
    global queries
    deadpos = Popen(["../src/deadpos.py", "--progress-bar",
                     "-solver", "../src/solver.exe"],
                    stdout=PIPE, stdin=PIPE, stderr=STDOUT)

    cmd = fen + " " + stipulation
    deadpos.stdin.write((cmd + "\n").encode("utf-8"))
    deadpos.stdin.flush()
    output = ""
    results = { 'query' : cmd, 'solutions' : []}
    queries[cmd] = results
    t0 = time()
    while "nsols" not in output:
        output = deadpos.stdout.readline().strip().decode("utf-8")
        if len(output) < 1:
            break
        results = queries.get(cmd)
        if "progress" in output:
            completed = float(output.split(" ")[1])
            remaining = 1 if completed == 0 else (1 - completed) / completed
            results['progress'] = completed
            results['remaining'] = int((time() - t0) * remaining)

        elif ">>>" not in output and not "nsols" in output:
            results['solutions'].append(output)

        queries[cmd] = results
        # print(results)
    # results = queries.get(cmd)
    results['progress'] = 1
    results['nsols'] = int(output.split(" ")[1])

@app.route("/deadpos/<r8>/<r7>/<r6>/<r5>/<r4>/<r3>/<r2>/<r1>/<s>", methods=["GET"])
def process_query(r8, r7, r6, r5, r4, r3, r2, r1, s):

    global queries

    fen = parseFEN(r8, r7, r6, r5, r4, r3, r2, r1)
    stipulation = s.replace('m', '#').replace('_', ' ')

    # print(fen, stipulation)
    if not fen:
        results = { 'error' : 'invalid FEN' }
        response = jsonify(results)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    cmd = fen + " " + stipulation
    results = queries.get(cmd, None)
    if results != None:
        response = jsonify(results)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    thr = threading.Thread(target=solve_query, args=[fen, stipulation])
    thr.start()

    results = queries.get(cmd)
    response = jsonify(results)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/cha/quick/<r8>/<r7>/<r6>/<r5>/<r4>/<r3>/<r2>/<r1>", methods=["GET"])
def quick(r8,r7,r6,r5,r4,r3,r2,r1):
    return CHA(q,r8,r7,r6,r5,r4,r3,r2,r1,True)

if __name__ == '__main__':
    #context = ('/etc/ssl/certs/elrubiongamma_certificate.crt', '/etc/ssl/private/elrubiongamma_private.key')
    #app.run(host='0.0.0.0',port=5000, ssl_context=context)
    app.run(host='0.0.0.0', port=6006)

