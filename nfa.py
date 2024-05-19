#!/usr/bin/env python

from typing import Self
from pda import *

class NFA:

    def __init__(self, blank: str = '_') -> None:
        self.start: int = 0
        self.finals: set[int] = set()
        self.states: set[int] = {0}

        self.delta: set[tuple[int,str,int]] = set()

        self.blank: str = blank
    
    def set_start(self, news: int) -> None:

        self.states.remove(self.start)
        self.states.add(news)
        new_delta: set[tuple[int,int,int]] = set()

        for p,a,q in self.delta:
            if p == self.start:
                new_delta.add((news,a,q))
            else: new_delta.add((p,a,q))
        
        self.start = news
        self.delta = new_delta
    
    def add_states_from_delta(self) -> None:

        self.states.clear()
        for p,_,q in self.delta: self.states.update({p,q})
    
    def get_adj_mat(self) -> list[list[list[str]]]:

        max_s = max(self.states)
        adj_mat: list[list[list[str]]] = [
            [[] for _ in range(max_s+1)] for _ in range(max_s+1)
        ]

        for p,a,q in self.delta:
            adj_mat[p][q].append(a)

        return adj_mat
    
    def to_dot_string(self) -> str:

        nfs = self.states - self.finals
        dotlines: list[str] = ['digraph G {', '\trankdir="LR";\n', '\tH [style=invis];',
                               '\t{ node [shape=circle]; ' + \
                                    ' '.join([str(p) for p in nfs]) + ' }',
                               '\t{ node [shape=doublecircle]; ' + \
                                    ' '.join([str(f) for f in self.finals]) + '}\n',
                               f'\tH -> {self.start};']
        
        for p,a,q in self.delta:
            if a == self.blank:
                a = u'\u03bb'
            
            dotlines.append(f'\t{p} -> {q} [label={a}];')
        
        return '\n'.join(dotlines + ['}'])

class OrdNFA(NFA):

    def __init__(self, blank: str = '_') -> None:
        super().__init__(blank=blank)
    
    def get_final(self) -> int:
        return list(self.finals)[0]

    def set_final(self, newf: int) -> None:

        self.states = self.states.difference(self.finals)
        self.states.add(newf)
        new_delta: set[tuple[int,int,int]] = set()

        for p,a,q in self.delta:
            if q in self.finals:
                new_delta.add((p,a,newf))
            else: new_delta.add((p,a,q))
        
        self.finals = {newf}
        self.delta = new_delta

    def set_state(self, p: int, newp: int) -> None:

        if p == self.start: self.set_start(newp)
        elif p in self.finals: self.set_final(newp)
        else:
            self.states.remove(p)
            self.states.add(newp)
            new_delta: set[tuple[int,str,int]] = set()

            for s,a,t in self.delta:
                news, newt = s, t
                if s == p: news = newp
                if t == p: newt = newp
                new_delta.add((news,a,newt))

            self.delta = new_delta
    
    def set_blank(self, newa: str) -> None:

        new_delta: set[tuple[int,str,int]] = set()

        for p,a,q in self.delta:
            if a == self.blank: new_delta.add((p,newa,q))
            else: new_delta.add((p,a,q))
        
        self.blank = newa
        self.delta = new_delta
    
    @classmethod
    def from_string(cls, w: str, start: int, blank: str = '_') -> Self:

        nfa = OrdNFA(blank=blank)
        nfa.set_start(start)

        for i in range(start,start+len(w)):
            nfa.states.add(i+1)
            nfa.delta.add((i,w[i-start],i+1))
        
        nfa.finals = {start+len(w)}

        return nfa
    
    @classmethod
    def star(cls, nfa: Self, blank: str = '_') -> Self:
        starred = OrdNFA(blank=nfa.blank)

        starred.set_start(nfa.start-1)
        starred.set_final(nfa.get_final()+1)

        starred.states.update(nfa.states)
        starred.delta.update(nfa.delta)
        starred.delta.update({
            (starred.start,blank,nfa.start),
            (nfa.start,blank,nfa.get_final()),
            (nfa.get_final(),blank,nfa.start),
            (nfa.get_final(),blank,starred.get_final())
        })

        if blank != nfa.blank: starred.set_blank(blank)

        return starred
    
    @classmethod
    def union(cls, nfa1: Self, nfa2: Self, blank: str = '_') -> Self:

        unioned = OrdNFA(blank=nfa1.blank)

        unioned.delta.update(nfa1.delta)
        unioned.start = nfa1.start
        unioned.add_states_from_delta()
        unioned.set_state(nfa1.get_final(), nfa2.get_final())
        if unioned.blank != nfa1.blank: unioned.set_blank(nfa2.blank)
        
        unioned.delta.update(nfa2.delta)
        unioned.finals = {nfa2.get_final()}
        unioned.add_states_from_delta()
        unioned.set_state(nfa2.start, unioned.start)
        if unioned.blank != blank: unioned.set_blank(blank)

        return unioned
    
    @classmethod
    def concat(cls, nfa1: Self, nfa2: Self, blank: str = '_') -> Self:

        concated = OrdNFA(blank=nfa1.blank)
        concated.delta.update(nfa1.delta)
        concated.states.update(nfa1.states)
        if concated.blank != nfa2.blank: concated.set_blank(nfa2.blank)

        concated.delta.update(nfa2.delta)
        concated.states.update(nfa2.states)
        if concated.blank != blank: concated.set_blank(blank)

        concated.start = nfa1.start
        concated.finals = {nfa2.get_final()}

        return concated
    
    @classmethod
    def from_tree(cls, tree: RegExTree | str, start: int = 0, blank: str = '_') -> Self:
        
        if type(tree) is str:
            return cls.from_string(tree, start=start, blank=blank)
        else:
            match tree.op:
                case TreeOp.STAR:
                    nfa = cls.from_tree(tree.left, start=start+1)
                    return cls.star(nfa, blank=blank)
                case TreeOp.UNION:
                    nfa1 = cls.from_tree(tree.left, start=start)
                    nfa2 = cls.from_tree(tree.right, start=nfa1.get_final())
                    return cls.union(nfa1, nfa2, blank=blank)
                case TreeOp.CNCT:
                    nfa1 = cls.from_tree(tree.left, start=start)
                    nfa2 = cls.from_tree(tree.right, start=nfa1.get_final())
                    return cls.concat(nfa1, nfa2, blank=blank)
                case _: raise RuntimeError('Bad operator for RegExTree.')

