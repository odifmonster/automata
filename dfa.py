#!/usr/bin/env python

from collections import defaultdict
from typing import Self

from nfa import *

class DFA:

    def __init__(self) -> None:
        self.start: int = 0
        self.finals: set[int] = set()
        self.states: set[int] = {0,-1}
        self.sigma: set[str] = set()

        self.delta: dict[tuple[int,str],int] = defaultdict(lambda:-1)
    
    def to_dot_string(self) -> str:

        nfs = self.states-self.finals
        dot_lines: list[str] = [
            'digraph G {', '\trankdir="LR";\n', '\tH [style=invis];',
            '\t{ node [shape=circle]; ' + ' '.join([str(p) for p in nfs]) + ' }',
            '\t{ node [shape=doublecircle]; ' + ' '.join([str(p) for p in self.finals]) + ' }\n',
            f'\tH -> {self.start};'
        ]

        for state in self.states:
            for a in self.sigma:
                dot_lines.append(f'\t{state} -> {self.delta[(state,a)]} [label={a}];')
        
        return '\n'.join(dot_lines + ['}'])
    
    @classmethod
    def from_nfa(cls, nfa: NFA) -> Self:

        dfa = DFA()

        adj_mat = nfa.get_adj_mat()
        reachable: list[int] = [dfa.start]
        processed: set[tuple[int]] = set()

        int_to_tuple: dict[int, tuple[int]] = { dfa.start:(nfa.start,), -1:tuple() }
        tuple_to_int: dict[tuple[int], int] = { (nfa.start,):dfa.start, tuple():-1 }

        while reachable:
            s = reachable.pop(0)
            dfa.states.add(s)

            s_tuple = int_to_tuple[s]
            if not nfa.finals.isdisjoint(s_tuple):
                dfa.finals.add(s)
            
            processed.add(s_tuple)

            mini_delta: dict[str, set[int]] = defaultdict(lambda:set())

            for start_st in s_tuple:
                for end_st in nfa.states:
                    for a in adj_mat[start_st][end_st]:
                        mini_delta[a].add(end_st)
                        dfa.sigma.add(a)
            
            for a, t_subset in mini_delta.items():
                t_tuple = tuple(sorted(t_subset))

                if t_tuple not in tuple_to_int:
                    t = max(iter(int_to_tuple.keys()))+1
                    int_to_tuple[t] = t_tuple
                    tuple_to_int[t_tuple] = t
                
                t = tuple_to_int[t_tuple]

                if t_tuple not in processed:
                    reachable.append(t)

                dfa.delta[(s,a)] = t
        
        if -1 not in dfa.delta.values():
            dfa.states -= {-1}

        return dfa
    
    @classmethod
    def minimize(cls, dfa: Self) -> Self:

        state_split: dict[int, set[int]] = {
            0: dfa.states.difference(dfa.finals),
            1: dfa.finals.copy()
        }
        next_split: dict[int, set[int]] = {}

        minimal = False
        while not minimal:
            minimal = True

            for subset in state_split.values():
                i = len(next_split)

                if len(subset) == 1:
                    next_split[i] = subset
                    continue

                trans_table: dict[tuple[tuple[str,int]],set[int]] = defaultdict(lambda:set())

                for s in subset:
                    trans_list: list[tuple[str,int]] = []
                    for a in dfa.sigma:
                        dest = dfa.delta[(s,a)]

                        for k,v in state_split.items():
                            if dest in v: trans_list.append((a,k))
                    trans_tuple = tuple(sorted(trans_list))
                    trans_table[trans_tuple].add(s)
                
                if len(trans_table) > 1:
                    minimal = False

                for set_split in trans_table.values():
                    next_split[len(next_split)] = set_split
            
            state_split = next_split
            next_split = {}
        
        min_dfa = DFA()
        min_dfa.states = set(state_split.keys())
        min_dfa.sigma = dfa.sigma.copy()

        for s, subset in state_split.items():
            if subset.issubset(dfa.finals): min_dfa.finals.add(s)
            if dfa.start in subset: min_dfa.start = s

            model = list(subset)[0]

            for a in min_dfa.sigma:
                dest = dfa.delta[(model,a)]
                for k,v in state_split.items():
                    if dest in v: min_dfa.delta[(s,a)] = k
        
        return min_dfa

def main():
    test_tree = simplify_tree(get_expr_tree('(0+1(01*0)*1)*'))
    ord_nfa = OrdNFA.from_tree(test_tree)
    nfa = kill_lbd_moves(ord_nfa)

    dfa = DFA.from_nfa(nfa)
    with open('dfa.dot', 'w', encoding='utf8') as dfaout:
        dfaout.write(dfa.to_dot_string())
    
    min_dfa = DFA.minimize(dfa)
    with open('min_dfa.dot', 'w', encoding='utf8') as mindfaout:
        mindfaout.write(min_dfa.to_dot_string())

if __name__ == '__main__':
    main()