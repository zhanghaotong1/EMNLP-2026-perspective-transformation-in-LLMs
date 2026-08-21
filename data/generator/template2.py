import json
from dataclasses import dataclass
from typing import Literal
from utils import *


@dataclass
class LoopLM:
    id: str
    side: Literal['up', 'down', 'left', 'right']


@dataclass
class PointLM:
    id: str
    attached_to: Literal['up', 'down', 'left', 'right']
    t: float
    side: Literal['left', 'right']


def generate_area(
        min_pl=1,
        max_pl=5,
):
    area = {}

    # generate loop linear landmarks
    boundary_lms = [LoopLM(id=f'loop_{i}', side=d) for i, d in enumerate(['up', 'down', 'left', 'right'])]
    area['loop_lm'] = boundary_lms

    # randomly generate point landmarks along loop linear landmarks
    pls = []
    for i, d in enumerate(['up', 'down', 'left', 'right']):
        n_pl = random.randint(min_pl, max_pl)
        ts = [random.uniform(0.05, 0.95) for _ in range(n_pl)]
        ts.sort()
        for j, t in enumerate(ts):
            pls.append(
                PointLM(
                    id=f'loop_{i}_pl_{j}',
                    attached_to=d,
                    t=t,
                    side=random.choice(['left', 'right']),
                )
            )
    area['point_lm'] = pls

    return area


def generate_names(area):
    transport = random.choice(WORDS_DICT['transport'])
    distance = random.choice(WORDS_DICT['distance'])
    if transport == 'walk':
        proportion = 1
        transporting = 'walking'
    elif transport == 'ride':
        proportion = 2
        transporting = 'riding'
    else:
        transporting = 'driving'
        proportion = 5

    loop_ll_names = {side: random.choice(WORDS_DICT['name']) + ' ' + random.choice(WORDS_DICT['linear_ll1'])
                     for side in ['up', 'down', 'left', 'right']}
    pl_names = random.sample(WORDS_DICT['point_ll'], len(area['point_lm']))
    pl_names_dict = {'up': {}, 'down': {}, 'left': {}, 'right': {}}
    for i, pl in enumerate(area['point_lm']):
        pl_names_dict[pl.attached_to][pl.t] = pl_names[i]

    options = [
        ('top_left', 'up', 'right'),
        ('top_right', 'right', 'down'),
        ('bottom_right', 'down', 'left'),
        ('bottom_left', 'left', 'up'),
        ('top_left', 'left', 'down'),
        ('top_right', 'up', 'left'),
        ('bottom_right', 'right', 'up'),
        ('bottom_left', 'down', 'right'),
    ]
    corner, first_edge, direction = random.choice(options)

    if (first_edge, direction) in [('up', 'right'), ('right', 'down'), ('down', 'left'), ('left', 'up')]:
        traverse = 'clock'
        edge_order = ['up', 'right', 'down', 'left']
        first_edge_index = edge_order.index(first_edge)
        edge_order = edge_order[first_edge_index:] + edge_order[:first_edge_index]
    else:
        traverse = 'counterclock'
        edge_order = ['up', 'left', 'down', 'right']
        first_edge_index = edge_order.index(first_edge)
        edge_order = edge_order[first_edge_index:] + edge_order[:first_edge_index]

    return {
        'transport': transport,
        'transporting': transporting,
        'proportion': proportion,
        'distance': distance,
        'loop_ll': loop_ll_names,
        'pl': pl_names_dict,
        'town_name': random.choice(WORDS_DICT["name"]),
        'corner': corner,
        'direction': direction,
        'edge_order': edge_order,
        'traverse': traverse
    }


def lm2names(names, lm):
    if isinstance(lm, LoopLM):
        return names['loop_ll'][lm.side]
    else:
        return names['pl'][lm.attached_to][lm.t]