def lbd_paths_from(node: int, adj_mat: list[list[list[str]]], lbd: str) -> set[int]:

    reachable: set[int] = set()
    visited: list[int] = []
    to_visit: list[int] = [node]

    while to_visit:
        cur_node = to_visit.pop()
        visited.append(cur_node)
        if cur_node != node: reachable.add(cur_node)

        for next_node in range(len(adj_mat)):
            if lbd in adj_mat[cur_node][next_node] and next_node not in visited:
                to_visit.append(next_node)
    
    return reachable

def ltr_paths_from(node: int, adj_mat: list[list[list[str]]], lbd: str) -> set[tuple[str, int]]:

    to_visit: list[tuple[int,str,int]] = [(0,'',node)]
    paths: set[tuple[str,int]] = set()

    while to_visit:
        dst, path_str, t = to_visit.pop(0)

        if len(path_str) == 1:
            paths.add((path_str,t))

        if dst >= 3: continue

        for r in range(len(adj_mat)):
            for a in adj_mat[t][r]:
                if a == lbd: a = ''
                to_visit.append((dst+1,path_str+a,r))
    
    return paths

def kill_lbd_moves(lbd_nfa: OrdNFA) -> NFA:

    adj_mat = lbd_nfa.get_adj_mat()
    
    for p in lbd_nfa.states:
        lbd_paths = lbd_paths_from(p, adj_mat, lbd_nfa.blank)
        for q in lbd_paths:
            adj_mat[p][q].append(lbd_nfa.blank)
    
    for p in lbd_nfa.states:
        ltr_paths = ltr_paths_from(p, adj_mat, lbd_nfa.blank)
        for ltr, q in ltr_paths:
            adj_mat[p][q].append(ltr)
    
    nfa = NFA()
    nfa.set_start(lbd_nfa.start)
    nfa.finals.update(lbd_nfa.finals)
    if adj_mat[lbd_nfa.start][lbd_nfa.get_final()]: nfa.finals.add(nfa.start)

    for p in range(len(adj_mat)):
        for q in range(len(adj_mat)):
            for a in adj_mat[p][q]:
                if a != lbd_nfa.blank: nfa.delta.add((p,a,q))
    
    nfa.add_states_from_delta()
    return nfa

def main():
    test_tree = simplify_tree(get_expr_tree('(0+1(01*0)*1)*'))

    ord_nfa = OrdNFA.from_tree(test_tree, 0)
    with open('lnfa.dot', 'w', encoding='utf8') as lnfaout:
        lnfaout.write(ord_nfa.to_dot_string())
    
    nfa = kill_lbd_moves(ord_nfa)
    with open('nfa.dot', 'w', encoding='utf8') as nfaout:
        nfaout.write(nfa.to_dot_string())

if __name__ == '__main__':
    main()