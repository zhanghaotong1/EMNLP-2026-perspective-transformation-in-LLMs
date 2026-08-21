import json
from dataclasses import dataclass
from typing import Literal
from utils import *


@dataclass
class CentralLM:
    id: str


@dataclass
class BranchLM:
    id: str
    side: Literal['up', 'down', 'left', 'right']


@dataclass
class PointLM:
    id: str
    attached_to: Literal['up', 'down', 'left', 'right']
    t: float
    side: Literal["left", "right"]


def generate_area(
        min_branch_pl=3,
        max_branch_pl=5,
):
    area = {}

    # generate central linear landmark
    area['central_lm'] = CentralLM(id="central")

    # generate four branch linear landmarks
    area['branch_ll'] = [BranchLM(id=f'branch_{i}', side=d) for i, d in enumerate(['up', 'down', 'left', 'right'])]

    # randomly generate point landmarks on branch linear landmarks
    pls = []
    for i, d in enumerate(['up', 'down', 'left', 'right']):
        n_pl = random.randint(min_branch_pl, max_branch_pl)
        ts = [random.uniform(0.05, 0.95) for _ in range(n_pl)]
        ts.sort()
        for j, t in enumerate(ts):
            pls.append(
                PointLM(
                    id=f'branch_{i}_pl_{j}',
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

    branch_names = random.sample(WORDS_DICT['name'], 4)
    branch_ll = {
        'up': branch_names[0] + ' ' + random.choice(WORDS_DICT['linear_ll1']),
        'down': branch_names[1] + ' ' + random.choice(WORDS_DICT['linear_ll1']),
        'left': branch_names[2] + ' ' + random.choice(WORDS_DICT['linear_ll1']),
        'right': branch_names[3] + ' ' + random.choice(WORDS_DICT['linear_ll1']),
    }

    central_lm = random.choice(WORDS_DICT['name']) + ' ' + random.choice(['Square', 'Plaza'])

    pl_names = random.sample(WORDS_DICT['point_ll'], len(area['point_lm']))
    pl_names_dict = {'up': {}, 'down': {}, 'left': {}, 'right': {}}
    for i, pl in enumerate(area['point_lm']):
        pl_names_dict[pl.attached_to][pl.t] = pl_names[i]

    names = {
        'transport': transport,
        'transporting': transporting,
        'proportion': proportion,
        'distance': distance,
        'branch_ll': branch_ll,
        'central_lm': central_lm,
        'pl': pl_names_dict,
    }

    return names


def lm2names(names, lm):
    if isinstance(lm, BranchLM):
        return names['branch_ll'][lm.side]
    else:
        return names['pl'][lm.attached_to][lm.t]


def generate_route(area, names):
    transport = names['transport']
    proportion = names['proportion']
    distance = names['distance']

    pl_names = names['pl']
    branch_ll = names['branch_ll']
    central_ll = names['central_lm']

    pls_by_edge = {d: [] for d in ['up', 'down', 'left', 'right']}
    for pl in area['point_lm']:
        pls_by_edge[pl.attached_to].append(pl)
    for edge in pls_by_edge:
        pls_by_edge[edge].sort(key=lambda x: x.t)

    description = (f'You arrive at {central_ll}. Standing at the centre of {central_ll} and facing {branch_ll["up"]}, '
                   f'{branch_ll["left"]} will be on your left, {branch_ll["right"]} will be on your right and '
                   f'{branch_ll["down"]} will be on your back. ')

    for direction in ['up', 'down', 'left', 'right']:
        description += f'{transport.capitalize()} onto {branch_ll[direction]}. '
        cur_t = 0
        for pl in pls_by_edge[direction]:
            description += (
                f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                f'{pl_names[direction][pl.t]} on your {pl.side}. '
            )
            cur_t = pl.t
        description += f'Return back along {branch_ll[direction]} to {central_ll}. '

    description += f'You finish your exploration at {central_ll} area.'

    return description


def generate_survey(area, names, up='north'):
    up_index = SURVEY_DIRECTIONS.index(up)

    def get_left_right_dirs(orientation_idx):
        left = SURVEY_DIRECTIONS[(orientation_idx - 2) % 8]
        right = SURVEY_DIRECTIONS[(orientation_idx + 2) % 8]
        return left, right

    transport = names['transport']
    proportion = names['proportion']
    distance = names['distance']

    pl_names = names['pl']
    branch_ll = names['branch_ll']
    central_ll = names['central_lm']

    pls_by_edge = {d: [] for d in ['up', 'down', 'left', 'right']}
    for pl in area['point_lm']:
        pls_by_edge[pl.attached_to].append(pl)
    for edge in pls_by_edge:
        pls_by_edge[edge].sort(key=lambda x: x.t)

    description = (f'You arrive at {central_ll}. Extending from it are four roads: {branch_ll["up"]} to the '
                   f'{SURVEY_DIRECTIONS[up_index]}, {branch_ll["down"]} to the {SURVEY_DIRECTIONS[(up_index + 4) % 8]}, '
                   f'{branch_ll["left"]} to the {SURVEY_DIRECTIONS[(up_index + 6) % 8]}, and {branch_ll["right"]} to '
                   f'the {SURVEY_DIRECTIONS[(up_index + 2) % 8]}. ')

    for direction in ['up', 'down', 'left', 'right']:
        if direction == 'up':
            orientation_idx = up_index
        elif direction == 'down':
            orientation_idx = (up_index + 4) % 8
        elif direction == 'left':
            orientation_idx = (up_index + 6) % 8
        else:
            orientation_idx = (up_index + 2) % 8

        left_dir, right_dir = get_left_right_dirs(orientation_idx)

        description += f'From {central_ll}, you head {SURVEY_DIRECTIONS[orientation_idx]} along {branch_ll[direction]}. '

        cur_t = 0
        for pl in pls_by_edge[direction]:
            side_dir = left_dir if pl.side == 'left' else right_dir
            description += (
                f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                f'{pl_names[direction][pl.t]} on the {side_dir}. '
            )
            cur_t = pl.t

        description += f'You then return along {branch_ll[direction]} to {central_ll}. '

    description += f'You finish your exploration at {central_ll} area.'

    return description


def generate_symbolic(area, names):
    boundary_side2name = {}
    for b in area['branch_ll']:
        boundary_side2name[b.side] = names['branch_ll'][b.side]

    description = (f'There are four roads around {names["central_lm"]}: {boundary_side2name["up"]}, {boundary_side2name["right"]}, '
                   f'{boundary_side2name["down"]} and {boundary_side2name["left"]}, arranged clockwise. All roads '
                   f'radiate outwards from the center. ')

    pls_by_side = {d: [] for d in ['up', 'down', 'left', 'right']}
    for pl in area['point_lm']:
        pls_by_side[pl.attached_to].append(pl)
    for side in pls_by_side:
        pls_by_side[side].sort(key=lambda x: x.t)

    for side in ['up', 'right', 'down', 'left']:
        side2pl = {'left': [], 'right': []}
        for pl in pls_by_side[side]:
            side2pl[pl.side].append(names['pl'][side][pl.t])
            description += f'{names["pl"][side][pl.t].capitalize()} is on {names["branch_ll"][side]} at proportion {pl.t:.2f}. '
        if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
            description += f'All landmarks are on the same side of {names["branch_ll"][side]}. '
        else:
            if len(side2pl['left']) == 1:
                description += f'{side2pl["left"][0].capitalize()} is on one side of {names["branch_ll"][side]}, '
            else:
                description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["branch_ll"][side]}, '
            if len(side2pl['right']) == 1:
                description += f'while {side2pl["right"][0]} is on the other side of {names["branch_ll"][side]}. '
            else:
                description += f'while {", ".join(side2pl["right"])} are on the other side of {names["branch_ll"][side]}. '

    return description.strip()


def generate_route_qa(area, qa_num=20):
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
            lls = area['branch_ll']
            pl1, pl2 = random.sample(pls, 2)
            ll = random.choice(lls)
            if (pl1, pl2, ll) not in selected_tuples:
                selected_tuples.append((pl1, pl2, ll))
                if pl1.attached_to == pl2.attached_to and pl1.attached_to == ROUTE_OPPOSITE[ll.side]:
                    if pl1.t < pl2.t:
                        qa_pairs[2].append((pl1, pl2, ll, 'back'))
                    else:
                        qa_pairs[2].append((pl1, pl2, ll, 'front'))

        elif t == 3:
            # qa type 3: go along ll with pl1 on the left/right, where is pl2? pl1 and pl2 are on the ll
            pls = area['point_lm']
            lls = area['branch_ll']
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
            lls = area['branch_ll']
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, pl, ll2) not in selected_tuples:
                selected_tuples.append((ll1, pl, ll2))
                if pl.attached_to == ll1.side and ll1.side == ROUTE_OPPOSITE[ll2.side]:
                    direction = random.choice(['left', 'right'])
                    if direction == pl.side:
                        qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                    else:
                        qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))

        elif t == 5:
            # qa type 5: go along ll1 with ll2 on the front/back, where is pl? pl is on ll1
            pls = area['point_lm']
            lls = area['branch_ll']
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2, pl) not in selected_tuples:
                selected_tuples.append((ll1, ll2, pl))
                if pl.attached_to == ll1.side and ll1.side == ROUTE_OPPOSITE[ll2.side]:
                    direction = random.choice(['front', 'back'])
                    if direction == 'back':
                        qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                    else:
                        qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))

    return {k: [(lm2names(names, p[0]), lm2names(names, p[1]), lm2names(names, p[2])) + p[3:] for p in v] for k, v in qa_pairs.items()}