def generate_route(area, names):
    transport = names['transport']
    proportion = names['proportion']
    distance = names['distance']

    pl_names = names['pl']
    loop_names = names['loop_ll']
    town_name = names['town_name']
    edge_order = names['edge_order']

    pls_by_edge = {e: [] for e in ['up', 'down', 'left', 'right']}
    for pl in area['point_lm']:
        pls_by_edge[pl.attached_to].append(pl)
    for edge in pls_by_edge:
        pls_by_edge[edge].sort(key=lambda x: x.t)

    description = f'You enter {town_name} Town through {loop_names[edge_order[0]]}. '

    if names['traverse'] == 'clock':
        turn = 'right'
    else:
        turn = 'left'

    cur_t = 0
    for pl in pls_by_edge[edge_order[0]]:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names[edge_order[0]][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += f'Make a {turn} turn onto {loop_names[edge_order[1]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[1]]:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names[edge_order[1]][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += f'Make a {turn} turn onto {loop_names[edge_order[2]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[2]]:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names[edge_order[2]][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += f'Make a {turn} turn onto {loop_names[edge_order[3]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[3]]:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names[edge_order[3]][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += f'You arrive back at your starting point on {loop_names[edge_order[0]]}, completing the tour.'

    return description


def generate_survey(area, names, up='north'):
    up_index = SURVEY_DIRECTIONS.index(up)
    new_sides = {'up': (SURVEY_DIRECTIONS[up_index], SURVEY_DIRECTIONS[(6 + up_index) % 8], SURVEY_DIRECTIONS[(2 + up_index) % 8]),
                 'left': (SURVEY_DIRECTIONS[(6 + up_index) % 8], SURVEY_DIRECTIONS[up_index], SURVEY_DIRECTIONS[(4 + up_index) % 8]),
                 'down': (SURVEY_DIRECTIONS[(4 + up_index) % 8], SURVEY_DIRECTIONS[(6 + up_index) % 8], SURVEY_DIRECTIONS[(2 + up_index) % 8]),
                 'right': (SURVEY_DIRECTIONS[(2 + up_index) % 8], SURVEY_DIRECTIONS[up_index], SURVEY_DIRECTIONS[(4 + up_index) % 8])}

    transport = names['transport']
    transporting = names['transporting']
    proportion = names['proportion']
    distance = names['distance']

    town_name = names['town_name']
    pl_names = names['pl']
    loop_names = names['loop_ll']
    edge_order = names['edge_order']
    traverse = names['traverse']

    pls_by_edge = {e: [] for e in ['up', 'down', 'left', 'right']}
    for pl in area['point_lm']:
        pls_by_edge[pl.attached_to].append(pl)
    for edge in pls_by_edge:
        pls_by_edge[edge].sort(key=lambda x: x.t)

    description = f'{town_name} Town is formed by four boundary routes: '
    description += ', '.join([loop_names[edge] for edge in ['up', 'right', 'down', 'left']]) + '. '
    for edge in ['up', 'down', 'left', 'right']:
        name = loop_names[edge]
        primary, from_dir, to_dir = new_sides[edge]
        description += f'The {primary} side is made up of the {name}, running from {from_dir} to {to_dir}. '

    description += f'You enter the town through {loop_names[edge_order[0]]}. '

    if names['direction'] == 'right':
        current_orientation_index = (2 + up_index) % 8
    elif names['direction'] == 'down':
        current_orientation_index = (4 + up_index) % 8
    elif names['direction'] == 'left':
        current_orientation_index = (6 + up_index) % 8
    else:
        current_orientation_index = up_index

    description += f'{transport.capitalize()} {SURVEY_DIRECTIONS[current_orientation_index]} along the {loop_names[edge_order[0]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[0]]:
        if pl.side == 'left':
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index - 2) % 8]
        else:
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index + 2) % 8]
        description += (
            f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
            f'{pl_names[edge_order[0]][pl.t]} on the {pl_orientation_index}. ')
        cur_t = pl.t

    if traverse == 'clock':
        current_orientation_index = (current_orientation_index + 2) % 8
        turn_dir = SURVEY_DIRECTIONS[current_orientation_index]
    else:
        current_orientation_index = (current_orientation_index - 2) % 8
        turn_dir = SURVEY_DIRECTIONS[current_orientation_index]
    description += f'Make a turn to the {turn_dir} onto {loop_names[edge_order[1]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[1]]:
        if pl.side == 'left':
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index - 2) % 8]
        else:
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index + 2) % 8]
        description += (
            f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
            f'{pl_names[edge_order[1]][pl.t]} on the {pl_orientation_index}. ')
        cur_t = pl.t

    if traverse == 'clock':
        current_orientation_index = (current_orientation_index + 2) % 8
        turn_dir = SURVEY_DIRECTIONS[current_orientation_index]
    else:
        current_orientation_index = (current_orientation_index - 2) % 8
        turn_dir = SURVEY_DIRECTIONS[current_orientation_index]
    description += f'Make a turn to the {turn_dir} onto {loop_names[edge_order[2]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[2]]:
        if pl.side == 'left':
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index - 2) % 8]
        else:
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index + 2) % 8]
        description += (
            f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
            f'{pl_names[edge_order[2]][pl.t]} on the {pl_orientation_index}. ')
        cur_t = pl.t

    if traverse == 'clock':
        current_orientation_index = (current_orientation_index + 2) % 8
        turn_dir = SURVEY_DIRECTIONS[current_orientation_index]
    else:
        current_orientation_index = (current_orientation_index - 2) % 8
        turn_dir = SURVEY_DIRECTIONS[current_orientation_index]
    description += f'Make a turn to the {turn_dir} onto {loop_names[edge_order[3]]}. '

    cur_t = 0
    for pl in pls_by_edge[edge_order[3]]:
        if pl.side == 'left':
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index - 2) % 8]
        else:
            pl_orientation_index = SURVEY_DIRECTIONS[(current_orientation_index + 2) % 8]
        description += (
            f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
            f'{pl_names[edge_order[3]][pl.t]} on the {pl_orientation_index}. ')
        cur_t = pl.t

    description += (f'Continue {transporting} until you complete the tour and return to your starting point on '
                    f'{loop_names[edge_order[0]]}.')

    return description


