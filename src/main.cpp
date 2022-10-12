#include "cha.h"
#include "solver.h"
#include <sstream>
#include <stdexcept>

enum SearchType { COOPERATIVE, COMPETITIVE };

struct Stipulation {
  SearchType searchType;
  SOLVER::Goal goal;
};

// We expect input commands to be a line of text containing a stipulation,
// followed by a valid FEN string.

Stipulation parse_line(Position &pos, float &nmoves, StateInfo *si,
                       std::string &line, bool &is_comment) {

  std::string fen, stipulation, token;
  std::istringstream iss(line);

  iss >> stipulation;

  if (stipulation.empty() || stipulation.substr(0, 2) == "//") {
    // this input line will be ignored, return anything
    is_comment = true;
    return {COMPETITIVE, SOLVER::MATE};
  }

  while (iss >> token)
    fen += token + " ";

  pos.set(fen, false, si, Threads.main());

  if (stipulation.substr(0, 2) == "h#") {
    nmoves = std::stof(stipulation.substr(2));
    return {COOPERATIVE, SOLVER::MATE};
  }

  else if (stipulation.substr(0, 2) == "h=") {
    nmoves = std::stof(stipulation.substr(2));
    return {COOPERATIVE, SOLVER::DRAW};
  }

  else if (stipulation.substr(0, 3) == "hdp") {
    nmoves = std::stof(stipulation.substr(3));
    return {COOPERATIVE, SOLVER::DEAD};
  }

  else if (stipulation.substr(0, 1) == "#") {
    nmoves = std::stof(stipulation.substr(1));
    return {COMPETITIVE, SOLVER::MATE};
  }

  else if (stipulation.substr(0, 1) == "=") {
    nmoves = std::stof(stipulation.substr(1));
    return {COMPETITIVE, SOLVER::DRAW};
  }

  else if (stipulation.substr(0, 2) == "dp") {
    nmoves = std::stof(stipulation.substr(2));
    return {COMPETITIVE, SOLVER::DEAD};
  }

  else
    throw std::invalid_argument("unknown stipulation");
};

// loop() waits for a command from stdin or tests file and analyzes it.

void loop(int argc, char *argv[]) {

  Position pos;
  std::string line;
  StateListPtr states(new std::deque<StateInfo>(1));

  static UTIL::Search search = UTIL::Search();

  while (getline(std::cin, line)) {

    if (line == "quit")
      break;

    float nmoves;
    bool is_comment = false;
    Stipulation stipulation = parse_line(pos, nmoves, &states->back(), line,
                                         is_comment);

    if (is_comment) {
      std::cout << line << std::endl;
      continue;
    }
    search.init();

    int nsols = 0;
    auto start = std::chrono::high_resolution_clock::now();

    if (stipulation.searchType == COOPERATIVE) {
      int n = (int)(2 * nmoves);
      if (stipulation.goal == SOLVER::MATE)
        nsols = SOLVER::help_mate(pos, n, search);

      else if (stipulation.goal == SOLVER::DRAW)
        nsols = SOLVER::help_draw(pos, n, search);

      else if (stipulation.goal == SOLVER::DEAD)
        nsols = SOLVER::help_dead(pos, n, search);

    } else if (stipulation.searchType == COMPETITIVE) {
      int n = (int)(2 * nmoves - 1);
      if (stipulation.goal == SOLVER::MATE)
        nsols = SOLVER::force_mate(pos, n, search);

      if (stipulation.goal == SOLVER::MATE)
        nsols = SOLVER::force_draw(pos, n, search);

      else if (stipulation.goal == SOLVER::DEAD)
        nsols = SOLVER::force_dead(pos, n, search);
    }

    auto stop = std::chrono::high_resolution_clock::now();
    auto diff =
        std::chrono::duration_cast<std::chrono::milliseconds>(stop - start);
    uint64_t duration = diff.count();

    std::cout << "nsols " << nsols << std::endl;
    std::cout << "time " << duration << " ms" << std::endl;
  }

  Threads.stop = true;
}

int main(int argc, char *argv[]) {

  init_stockfish();
  CHA::init();
  std::cout << "Deadpos Analyzer version 1.0" << std::endl;

  CommandLine::init(argc, argv);
  loop(argc, argv);

  Threads.set(0);
  return 0;
}
