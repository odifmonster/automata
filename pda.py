#!/usr/bin/env python

from enum import Enum
from typing import Self

class TreeOp(Enum):
    CNCT, STAR, UNION, PAREN = 0, 1, 2, 3

    def __str__(self) -> str:
        return self.name

class RegExTree:

    def __init__(self,
                 left: Self | str = '',
                 right: Self | str | None = None,
                 op: TreeOp = TreeOp.CNCT) -> None:
        self.left: RegExTree | str = left
        self.right: RegExTree | str | None = right
        self.op: TreeOp = op
    
    def __str__(self) -> str:
        l = 'LAMBDA' if self.left == '' else str(self.left)

        if self.right is None:
            return ' '.join(['(',str(self.op),l,')'])
        
        r = 'LAMBDA' if self.right == '' else str(self.right)
        return ' '.join(['(',str(self.op),l,r,')'])
    
    def pretty_string(self) -> str:

        l = self.left if type(self.left) is str else self.left.pretty_string()
        if self.right is None:
            r = None
        else:
            r = self.right if type(self.right) is str else self.right.pretty_string()

        l = l.split('\n')
        r = [] if r is None else r.split('\n')
            
        new_l, new_r = [], []
        if l[0]: new_l.append(str(self.op) + '---' + l[0])
        else: new_l.append(str(self.op) + '---LAMBDA')
        if r:
            if r[0]: new_r.append(' '*(len(str(self.op))+2) + '-' + r[0])
            else: new_r.append(' '*(len(str(self.op))+2) + '-LAMBDA')

        for line in l[1:]:
            line = line if line else 'LAMBDA'
            if r: new_l.append(' '*(len(str(self.op))+1)+'| '+line)
            else: new_l.append(' '*(len(str(self.op))+3)+line)
            
        for line in r[1:]:
            line = line if line else 'LAMBDA'
            new_r.append(' '*(len(str(self.op))+3)+line)
            
        if r:
            lines = new_l + [' '*(len(str(self.op))+1) + '|'] + new_r
        else:
            lines = new_l

        return '\n'.join(lines)

class PDA:

    def __init__(self) -> None:

        self.blank: str = ''
        self.sigma: set[str] = set()
        self.gamma: set[str] = set()

        self.start: str = ''
        self.states: set[str] = set()
        self.finals: set[str] = set()

        self.delta: dict[tuple[str,str,str],tuple[str,str]] = {}
    
    def check_string(self, w: str) -> bool:

        stack: list[str] = []
        cur_state: str = self.start
        
        for letter in w:

            to_pop = self.blank
            if len(stack) > 0 and (cur_state,stack[-1],letter) in self.delta:
                to_pop = stack.pop()
            
            next_state, to_push = self.delta[(cur_state,to_pop,letter)]
            if to_push in self.gamma:
                stack.append(to_push)
            
            cur_state = next_state
        
        return len(stack) == 0 and cur_state in self.finals

def parse_pda(pdapath: str) -> PDA:
    with open(pdapath, encoding='utf8') as pdafile:
        lines = [''.join(l.split()) for line in pdafile if (l:=line.strip()) != '']
    
    statements: list[str] = []
    stmt_in_progress: bool = False

    for line in lines:
        line, *_ = line.split('#')

        if line == '': continue

        if not stmt_in_progress:
            if '{' in line and '}' not in line:
                stmt_in_progress = True
            statements.append(line)
        else:
            if '}' in line:
                stmt_in_progress = False
            statements[-1] += line

    pda = PDA()
    val_dict: dict[str, str | set[str] | set[tuple[str,str,str,str,str]]] = {}

    for stmt in statements:
        name, val = stmt.split('=')
        if val[0] == '{' and val[-1] == '}':
            if name == 'Delta':
                tuples = val[2:-2].split('>,<')
                val_dict[name] = set()
                for tup in tuples:
                    val_dict[name].add(tuple(tup.split(',')))
            else:
                val_dict[name] = set(val[1:-1].split(','))
        else:
            val_dict[name] = val
    
    pda.blank, pda.sigma, pda.gamma = val_dict['lambda'], val_dict['Sigma'], val_dict['Gamma']
    pda.start, pda.states, pda.finals = val_dict['start'], val_dict['Q'], val_dict['F']

    for p1, g1, a, p2, g2 in val_dict['Delta']:
        if a not in pda.sigma:
            char_set = val_dict[a]
            for letter in char_set:
                pda.delta[(p1,g1,letter)] = (p2,g2)
        else:
            pda.delta[(p1,g1,a)] = (p2,g2)
    
    return pda

def get_expr_tree(regex: str, pdapath: str = 'regex.pda') -> RegExTree | None:

    regex_pda = parse_pda(pdapath)
    if not regex_pda.check_string(regex): return None

    op_stack: list[TreeOp] = []
    n_stack: list[str | RegExTree] = ['']

    for letter in regex:
        match letter:
            case '(':
                op_stack.append(TreeOp.CNCT)
                op_stack.append(TreeOp.PAREN)
                n_stack.append('')
            case '*':
                if type(n_stack[-1]) is str:
                    last_str = n_stack.pop()
                    last_ltr = last_str[-1]
                    n_stack.append(last_str[:-1])
                    n_stack.append(RegExTree(left=last_ltr, op=TreeOp.STAR))
                    op_stack.append(TreeOp.CNCT)
                else:
                    n_stack.append(RegExTree(left=n_stack.pop(), op=TreeOp.STAR))
            case '+':
                while len(op_stack) > 0 and op_stack[-1] != TreeOp.PAREN:
                    last_op = op_stack.pop()
                    n2, n1 = n_stack.pop(), n_stack.pop()
                    n_stack.append(RegExTree(left=n1, right=n2, op=last_op))
                
                op_stack.append(TreeOp.UNION)
                n_stack.append('')
            case ')':
                while op_stack[-1] != TreeOp.PAREN:
                    last_op = op_stack.pop()
                    n2, n1 = n_stack.pop(), n_stack.pop()
                    n_stack.append(RegExTree(left=n1, right=n2, op=last_op))

                op_stack.pop()
            case _:
                if type(n_stack[-1]) is str:
                    n_stack[-1] = n_stack[-1] + letter
                else:
                    op_stack.append(TreeOp.CNCT)
                    n_stack.append(letter)
    
    return n_stack.pop()

def simplify_tree(tree: RegExTree | str | None) -> RegExTree:
    if type(tree) is str or tree is None:
        return tree
    else:
        simple_tree = RegExTree(
            left = simplify_tree(tree.left),
            right = simplify_tree(tree.right),
            op = tree.op
        )

        if simple_tree.op == TreeOp.CNCT and not (simple_tree.left and simple_tree.right):
            if not (simple_tree.left or simple_tree.right):
                return ''
            elif simple_tree.right:
                return simple_tree.right
            else:
                return simple_tree.left
        
        return simple_tree

def main():
    test_tree = get_expr_tree('(((a+b)*ab)+(ba+a)*)*')
    print(str(test_tree))
    print(test_tree.pretty_string())
    simple_tree = simplify_tree(test_tree)
    print(str(simple_tree))
    print(simple_tree.pretty_string())

if __name__ == '__main__':
    main()