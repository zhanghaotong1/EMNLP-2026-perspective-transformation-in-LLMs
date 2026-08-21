import json
from dataclasses import dataclass
from typing import Literal
from utils import *


@dataclass
class MainLM:
    id: str
    side: Literal['up', 'down', 'left', 'right']


@dataclass
class BoundaryLM:
    id: str
    side: Literal['up', 'down', 'left', 'right']


@dataclass
class SecondaryLoop:
    id: str
    entry_t: float
    exit_t: float


@dataclass
class PointLM:
    id: str
    attached_to: Literal['main', 'sec_entry', 'sec_inner', 'sec_exit']
    t: float
    side: Literal['left', 'right']


def generate_area(
        min_main_pl=3,
        max_main_pl=6,
        min_sec_pl=1,
        max_sec_pl=3,
        sec_entry=(0.1, 0.4),
        sec_exit=(0.6, 0.9),
):
    area = {}

    # randomly choose a boundary linear landmark as the main linear landmark
    main_ll_side = random.choice(['up', 'down', 'left', 'right'])
    main_ll = MainLM(id='main_0', side=main_ll_side)
    area['main_ll'] = main_ll

    boundaries = []
    boundary_ll_sides = list({'up', 'down', 'left', 'right'} - {main_ll_side})
    for i, b in enumerate(boundary_ll_sides):
        boundaries.append(BoundaryLM(id=f'boundary_{i}', side=b))
    area['boundary_ll'] = boundaries

    # initiate a secondary linear landmark
    sec_entry_t = random.uniform(sec_entry[0], sec_entry[1])
    sec_exit_t = random.uniform(sec_exit[0], sec_exit[1])
    secondary_ll = SecondaryLoop(id='secondary_0', entry_t=sec_entry_t, exit_t=sec_exit_t)
    area['secondary_ll'] = secondary_ll
    area['secondary_exit_t'] = sec_exit_t

    # randomly generate point landmarks along main linear landmark
    n_main_pl = random.randint(min_main_pl, max_main_pl)
    n_pl = n_main_pl
    main_ts1, main_ts2 = [], []
    while len(main_ts1) + len(main_ts2) < n_main_pl:
        t = random.uniform(0.05, 0.95)
        if t < sec_entry_t:
            main_ts1.append(t)
        elif t > sec_exit_t:
            main_ts2.append(t)
    main_ts1.sort()
    main_ts2.sort()

    main_pls1 = []
    for i, t in enumerate(main_ts1):
        main_pls1.append(
            PointLM(
                id=f'main_pl_{i}',
                attached_to='main',
                t=t,
                side=random.choice(['left', 'right']),
            )
        )
    area['main_pl1'] = main_pls1

    main_pls2 = []
    for i, t in enumerate(main_ts2):
        main_pls2.append(
            PointLM(
                id=f'main_pl_{i}',
                attached_to='main',
                t=t,
                side=random.choice(['left', 'right']),
            )
        )
    area['main_pl2'] = main_pls2

    # randomly generate point landmarks along secondary linear landmark
    for d in ['sec_entry', 'sec_inner', 'sec_exit']:
        n_sec_pl = random.randint(min_sec_pl, max_sec_pl)
        n_pl += n_sec_pl
        sec_pls = []
        ts = [random.uniform(0.05, 0.95) for _ in range(n_sec_pl)]
        ts.sort()
        for i, t in enumerate(ts):
            sec_pls.append(
                PointLM(
                    id=f'{d}_pl_{i}',
                    attached_to=d,
                    t=t,
                    side=random.choice(['left', 'right']),
                )
            )
        area[f'{d}_pl'] = sec_pls

    area['n_pl'] = n_pl

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

    ll_names = random.sample(WORDS_DICT['name'], 7)
    main_ll_name = ll_names[0] + ' ' + random.choice(WORDS_DICT['linear_ll1'])
    secondary_ll_names = [ll_names[1 + i] + ' ' + random.choice(WORDS_DICT['linear_ll1']) for i in range(3)]
    boundary_ll_names = [ll_names[4 + i] + ' ' + random.choice(WORDS_DICT['linear_ll1'] + WORDS_DICT['linear_ll2']) for
                         i in range(3)]
    boundary_ll_names = {ll.side: boundary_ll_names[i] for i, ll in enumerate(area['boundary_ll'])}

    pl_names = random.sample(WORDS_DICT['point_ll'], area['n_pl'])
    pl_names_dict = {}
    n = 0
    for ll in ['main_pl1', 'sec_entry_pl', 'sec_inner_pl', 'sec_exit_pl', 'main_pl2']:
        pl_names_dict[ll] = {pl.t: pl_names[i + n] for i, pl in enumerate(area[ll])}
        n += len(area[ll])

    # determine the entrance of main linear landmark
    main_ll_side = area['main_ll'].side
    if main_ll_side in ['left', 'right']:
        entrances = ['up', 'down']
    else:
        entrances = ['left', 'right']
    entrance = entrances[0] if random.random() < 0.5 else entrances[1]

    if (main_ll_side, entrance) in [('left', 'up'), ('down', 'left'), ('right', 'down'), ('up', 'right')]:
        turns = ['left', 'right', 'right', 'left']
    else:
        turns = ['right', 'left', 'left', 'right']

    names = {'transport': transport,
             'transporting': transporting,
             'proportion': proportion,
             'distance': distance,
             'main_ll': main_ll_name,
             'secondary_ll': secondary_ll_names,
             'boundary_ll': boundary_ll_names,
             'pl': pl_names_dict,
             'town_name': random.choice(WORDS_DICT['name']),
             'turns': turns,
             'entrance': entrance}

    return names