def generate_symbolic(area, names):
    boundary_side2name = {}
    for b in area['loop_lm']:
        boundary_side2name[b.side] = names['loop_ll'][b.side]

    description = (f'{names["town_name"]} Town is surrounded by {boundary_side2name["up"]}, {boundary_side2name["right"]}, '
                   f'{boundary_side2name["down"]} and {boundary_side2name["left"]}, arranged clockwise. ')

    pls_by_side = {e: [] for e in ['up', 'down', 'left', 'right']}
    for pl in area['point_lm']:
        pls_by_side[pl.attached_to].append(pl)
    for side in pls_by_side:
        pls_by_side[side].sort(key=lambda x: x.t)

    for side in ['up', 'right', 'down', 'left']:
        side2pl = {'left': [], 'right': []}
        for pl in pls_by_side[side]:
            side2pl[pl.side].append(names['pl'][side][pl.t])
            description += f'{names["pl"][side][pl.t].capitalize()} is on {names["loop_ll"][side]} at proportion {pl.t:.2f}. '
        if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
            description += f'All landmarks are on the same side of {names["loop_ll"][side]}. '
        else:
            if len(side2pl['left']) == 1:
                description += f'{side2pl["left"][0].capitalize()} is on one side of {names["loop_ll"][side]}, '
            else:
                description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["loop_ll"][side]}, '
            if len(side2pl['right']) == 1:
                description += f'while {side2pl["right"][0]} is on the other side of {names["loop_ll"][side]}. '
            else:
                description += f'while {", ".join(side2pl["right"])} are on the other side of {names["loop_ll"][side]}. '

    return description.strip()