def generate_survey_qa(area, names, up='north', qa_num=20):
    up_index = SURVEY_DIRECTIONS.index(up)

    qa_pairs = {k: [] for k in range(1, 4)}
    selected_pairs = []
    while sum([len(v) for v in qa_pairs.values()]) < qa_num:
        t = random.randint(1, 3)

        if t == 1:
            # qa type 1: ll vs ll
            lls = area['branch_ll']
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2) not in selected_pairs:
                selected_pairs.append((ll1, ll2))
                ll1_to_ll2_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll1.side]) + up_index) % 8]
                qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))

        elif t == 2:
            # qa type 2: pl vs ll
            pls = area['point_lm']
            lls = area['branch_ll']
            pl = random.choice(pls)
            ll = random.choice(lls)
            if (pl, ll) not in selected_pairs:
                selected_pairs.append((pl, ll))
                if pl.attached_to == ll.side:
                    cur_direction_index = SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll.side])
                    if pl.side == 'left':
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(cur_direction_index + up_index - 2) % 8]
                    else:
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(cur_direction_index + up_index + 2) % 8]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                else:
                    pl_to_ll_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[pl.attached_to]) + up_index) % 8]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))

        elif t == 3:
            # qa type 3: pl vs pl
            pls = area['point_lm']
            pl1, pl2 = random.sample(pls, 2)
            if (pl1, pl2) not in selected_pairs:
                selected_pairs.append((pl1, pl2))
                if pl1.attached_to == pl2.attached_to and pl1.side == pl2.side:  # on the same side of the same ll
                    cur_direction_index = (SURVEY_DIRECTIONS.index(ROUTE2SURVEY[pl1.attached_to]) + up_index) % 8
                    if pl1.t < pl2.t:
                        pl1_to_pl2_dir = SURVEY_OPPOSITE[SURVEY_DIRECTIONS[cur_direction_index]]
                    else:
                        pl1_to_pl2_dir = SURVEY_DIRECTIONS[cur_direction_index]
                    qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                elif pl1.attached_to != pl2.attached_to:  # on different lls
                    if ({pl1.attached_to, pl2.attached_to} in [{'up', 'down'}, {'left', 'right'}]) and pl1.side != pl2.side:
                        if pl1.attached_to == 'up':
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(up_index) % 8]))
                        elif pl1.attached_to == 'down':
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(4 + up_index) % 8]))
                        elif pl1.attached_to == 'left':
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(6 + up_index) % 8]))
                        elif pl1.attached_to == 'right':
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(2 + up_index) % 8]))
                    elif {pl1.attached_to, pl2.attached_to} not in [{'up', 'down'}, {'left', 'right'}]:
                        pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[pl1.attached_to]) + up_index) % 8]}+{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[pl2.attached_to]) + up_index) % 8]]}']
                        qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))

    return {k: [(lm2names(names, lm1), lm2names(names, lm2), dir) for (lm1, lm2, dir) in v] for k, v in qa_pairs.items()}