def lm2names(area, names, lm):
    pl_names = names['pl']
    if isinstance(lm, MainLM):
        return names['main_ll']
    elif isinstance(lm, BoundaryLM):
        return names['boundary_ll'][lm.side]
    elif lm in ['sec_entry', 'sec_inner', 'sec_exit']:
        return names['secondary_ll'][['sec_entry', 'sec_inner', 'sec_exit'].index(lm)]
    elif isinstance(lm, PointLM):
        if lm.attached_to == 'main' and lm.t < area['secondary_ll'].entry_t:
            return pl_names['main_pl1'][lm.t]
        elif lm.attached_to == 'main' and lm.t > area['secondary_ll'].exit_t:
            return pl_names['main_pl2'][lm.t]
        else:
            return pl_names[f'{lm.attached_to}_pl'][lm.t]


def generate_route(area, names):
    transport = names['transport']
    transporting = names['transporting']
    proportion = names['proportion']
    distance = names['distance']
    turns = names['turns']

    main_ll_name = names['main_ll']
    secondary_ll_names = names['secondary_ll']
    boundary_ll_names = names['boundary_ll']
    pl_names = names['pl']

    main_ll_side = area['main_ll'].side
    if names['entrance'] == 'down':
        boundary_order = ['down', 'up', list({'left', 'right'} - {main_ll_side})[0]]
    elif names['entrance'] == 'up':
        boundary_order = ['up', 'down', list({'left', 'right'} - {main_ll_side})[0]]
    elif names['entrance'] == 'left':
        boundary_order = ['left', 'right', list({'up', 'down'} - {main_ll_side})[0]]
    else:
        boundary_order = ['right', 'left', list({'up', 'down'} - {main_ll_side})[0]]

    description = (f'You enter {names["town_name"]} Town through {main_ll_name}. At this point, you see '
                   f'{boundary_ll_names[boundary_order[0]]} on your {turns[0]}, intersecting with {main_ll_name}. '
                   f'{transport.capitalize()} along {main_ll_name}. ')

    cur_t = 0
    for pl in area['main_pl1']:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main_pl1"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (f'You continue {transporting} on {main_ll_name} and come to, on your {turns[0]}, '
                    f'{secondary_ll_names[0]}. Turning {turns[0]} onto {secondary_ll_names[0]}. ')

    cur_t = 0
    for pl in area['sec_entry_pl']:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["sec_entry_pl"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (
        f'Continue {transporting} on {secondary_ll_names[0]} until you are forced to make a {turns[1]} turn. '
        f'Turning {turns[1]} onto {secondary_ll_names[1]}. ')

    cur_t = 0
    for pl in area['sec_inner_pl']:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["sec_inner_pl"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (f'Continue {transporting} along {secondary_ll_names[1]} until you are again forced to make a '
                    f'{turns[2]} turn. Turning {turns[2]} onto {secondary_ll_names[2]}. ')

    cur_t = 0
    for pl in area['sec_exit_pl']:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["sec_exit_pl"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (f'Continue {transporting} along {secondary_ll_names[2]} until you meet a dead-end into '
                    f'{main_ll_name}. Turn {turns[3]} onto {main_ll_name}. ')

    cur_t = area['secondary_exit_t']
    for pl in area['main_pl2']:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main_pl2"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (
        f'You {transport} along {main_ll_name} until you see {boundary_ll_names[boundary_order[1]]} on your '
        f'{turns[0]}, intersecting with the one you are on. ')
    description += f'{boundary_ll_names[boundary_order[2]]} runs parallel to your far {turns[0]}, on the other side of the town.'

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
    turns = names['turns']

    main_ll_name = names['main_ll']
    secondary_ll_names = names['secondary_ll']
    boundary_ll_names = names['boundary_ll']
    pl_names = names['pl']

    if names['entrance'] == 'down':
        current_orientation_index = up_index
    elif names['entrance'] == 'up':
        current_orientation_index = (4 + up_index) % 8
    elif names['entrance'] == 'left':
        current_orientation_index = (2 + up_index) % 8
    else:
        current_orientation_index = (6 + up_index) % 8

    description = (f'{names["town_name"]} Town is surrounded by four major landmarks: {main_ll_name}, '
                   f'{list(boundary_ll_names.values())[0]}, {list(boundary_ll_names.values())[1]} and '
                   f'{list(boundary_ll_names.values())[2]}. ')
    for ll, name in zip([area['main_ll']] + area['boundary_ll'], [main_ll_name] + list(boundary_ll_names.values())):
        description += f'The {new_sides[ll.side][0]} is made up of the {name}, running {new_sides[ll.side][1]}-{new_sides[ll.side][2]}. '

    description += (f'You enter the town through {main_ll_name}. {transport.capitalize()} '
                    f'{SURVEY_DIRECTIONS[current_orientation_index]} along {main_ll_name}. ')

    cur_t = 0
    for pl in area['main_pl1']:
        if pl.side == 'left':
            pl_orientation_index = (current_orientation_index - 2) % 8
        else:
            pl_orientation_index = (current_orientation_index + 2) % 8
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main_pl1"][pl.t]} on the {SURVEY_DIRECTIONS[pl_orientation_index]}. ')
        cur_t = pl.t

    if turns[0] == 'left':
        current_orientation_index = (current_orientation_index - 2) % 8
    else:
        current_orientation_index = (current_orientation_index + 2) % 8
    description += (
        f'You continue {transporting} on {main_ll_name} and come to, on the {SURVEY_DIRECTIONS[current_orientation_index]}, '
        f'{secondary_ll_names[0]}. Turning {SURVEY_DIRECTIONS[current_orientation_index]} onto {secondary_ll_names[0]}. ')

    cur_t = 0
    for pl in area['sec_entry_pl']:
        if pl.side == 'left':
            pl_orientation_index = (current_orientation_index - 2) % 8
        else:
            pl_orientation_index = (current_orientation_index + 2) % 8
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["sec_entry_pl"][pl.t]} on the {SURVEY_DIRECTIONS[pl_orientation_index]}. ')
        cur_t = pl.t

    if turns[1] == 'left':
        current_orientation_index = (current_orientation_index - 2) % 8
    else:
        current_orientation_index = (current_orientation_index + 2) % 8
    description += (f'Continue {transporting} on {secondary_ll_names[0]} until you are forced to make a turn to the '
                    f'{SURVEY_DIRECTIONS[current_orientation_index]}. Turning {SURVEY_DIRECTIONS[current_orientation_index]}'
                    f' onto {secondary_ll_names[1]}. ')

    cur_t = 0
    for pl in area['sec_inner_pl']:
        if pl.side == 'left':
            pl_orientation_index = (current_orientation_index - 2) % 8
        else:
            pl_orientation_index = (current_orientation_index + 2) % 8
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["sec_inner_pl"][pl.t]} on the {SURVEY_DIRECTIONS[pl_orientation_index]}. ')
        cur_t = pl.t

    if turns[2] == 'left':
        current_orientation_index = (current_orientation_index - 2) % 8
    else:
        current_orientation_index = (current_orientation_index + 2) % 8
    description += (f'Continue {transporting} along {secondary_ll_names[1]} until you are again forced to make a turn '
                    f'to the {SURVEY_DIRECTIONS[current_orientation_index]}. Turning {SURVEY_DIRECTIONS[current_orientation_index]}'
                    f' onto {secondary_ll_names[2]}. ')

    cur_t = 0
    for pl in area['sec_exit_pl']:
        if pl.side == 'left':
            pl_orientation_index = (current_orientation_index - 2) % 8
        else:
            pl_orientation_index = (current_orientation_index + 2) % 8
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["sec_exit_pl"][pl.t]} on the {SURVEY_DIRECTIONS[pl_orientation_index]}. ')
        cur_t = pl.t

    if turns[3] == 'left':
        current_orientation_index = (current_orientation_index - 2) % 8
    else:
        current_orientation_index = (current_orientation_index + 2) % 8
    description += (f'Continue {transporting} along {secondary_ll_names[2]} until you meet a dead-end into '
                    f'{main_ll_name}. Turn {SURVEY_DIRECTIONS[current_orientation_index]} onto {main_ll_name}. ')

    cur_t = area['secondary_exit_t']
    for pl in area['main_pl2']:
        if pl.side == 'left':
            pl_orientation_index = (current_orientation_index - 2) % 8
        else:
            pl_orientation_index = (current_orientation_index + 2) % 8
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main_pl2"][pl.t]} on the {SURVEY_DIRECTIONS[pl_orientation_index]}. ')
        cur_t = pl.t

    description += (f'Continue {transporting} {SURVEY_DIRECTIONS[current_orientation_index]} along {main_ll_name} and '
                    f'you leave the town.')

    return description


