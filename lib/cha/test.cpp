#include "cha.h"
#include "stockfish.h"

int main () {
  init_stockfish();
  CHA::init();

  Position pos;
  StateListPtr states(new std::deque<StateInfo>(1));
  pos.set("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", false, &states->back(), Threads.main());
  std::cout << pos;
  std::cout << std::endl;
  bool b = CHA::is_dead(pos);
  std::cout << "DEAD: " << b << std::endl;

  return 0;
}
