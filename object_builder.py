from random import choice, randrange, random

def generate_random_duckie(tag):
    kind = 'duckie'
    offset = random(), random()
    pos = [float(f'{randrange(0, 3) + offset[0]:.2f}'),
        float(f'{randrange(16, 19) - offset[1]:.2f}')]
    rotate = randrange(0, 360)
    height = random()/20.0 + 1/20
    name = f'{kind}{tag}r'
    with open("patterns.txt", "a+") as out:
        out.write(f' {name}:\n'
            f'  kind: {kind}\n'
            f'  pos: {pos}\n'
            f'  rotate: {rotate}\n'
            f'  height: {height:.2f}\n')
    
def generate_some_trees(tag, ix, iy):
    start = [13.0, 17.3]
    start[0] += ix
    start[1] += iy
    dxs = [0.0, 0.2, 0.5]
    dys = [0.0, 0.4, -0.2]
    hs = [0.7, 0.6, 0.5]
    with open("patterns.txt", "a+") as out:
        for dx, dy, h in zip(dxs, dys, hs):
            out.write(f' tree{tag}{int(h*10)}r:\n'
                f'  kind: tree\n'
                f'  pos: [{start[0]+dx}, {start[1]+dy}]\n'
                f'  rotate: 0\n'
                f'  height: {h}\n')

for i in range(1, 8):
    generate_some_trees(f'{i}r', i-2, 0)
#     generate_random_duckie(f'{i}k')