if __name__ == '__main__':
    f1 = open('../template4_route_train.jsonl', 'w')
    f2 = open('../template4_survey_train.jsonl', 'w')
    n = 1

    for up in ['north', 'east', 'south', 'west']:
        up_index = SURVEY_DIRECTIONS.index(up)
        for _ in range(50):
            area = generate_area()
            names = generate_names(area)
            symbolic = generate_symbolic(area, names)
            route = generate_route(area, names)
            survey = generate_survey(area, names, up=up)
            route_qa = routeqa2nl(generate_route_qa(area))
            survey_qa = surveyqa2nl(generate_survey_qa(area, names, up=up))

            for qa in route_qa:
                data_dict = {'id': n,
                             'up': up,
                             'route_initial': up,
                             'symbolic': symbolic,
                             'route': route,
                             'survey': survey,
                             'question': qa[0],
                             'answer': qa[1]}
                print(json.dumps(data_dict), file=f1)

            for qa in survey_qa:
                data_dict = {'id': n,
                             'up': up,
                             'route_initial': up,
                             'symbolic': symbolic,
                             'route': route,
                             'survey': survey,
                             'question': qa[0],
                             'answer': qa[1]}
                print(json.dumps(data_dict), file=f2)

            n += 1

    f1.close()
    f2.close()