def generate_route_qa(area, names, qa_num=20):
    qa_pairs = {k: [] for k in range(1, 6)}
    selected_tuples = []
    while sum([len(v) for v in qa_pairs.values()]) < qa_num:
        t = random.randint(1, 5)

        if t == 1:
            # qa type 1: go from pl1 to pl2, where is pl3? pl1, pl2, pl3 are on the same ll
            pls = area['point_lm']
            pl1, pl2, pl3 = random.sample(pls, 3)
            if (pl1, pl2, pl3) not in selected_tuples:
                selected_tuples.append((pl1, pl2, pl3))
                if pl1.attached_to == pl2.attached_to == pl3.attached_to:
                    if pl1.t < pl3.t < pl2.t:
                        qa_pairs[1].append((pl1, pl2, pl3, pl3.side))
                    elif pl2.t < pl3.t < pl1.t:
                        qa_pairs[1].append((pl1, pl2, pl3, ROUTE_OPPOSITE[pl3.side]))
                    elif pl1.t < pl2.t < pl3.t or pl3.t < pl2.t < pl1.t:
                        qa_pairs[1].append((pl1, pl2, pl3, 'front'))
                    elif pl2.t < pl1.t < pl3.t or pl3.t < pl1.t < pl2.t:
                        qa_pairs[1].append((pl1, pl2, pl3, 'back'))

        elif t == 2:
            # qa type 2: go from pl1 to pl2, where is ll? pl1 and pl2 are on the same ll
            pls = area['point_lm']
            lls = area['loop_lm']
            pl1, pl2 = random.sample(pls, 2)
            ll = random.choice(lls)
            if (pl1, pl2, ll) not in selected_tuples:
                selected_tuples.append((pl1, pl2, ll))
                if pl1.attached_to == pl2.attached_to and pl1.attached_to != ll.side:
                    if pl1.attached_to == ROUTE_OPPOSITE[ll.side]:
                        if (names['traverse'] == 'clock' and pl1.t < pl2.t) or (names['traverse'] == 'counterclock' and pl1.t > pl2.t):
                            qa_pairs[2].append((pl1, pl2, ll, 'right'))
                        else:
                            qa_pairs[2].append((pl1, pl2, ll, 'left'))
                    elif pl1.attached_to != ROUTE_OPPOSITE[ll.side]:
                        if names['traverse'] == 'clock':
                            if pl1.t < pl2.t:
                                if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(pl1.attached_to)) % 4 == 1:
                                    qa_pairs[2].append((pl1, pl2, ll, 'front'))
                                else:
                                    qa_pairs[2].append((pl1, pl2, ll, 'back'))
                            else:
                                if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(pl1.attached_to)) % 4 == 1:
                                    qa_pairs[2].append((pl1, pl2, ll, 'back'))
                                else:
                                    qa_pairs[2].append((pl1, pl2, ll, 'front'))
                        else:
                            if pl1.t < pl2.t:
                                if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(pl1.attached_to)) % 4 == 1:
                                    qa_pairs[2].append((pl1, pl2, ll, 'back'))
                                else:
                                    qa_pairs[2].append((pl1, pl2, ll, 'front'))
                            else:
                                if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(pl1.attached_to)) % 4 == 1:
                                    qa_pairs[2].append((pl1, pl2, ll, 'front'))
                                else:
                                    qa_pairs[2].append((pl1, pl2, ll, 'back'))

        elif t == 3:
            # qa type 3: go along ll with pl1 on the left/right, where is pl2? pl1 and pl2 are on the ll
            pls = area['point_lm']
            lls = area['loop_lm']
            ll = random.choice(lls)
            pl1, pl2 = random.sample(pls, 2)
            if (ll, pl1, pl2) not in selected_tuples:
                selected_tuples.append((ll, pl1, pl2))
                if pl1.attached_to == pl2.attached_to and pl1.attached_to == ll.side:
                    direction = random.choice(['left', 'right'])
                    if direction == pl1.side:
                        qa_pairs[3].append((ll, pl1, pl2, direction, pl2.side))
                    else:
                        qa_pairs[3].append((ll, pl1, pl2, direction, ROUTE_OPPOSITE[pl2.side]))

        elif t == 4:
            # qa type 4: go along ll1 with pl on the left/right, where is ll2? pl is on ll1
            pls = area['point_lm']
            lls = area['loop_lm']
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, pl, ll2) not in selected_tuples:
                selected_tuples.append((ll1, pl, ll2))
                if pl.attached_to == ll1.side:
                    if ll1.side == ROUTE_OPPOSITE[ll2.side]:
                        direction = random.choice(['left', 'right'])
                        if (direction == pl.side and names['traverse'] == 'clock') or (direction != pl.side and names['traverse'] == 'counterclock'):
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'right'))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'left'))
                    elif ll1.side != ROUTE_OPPOSITE[ll2.side]:
                        direction = random.choice(['left', 'right'])
                        if (direction == pl.side and names['traverse'] == 'clock') or (direction != pl.side and names['traverse'] == 'counterclock'):
                            if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ll1.side)) % 4 == 1:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                        else:
                            if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ll1.side)) % 4 == 1:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))

        elif t == 5:
            # qa type 5: go along ll1 with ll2 on the left/right/front/back, where is pl? pl is on ll1
            pls = area['point_lm']
            lls = area['loop_lm']
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2, pl) not in selected_tuples:
                selected_tuples.append((ll1, ll2, pl))
                if pl.attached_to == ll1.side:
                    if ll1.side == ROUTE_OPPOSITE[ll2.side]:
                        direction = random.choice(['left', 'right'])
                        if (direction == 'right' and names['traverse'] == 'clock') or (direction == 'left' and names['traverse'] == 'counterclock'):
                            qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                        else:
                            qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                    elif ll1.side != ROUTE_OPPOSITE[ll2.side]:
                        direction = random.choice(['front', 'back'])
                        if names['traverse'] == 'clock':
                            if direction == 'front':
                                if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ll1.side)) % 4 == 1:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                                else:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                            else:
                                if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ll1.side)) % 4 == 1:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                                else:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                        else:
                            if direction == 'front':
                                if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ll1.side)) % 4 == 1:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                                else:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            else:
                                if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ll1.side)) % 4 == 1:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                                else:
                                    qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))

    return {k: [(lm2names(names, p[0]), lm2names(names, p[1]), lm2names(names, p[2])) + p[3:] for p in v] for k, v in qa_pairs.items()}


