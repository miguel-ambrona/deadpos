#ifndef UTIL_H_INCLUDED
#define UTIL_H_INCLUDED

namespace UTIL {

constexpr int MAX_VARIATION_LENGTH = 300;

class Search {
public:
  Search() = default;

  void init();

  Depth search_depth() const;

  void push(Move m);
  void pop();

  void print_solution(bool dead, bool stalemate) const;

private:
  Move solution[MAX_VARIATION_LENGTH];
  Color winner;
  Depth depth;
};

inline void Search::init() { depth = 0; }

inline Depth Search::search_depth() const { return depth; }

inline void Search::push(Move m) {
  if (depth < MAX_VARIATION_LENGTH)
    solution[depth] = m;
  depth++;
}

inline void Search::pop() { depth--; }

inline void Search::print_solution(bool dead, bool stalemate) const {
  std::cout << "solution";
  for (int i = 0; i < std::min(depth, MAX_VARIATION_LENGTH); i++)
    std::cout << " " << UCI::move(solution[i], false);
  if (!dead)
    std::cout << "#";
  else if (stalemate)
    std::cout << " stalemate";
  else
    std::cout << " DP";
  std::cout << std::endl;
}

} // namespace UTIL

#endif // #ifndef UTIL_H_INCLUDED