def generate_symbolic(area, names):
    boundary_side2name = {area['main_ll'].side: names['main_ll']}
    for b in area['boundary_ll']:
        boundary_side2name[b.side] = names['boundary_ll'][b.side]

    description = (f'{names["town_name"]} Town is surrounded by {boundary_side2name["up"]}, {boundary_side2name["right"]}, '
                   f'{boundary_side2name["down"]} and {boundary_side2name["left"]}, arranged clockwise. '
                   f'{names["secondary_ll"][0]}, {names["secondary_ll"][1]} and {names["secondary_ll"][2]} are connected '
                   f'to {names["main_ll"]} in a U-shape, where {names["secondary_ll"][0]} and {names["secondary_ll"][2]} '
                   f'are perpendicular to {names["main_ll"]} and {names["secondary_ll"][1]} is parallel to {names["main_ll"]}. '
                   f'{names["secondary_ll"][0]} intersects {names["main_ll"]} at proportion {area["secondary_ll"].entry_t:.2f}'
                   f' while {names["secondary_ll"][2]} intersects {names["main_ll"]} at proportion {area["secondary_ll"].exit_t:.2f}. ')

    side2pl = {'left': [], 'right': []}
    for pl in area['main_pl1']:
        side2pl[pl.side].append(names['pl']['main_pl1'][pl.t])
        description += f'{names["pl"]["main_pl1"][pl.t].capitalize()} is on {names["main_ll"]} at proportion {pl.t:.2f}. '
    for pl in area['main_pl2']:
        side2pl[pl.side].append(names['pl']['main_pl2'][pl.t])
        description += f'{names["pl"]["main_pl2"][pl.t].capitalize()} is on {names["main_ll"]} at proportion {pl.t:.2f}. '
    if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
        description += f'All landmarks are on the same side of {names["main_ll"]}. '
    else:
        if len(side2pl['left']) == 1:
            description += f'{side2pl["left"][0].capitalize()} is on one side of {names["main_ll"]}, '
        else:
            description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["main_ll"]}, '
        if len(side2pl['right']) == 1:
            description += f'while {side2pl["right"][0]} is on the other side of {names["main_ll"]}. '
        else:
            description += f'while {", ".join(side2pl["right"])} are on the other side of {names["main_ll"]}. '

    side2pl = {'left': [], 'right': []}
    for pl in area['sec_entry_pl']:
        side2pl[pl.side].append(names['pl']['sec_entry_pl'][pl.t])
        description += f'{names["pl"]["sec_entry_pl"][pl.t].capitalize()} is on {names["secondary_ll"][0]} at proportion {pl.t:.2f}. '
    if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
        description += f'All landmarks are on the same side of {names["secondary_ll"][0]}. '
    else:
        if len(side2pl['left']) == 1:
            description += f'{side2pl["left"][0].capitalize()} is on one side of {names["secondary_ll"][0]}, '
        else:
            description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["secondary_ll"][0]}, '
        if len(side2pl['right']) == 1:
            description += f'while {side2pl["right"][0]} is on the other side of {names["secondary_ll"][0]}. '
        else:
            description += f'while {", ".join(side2pl["right"])} are on the other side of {names["secondary_ll"][0]}. '

    side2pl = {'left': [], 'right': []}
    for pl in area['sec_inner_pl']:
        side2pl[pl.side].append(names['pl']['sec_inner_pl'][pl.t])
        description += f'{names["pl"]["sec_inner_pl"][pl.t].capitalize()} is on {names["secondary_ll"][1]} at proportion {pl.t:.2f}. '
    if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
        description += f'All landmarks are on the same side of {names["secondary_ll"][1]}. '
    else:
        if len(side2pl['left']) == 1:
            description += f'{side2pl["left"][0].capitalize()} is on one side of {names["secondary_ll"][1]}, '
        else:
            description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["secondary_ll"][1]}, '
        if len(side2pl['right']) == 1:
            description += f'while {side2pl["right"][0]} is on the other side of {names["secondary_ll"][1]}. '
        else:
            description += f'while {", ".join(side2pl["right"])} are on the other side of {names["secondary_ll"][1]}. '

    side2pl = {'left': [], 'right': []}
    for pl in area['sec_exit_pl']:
        side2pl[pl.side].append(names['pl']['sec_exit_pl'][pl.t])
        description += f'{names["pl"]["sec_exit_pl"][pl.t].capitalize()} is on {names["secondary_ll"][2]} at proportion {pl.t:.2f}. '
    if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
        description += f'All landmarks are on the same side of {names["secondary_ll"][2]}.'
    else:
        if len(side2pl['left']) == 1:
            description += f'{side2pl["left"][0].capitalize()} is on one side of {names["secondary_ll"][2]}, '
        else:
            description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["secondary_ll"][2]}, '
        if len(side2pl['right']) == 1:
            description += f'while {side2pl["right"][0]} is on the other side of {names["secondary_ll"][2]}.'
        else:
            description += f'while {", ".join(side2pl["right"])} are on the other side of {names["secondary_ll"][2]}.'

    return description