def generate_survey_qa(area, names, up='north', qa_num=20):
    up_index = SURVEY_DIRECTIONS.index(up)
    if names['direction'] == 'right':
        ori_direction = 2
    elif names['direction'] == 'down':
        ori_direction = 4
    elif names['direction'] == 'left':
        ori_direction = 6
    else:
        ori_direction = 0

    if names['traverse'] == 'clock':
        direction_indices = [ori_direction, (ori_direction + 2) % 8, (ori_direction + 4) % 8, (ori_direction + 6) % 8]
    else:
        direction_indices = [ori_direction, (ori_direction - 2) % 8, (ori_direction - 4) % 8, (ori_direction - 6) % 8]
    edge_order = names['edge_order']

    qa_pairs = {k: [] for k in range(1, 4)}
    selected_pairs = []
    while sum([len(v) for v in qa_pairs.values()]) < qa_num:
        t = random.randint(1, 3)

        if t == 1:
            # qa type 1: ll vs ll
            lls = area['loop_lm']
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2) not in selected_pairs:
                selected_pairs.append((ll1, ll2))
                ll1_to_ll2_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll1.side]) + up_index) % 8]
                qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))

        elif t == 2:
            # qa type 2: pl vs ll
            pls = area['point_lm']
            lls = area['loop_lm']
            pl = random.choice(pls)
            ll = random.choice(lls)
            if (pl, ll) not in selected_pairs:
                selected_pairs.append((pl, ll))
                if pl.attached_to != ll.side:
                    pl_to_ll_dir = SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll.side]) + up_index) % 8]]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                else:
                    cur_direction_index = direction_indices[edge_order.index(ll.side)]
                    if pl.side == 'left':
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(cur_direction_index + up_index - 2) % 8]
                    else:
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(cur_direction_index + up_index + 2) % 8]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))

        elif t == 3:
            # qa type 3: pl vs pl
            pls = area['point_lm']
            pl1, pl2 = random.sample(pls, 2)
            if (pl1, pl2) not in selected_pairs:
                selected_pairs.append((pl1, pl2))
                if pl1.attached_to == pl2.attached_to and pl1.side == pl2.side:  # on the same side of the same ll
                    cur_direction_index = direction_indices[edge_order.index(pl1.attached_to)]
                    if pl1.t > pl2.t:
                        qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(cur_direction_index + up_index) % 8]))
                    else:
                        qa_pairs[3].append((pl1, pl2, SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(cur_direction_index + up_index) % 8]]))
                elif pl1.attached_to != pl2.attached_to:  # on different lls
                    if {pl1.attached_to, pl2.attached_to} == {'left', 'right'} or {pl1.attached_to, pl2.attached_to} == {'up', 'down'}:
                        continue  # this case is not well-defined because we don't know the total length of loop lms
                    else:
                        pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[pl1.attached_to]) + up_index) % 8]}+{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[pl2.attached_to]) + up_index) % 8]]}']
                        qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))

    return {k: [(lm2names(names, lm1), lm2names(names, lm2), dir) for (lm1, lm2, dir) in v] for k, v in qa_pairs.items()}


if __name__ == '__main__':
    f1 = open('../template2_route_train.jsonl', 'w')
    f2 = open('../template2_survey_train.jsonl', 'w')
    n = 1

    for up in ['north', 'east', 'south', 'west']:
        up_index = SURVEY_DIRECTIONS.index(up)
        for _ in range(50):
            area = generate_area()
            names = generate_names(area)
            route_initial = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[names['direction']]) + up_index) % 8]
            symbolic = generate_symbolic(area, names)
            route = generate_route(area, names)
            survey = generate_survey(area, names, up=up)
            route_qa = routeqa2nl(generate_route_qa(area, names))
            survey_qa = surveyqa2nl(generate_survey_qa(area, names, up=up))

            for qa in route_qa:
                data_dict = {'id': n,
                             'up': up,
                             'route_initial': route_initial,
                             'symbolic': symbolic,
                             'route': route,
                             'survey': survey,
                             'question': qa[0],
                             'answer': qa[1]}
                print(json.dumps(data_dict), file=f1)

            for qa in survey_qa:
                data_dict = {'id': n,
                             'up': up,
                             'route_initial': route_initial,
                             'symbolic': symbolic,
                             'route': route,
                             'survey': survey,
                             'question': qa[0],
                             'answer': qa[1]}
                print(json.dumps(data_dict), file=f2)

            n += 1

    f1.close()
    f2.close()