def generate_route_qa(area, names, qa_num=20):
    qa_pairs = {k: [] for k in range(1, 6)}
    selected_tuples = []
    while sum([len(v) for v in qa_pairs.values()]) < qa_num:
        t = random.randint(1, 5)

        if t == 1:
            # qa type 1: go from pl1 to pl2, where is pl3? pl1, pl2, pl3 are on the same ll
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
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
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
            lls = area['boundary_ll'] + [area['main_ll']] + ['sec_entry', 'sec_inner', 'sec_exit']
            pl1, pl2 = random.sample(pls, 2)
            ll = random.choice(lls)
            if (pl1, pl2, ll) not in selected_tuples:
                selected_tuples.append((pl1, pl2, ll))
                if pl1.attached_to == pl2.attached_to:
                    if pl1.attached_to == 'main' and (ll == 'sec_inner' or (isinstance(ll, BoundaryLM) and ll.side == ROUTE_OPPOSITE[area['main_ll'].side])):
                        if pl1.t < pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, names['turns'][0]))
                        else:
                            qa_pairs[2].append((pl1, pl2, ll, ROUTE_OPPOSITE[names['turns'][0]]))
                    elif pl1.attached_to == 'sec_inner' and isinstance(ll, MainLM):
                        if pl1.t < pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, ROUTE_OPPOSITE[names['turns'][0]]))
                        else:
                            qa_pairs[2].append((pl1, pl2, ll, names['turns'][0]))
                    elif pl1.attached_to == 'sec_inner' and (isinstance(ll, BoundaryLM) and ll.side == ROUTE_OPPOSITE[area['main_ll'].side]):
                        if pl1.t < pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, names['turns'][0]))
                        else:
                            qa_pairs[2].append((pl1, pl2, ll, ROUTE_OPPOSITE[names['turns'][0]]))
                    elif (pl1.attached_to == 'sec_entry' and ll == 'sec_exit') or (pl1.attached_to == 'sec_exit' and ll == 'sec_entry'):
                        if pl1.t < pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, names['turns'][1]))
                        else:
                            qa_pairs[2].append((pl1, pl2, ll, ROUTE_OPPOSITE[names['turns'][1]]))
                    elif pl1.attached_to == 'sec_entry' and isinstance(ll, BoundaryLM) and ll.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                        if pl1.t < pl2.t:
                            if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[2].append((pl1, pl2, ll, 'left'))
                            else:
                                qa_pairs[2].append((pl1, pl2, ll, 'right'))
                        else:
                            if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[2].append((pl1, pl2, ll, 'left'))
                            else:
                                qa_pairs[2].append((pl1, pl2, ll, 'right'))
                    elif pl1.attached_to == 'sec_exit' and isinstance(ll, BoundaryLM) and ll.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                        if pl1.t < pl2.t:
                            if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[2].append((pl1, pl2, ll, 'left'))
                            else:
                                qa_pairs[2].append((pl1, pl2, ll, 'right'))
                        else:
                            if (ROUTE_DIRECTIONS.index(ll.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[2].append((pl1, pl2, ll, 'left'))
                            else:
                                qa_pairs[2].append((pl1, pl2, ll, 'right'))

        elif t == 3:
            # qa type 3: go along ll with pl1 on the left/right, where is pl2? pl1 and pl2 are on the ll
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
            lls = area['boundary_ll'] + [area['main_ll']] + ['sec_entry', 'sec_inner', 'sec_exit']
            ll = random.choice(lls)
            pl1, pl2 = random.sample(pls, 2)
            if (ll, pl1, pl2) not in selected_tuples:
                selected_tuples.append((ll, pl1, pl2))
                if pl1.attached_to == pl2.attached_to and ((pl1.attached_to == 'main' and isinstance(ll, MainLM)) or pl1.attached_to == ll):
                    direction = random.choice(['left', 'right'])
                    if direction == pl1.side:
                        qa_pairs[3].append((ll, pl1, pl2, direction, pl2.side))
                    else:
                        qa_pairs[3].append((ll, pl1, pl2, direction, ROUTE_OPPOSITE[pl2.side]))

        elif t == 4:
            # qa type 4: go along ll1 with pl on the left/right, where is ll2? pl is on ll1
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
            lls = area['boundary_ll'] + [area['main_ll']] + ['sec_entry', 'sec_inner', 'sec_exit']
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, pl, ll2) not in selected_tuples:
                selected_tuples.append((ll1, pl, ll2))
                if pl.attached_to == 'main' and isinstance(ll1, MainLM) and (ll2 in ['sec_entry', 'sec_inner', 'sec_exit'] or (isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side])):
                    direction = random.choice(['left', 'right'])
                    if direction == pl.side:
                        qa_pairs[4].append((ll1, pl, ll2, direction, names['turns'][0]))
                    else:
                        qa_pairs[4].append((ll1, pl, ll2, direction, ROUTE_OPPOSITE[names['turns'][0]]))
                elif pl.attached_to == 'sec_inner' and ll1 == 'sec_inner':
                    if isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side]:
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            qa_pairs[4].append((ll1, pl, ll2, direction, names['turns'][0]))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, ROUTE_OPPOSITE[names['turns'][0]]))
                    elif isinstance(ll2, MainLM):
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            qa_pairs[4].append((ll1, pl, ll2, direction, ROUTE_OPPOSITE[names['turns'][0]]))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, names['turns'][0]))
                    elif isinstance(ll2, BoundaryLM) and ll2.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            if ll2.side == names['entrance']:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                        else:
                            if ll2.side == names['entrance']:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                elif pl.attached_to == 'sec_entry' and ll1 == 'sec_entry':
                    if isinstance(ll2, BoundaryLM) and ll2.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'left'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'right'))
                        else:
                            if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'left'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'right'))
                    elif isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side]:
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                    elif isinstance(ll2, MainLM):
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                elif pl.attached_to == 'sec_exit' and ll1 == 'sec_exit':
                    if isinstance(ll2, BoundaryLM) and ll2.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'left'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'right'))
                        else:
                            if (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'left'))
                            else:
                                qa_pairs[4].append((ll1, pl, ll2, direction, 'right'))
                    elif isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side]:
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                    elif isinstance(ll2, MainLM):
                        direction = random.choice(['left', 'right'])
                        if direction == pl.side:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))
                        else:
                            qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))

        elif t == 5:
            # qa type 5: go along ll1 with ll2 on the left/right/front/back, where is pl? pl is on ll1
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
            lls = area['boundary_ll'] + [area['main_ll']] + ['sec_entry', 'sec_inner', 'sec_exit']
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2, pl) not in selected_tuples:
                selected_tuples.append((ll1, ll2, pl))
                if pl.attached_to == ll1 or (pl.attached_to == 'main' and isinstance(ll1, MainLM)):
                    if isinstance(ll1, MainLM) and (ll2 in ['sec_entry', 'sec_inner', 'sec_exit'] or (isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side])):
                        direction = random.choice(['left', 'right'])
                        if direction == names['turns'][0]:
                            qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                        else:
                            qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                    elif ll1 == 'sec_inner':
                        if isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side]:
                            direction = random.choice(['left', 'right'])
                            if direction == names['turns'][0]:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            else:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                        elif isinstance(ll2, MainLM):
                            direction = random.choice(['left', 'right'])
                            if direction == names['turns'][0]:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                            else:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                        elif isinstance(ll2, BoundaryLM) and ll2.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                            direction = random.choice(['front', 'back'])
                            if (direction == 'back' and ll2.side == names['entrance']) or (direction == 'front' and ll2.side != names['entrance']):
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            else:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                    elif ll1 == 'sec_entry':
                        if isinstance(ll2, MainLM) or (
                                isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side]):
                            direction = random.choice(['front', 'back'])
                            if (direction == 'back' and isinstance(ll2, MainLM)) or (direction == 'front' and not isinstance(ll2, MainLM)):
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            else:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                        elif isinstance(ll2, BoundaryLM) and ll2.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                            direction = random.choice(['left', 'right'])
                            if direction == 'left' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'left' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                        elif ll2 == 'sec_exit':
                            direction = random.choice(['left', 'right'])
                            if direction == 'left' and (ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[names['entrance']]) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[names['entrance']]) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'left' and (ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[names['entrance']]) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[names['entrance']]) - ROUTE_DIRECTIONS.index(ROUTE_OPPOSITE[area['main_ll'].side])) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                    elif ll1 == 'sec_exit':
                        if isinstance(ll2, MainLM) or (isinstance(ll2, BoundaryLM) and ll2.side == ROUTE_OPPOSITE[area['main_ll'].side]):
                            direction = random.choice(['front', 'back'])
                            if (direction == 'front' and isinstance(ll2, MainLM)) or (direction == 'back' and not isinstance(ll2, MainLM)):
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            else:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                        elif isinstance(ll2, BoundaryLM) and ll2.side != ROUTE_OPPOSITE[area['main_ll'].side]:
                            direction = random.choice(['left', 'right'])
                            if direction == 'left' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'left' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(ll2.side) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                        elif ll2 == 'sec_entry':
                            direction = random.choice(['left', 'right'])
                            if direction == 'left' and (ROUTE_DIRECTIONS.index(names['entrance']) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(names['entrance']) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                            elif direction == 'left' and (ROUTE_DIRECTIONS.index(names['entrance']) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 1:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                            elif direction == 'right' and (ROUTE_DIRECTIONS.index(names['entrance']) - ROUTE_DIRECTIONS.index(area['main_ll'].side)) % 4 == 3:
                                qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))

    return {k: [(lm2names(area, names, p[0]), lm2names(area, names, p[1]), lm2names(area, names, p[2])) + p[3:] for p in v] for k, v in qa_pairs.items()}


def generate_survey_qa(area, names, up='north', qa_num=20):
    up_index = SURVEY_DIRECTIONS.index(up)
    main_side = area['main_ll'].side
    entrance = names['entrance']

    turns = names['turns']
    ori_direction = SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ROUTE_OPPOSITE[entrance]])
    if turns[0] == 'left':
        sec_dirs = {'sec_entry': ori_direction - 2,
                    'sec_inner': ori_direction,
                    'sec_exit': ori_direction + 2}
    else:
        sec_dirs = {'sec_entry': ori_direction + 2,
                    'sec_inner': ori_direction,
                    'sec_exit': ori_direction - 2}

    qa_pairs = {k: [] for k in range(1, 4)}
    selected_pairs = []
    while sum([len(v) for v in qa_pairs.values()]) < qa_num:
        t = random.randint(1, 3)

        if t == 1:
            # qa type 1: ll vs ll
            lls = area['boundary_ll'] + [area['main_ll']] + ['sec_entry', 'sec_inner', 'sec_exit']
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2) not in selected_pairs:
                selected_pairs.append((ll1, ll2))
                if ll1 in area['boundary_ll'] + [area['main_ll']]:
                    ll1_to_ll2_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll1.side]) + up_index) % 8]
                    qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))
                elif ll2 in area['boundary_ll'] + [area['main_ll']]:
                    ll1_to_ll2_dir = SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll2.side]) + up_index) % 8]]
                    qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))
                elif (ll1, ll2) == ('sec_entry', 'sec_exit'):
                    ll1_to_ll2_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[entrance]) + up_index) % 8]
                    qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))
                elif (ll1, ll2) == ('sec_exit', 'sec_entry'):
                    ll1_to_ll2_dir = SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[entrance]) + up_index) % 8]]
                    qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))

        elif t == 2:
            # qa type 2: pl vs ll
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
            lls = area['boundary_ll'] + [area['main_ll']] + ['sec_entry', 'sec_inner', 'sec_exit']
            pl = random.choice(pls)
            ll = random.choice(lls)
            if (pl, ll) not in selected_pairs:
                selected_pairs.append((pl, ll))
                if ll in area['boundary_ll']:
                    pl_to_ll_dir = SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll.side]) + up_index) % 8]]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                elif ll == area['main_ll'] and pl in area['main_pl1'] + area['main_pl2']:
                    if pl.side == 'left':
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(ori_direction + up_index - 2) % 8]
                        qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                    else:
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(ori_direction + up_index + 2) % 8]
                        qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                elif ll in ['sec_entry', 'sec_inner', 'sec_exit'] and pl in area['sec_entry_pl'] + area['sec_inner_pl'] + \
                        area['sec_exit_pl'] and pl.attached_to == ll:
                    if pl.side == 'left':
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(sec_dirs[ll] + up_index - 2) % 8]
                        qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                    else:
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(sec_dirs[ll] + up_index + 2) % 8]
                        qa_pairs[2].append((pl, ll, pl_to_ll_dir))

        elif t == 3:
            # qa type 3: pl vs pl
            pls = area['sec_entry_pl'] + area['sec_inner_pl'] + area['sec_exit_pl'] + area['main_pl1'] + area['main_pl2']
            pl1, pl2 = random.sample(pls, 2)
            if (pl1, pl2) not in selected_pairs:
                selected_pairs.append((pl1, pl2))
                if pl1.attached_to == pl2.attached_to and pl1.side == pl2.side:  # on the same side of the same ll
                    if pl1.attached_to == 'main':
                        if pl1.t > pl2.t:
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]))
                        else:
                            qa_pairs[3].append((pl1, pl2, SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]]))
                    else:
                        if pl1.t > pl2.t:
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(sec_dirs[pl1.attached_to] + up_index) % 8]))
                        else:
                            qa_pairs[3].append((pl1, pl2, SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(sec_dirs[pl1.attached_to] + up_index) % 8]]))
                elif pl1.attached_to != pl2.attached_to:  # on different lls
                    if pl1.attached_to == 'main':
                        if pl1.t < area['secondary_ll'].entry_t:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]}+{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                        elif pl1.t > area['secondary_ll'].exit_t:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]}+{SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                    elif pl2.attached_to == 'main':
                        if pl2.t < area['secondary_ll'].entry_t:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]]}+{SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                        elif pl2.t > area['secondary_ll'].exit_t:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]]}+{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                    elif pl1.attached_to == 'sec_entry' and pl2.attached_to == 'sec_inner':
                        pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]]}+{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]}']
                        qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                    elif pl1.attached_to == 'sec_inner' and pl2.attached_to == 'sec_entry':
                        pl1_to_pl2_dir = SURVEY_OPPOSITE[STR2SURVEY[f'{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]]}+{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]}']]
                        qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                    elif pl1.attached_to == 'sec_exit' and pl2.attached_to == 'sec_inner':
                        pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]}+{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]}']
                        qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                    elif pl1.attached_to == 'sec_inner' and pl2.attached_to == 'sec_exit':
                        pl1_to_pl2_dir = SURVEY_OPPOSITE[STR2SURVEY[f'{SURVEY_DIRECTIONS[(ori_direction + up_index) % 8]}+{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[main_side]) + up_index) % 8]}']]
                        qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))

    return {k: [(lm2names(area, names, lm1), lm2names(area, names, lm2), dir) for (lm1, lm2, dir) in v] for k, v in qa_pairs.items()}


if __name__ == '__main__':
    f1 = open('../template1_route_train.jsonl', 'w')
    f2 = open('../template1_survey_train.jsonl', 'w')
    n = 1

    for up in ['north', 'east', 'south', 'west']:
        up_index = SURVEY_DIRECTIONS.index(up)
        for _ in range(50):
            area = generate_area()
            names = generate_names(area)
            route_initial = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ROUTE_OPPOSITE[names['entrance']]]) + up_index) % 8]
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
