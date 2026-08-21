import json
from dataclasses import dataclass
from typing import Literal
from utils import *


@dataclass
class MainLM:
    id: str


@dataclass
class BranchLM:
    id: str
    side: Literal['up', 'down']


@dataclass
class Junction:
    t_main: float


@dataclass
class PointLM:
    id: str
    attached_to: Literal['main', 'branch']
    t: float
    side: Literal['left', 'right']


def generate_area(
        min_junc=0.35,
        max_junc=0.65,
        min_main_pl=2,
        max_main_pl=5,
        min_branch_pl=3,
        max_branch_pl=6,
):
    area = {}

    # generate main linear landmark
    area['main_ll'] = MainLM(id='main')

    # randomly generate junction point of main linear landmark and branch linear landmark
    area['junction'] = Junction(t_main=random.uniform(min_junc, max_junc))

    # randomly generate branch linear landmarks
    branch = BranchLM(
        id='branch',
        side=random.choice(['up', 'down'])
    )
    area['branch_ll'] = branch

    # randomly generate point landmarks on main linear landmark
    n_main_pl = random.randint(min_main_pl, max_main_pl)
    main_ts = []
    while len(main_ts) < n_main_pl:
        t = random.uniform(0.05, 0.95)
        if abs(t - area['junction'].t_main) > 0.08:
            main_ts.append(t)
    main_ts.sort()
    main_pls = []
    for i, t in enumerate(main_ts):
        main_pls.append(
            PointLM(
                id=f'main_pl_{i}',
                attached_to='main',
                t=t,
                side=random.choice(['left', 'right']),
            )
        )

    # randomly generate point landmarks on branch linear landmark
    n_branch_pl = random.randint(min_branch_pl, max_branch_pl)
    branch_ts = sorted(random.uniform(0.05, 0.95) for _ in range(n_branch_pl))
    branch_pls = []
    for i, t in enumerate(branch_ts):
        branch_pls.append(
            PointLM(
                id=f'branch_pl_{i}',
                attached_to='branch',
                t=t,
                side=random.choice(['left', 'right']),
            )
        )

    area['point_lm'] = main_pls + branch_pls

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

    main_ll_name = random.choice(WORDS_DICT['name']) + ' ' + random.choice(WORDS_DICT['linear_ll1'])
    branch_ll_name = random.choice(WORDS_DICT['name']) + ' ' + random.choice(WORDS_DICT['linear_ll1'])
    town_name = random.choice(WORDS_DICT['name'])

    pl_names = random.sample(WORDS_DICT['point_ll'], len(area['point_lm']))
    pl_names_dict = {'main': {}, 'branch': {}}
    for i, pl in enumerate(area['point_lm']):
        pl_names_dict[pl.attached_to][pl.t] = pl_names[i]

    entrance = random.choice(['left', 'right'])
    branch_side = area['branch_ll'].side
    if (entrance, branch_side) in [('left', 'down'), ('right', 'up')]:
        turn = 'right'
    else:
        turn = 'left'

    return {
        'transport': transport,
        'transporting': transporting,
        'proportion': proportion,
        'distance': distance,
        'main_ll': main_ll_name,
        'branch_ll': branch_ll_name,
        'pl': pl_names_dict,
        'town_name': town_name,
        'entrance': entrance,
        'branch_side': branch_side,
        'turn': turn,
    }


def lm2names(names, lm):
    if isinstance(lm, MainLM):
        return names['main_ll']
    elif isinstance(lm, BranchLM):
        return names['branch_ll']
    else:
        return names['pl'][lm.attached_to][lm.t]


def generate_route(area, names):
    transport = names['transport']
    transporting = names['transporting']
    proportion = names['proportion']
    distance = names['distance']

    main_ll_name = names['main_ll']
    branch_ll_name = names['branch_ll']
    pl_names = names['pl']
    town_name = names['town_name']
    turn = names['turn']

    pls_main = [pl for pl in area['point_lm'] if pl.attached_to == 'main']
    pls_main_before = [pl for pl in pls_main if pl.t < area['junction'].t_main]
    pls_main_after = [pl for pl in pls_main if pl.t > area['junction'].t_main]
    pls_branch = [pl for pl in area['point_lm'] if pl.attached_to == 'branch']
    pls_main_before.sort(key=lambda x: x.t)
    pls_main_after.sort(key=lambda x: x.t)
    pls_branch.sort(key=lambda x: x.t)

    description = f'You enter {town_name} Town through {main_ll_name}. {transport.capitalize()} along {main_ll_name}. '

    cur_t = 0
    for pl in pls_main_before:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (f'You continue {transporting} along {main_ll_name} and come to {branch_ll_name} on your {turn}. '
                    f'Turn {turn} onto {branch_ll_name}. ')

    cur_t = 0
    for pl in pls_branch:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["branch"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += (f'You reach the end of {branch_ll_name}. Go back to where you leave {main_ll_name} and turn {turn} '
                    f'back onto {main_ll_name}. ')

    cur_t = area['junction'].t_main
    for pl in pls_main_after:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main"][pl.t]} on your {pl.side}. ')
        cur_t = pl.t

    description += f'You continue along {main_ll_name} and leave the town.'

    return description


def generate_survey(area, names, up='north'):
    up_index = SURVEY_DIRECTIONS.index(up)

    transport = names['transport']
    transporting = names['transporting']
    proportion = names['proportion']
    distance = names['distance']
    entrance = names['entrance']
    turn = names['turn']

    main_ll_name = names['main_ll']
    branch_ll_name = names['branch_ll']
    pl_names = names['pl']
    town_name = names['town_name']

    if entrance == 'left':
        current_orientation_index = (2 + up_index) % 8
    else:
        current_orientation_index = (6 + up_index) % 8

    def get_relative_dir(side):
        if side == 'left':
            return SURVEY_DIRECTIONS[(current_orientation_index - 2) % 8]
        else:
            return SURVEY_DIRECTIONS[(current_orientation_index + 2) % 8]

    pls_main = [pl for pl in area['point_lm'] if pl.attached_to == 'main']
    pls_main_before = [pl for pl in pls_main if pl.t < area['junction'].t_main]
    pls_main_after = [pl for pl in pls_main if pl.t > area['junction'].t_main]
    pls_branch = [pl for pl in area['point_lm'] if pl.attached_to == 'branch']
    pls_main_before.sort(key=lambda x: x.t)
    pls_main_after.sort(key=lambda x: x.t)
    pls_branch.sort(key=lambda x: x.t)

    description = (f'{town_name} Town consists of two main roads: {main_ll_name} and {branch_ll_name}. You enter the '
                   f'town via {main_ll_name}. {transport.capitalize()} {SURVEY_DIRECTIONS[current_orientation_index]} '
                   f'along {main_ll_name}. ')

    cur_t = 0
    for pl in pls_main_before:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main"][pl.t]} on the {get_relative_dir(pl.side)}. ')
        cur_t = pl.t

    if turn == 'left':
        current_orientation_index = (current_orientation_index - 2) % 8
    else:
        current_orientation_index = (current_orientation_index + 2) % 8

    description += (f'You come to {branch_ll_name} on the {SURVEY_DIRECTIONS[current_orientation_index]}. Turn '
                    f'{SURVEY_DIRECTIONS[current_orientation_index]} onto {branch_ll_name}. ')

    cur_t = 0
    for pl in pls_branch:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["branch"][pl.t]} on the {get_relative_dir(pl.side)}. ')
        cur_t = pl.t

    # now the direction is 180 degree reversed
    if turn == 'left':
        current_orientation_index = (current_orientation_index + 2) % 8
    else:
        current_orientation_index = (current_orientation_index - 2) % 8

    description += (f'You reach the end of {branch_ll_name}. Go back to where you leave {main_ll_name} and turn '
                    f'{SURVEY_DIRECTIONS[current_orientation_index]} back onto {main_ll_name}. ')

    cur_t = area['junction'].t_main
    for pl in pls_main_after:
        description += (f'{transport.capitalize()} for {(pl.t - cur_t) * proportion:.2f} {distance} and you will see '
                        f'{pl_names["main"][pl.t]} on the {get_relative_dir(pl.side)}. ')
        cur_t = pl.t

    description += f'Continue {transporting} {SURVEY_DIRECTIONS[current_orientation_index]} and you leave the town via {main_ll_name}.'

    return description


def generate_symbolic(area, names):
    description = (f'{names["town_name"]} Town has two main roads: {names["main_ll"]} and {names["branch_ll"]}, which '
                   f'are perpendicular to each other, forming a T-junction. They intersect at proportion '
                   f'{area["junction"].t_main:.2f} of {names["main_ll"]}. ')

    pls_main = [pl for pl in area['point_lm'] if pl.attached_to == 'main']
    pls_branch = [pl for pl in area['point_lm'] if pl.attached_to == 'branch']
    pls_main.sort(key=lambda x: x.t)
    pls_branch.sort(key=lambda x: x.t)

    side2pl = {'left': [], 'right': []}
    for pl in pls_main:
        side2pl[pl.side].append(names['pl']['main'][pl.t])
        description += f'{names["pl"]["main"][pl.t].capitalize()} is on {names["main_ll"]} at proportion {pl.t:.2f}. '
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
    for pl in pls_branch:
        side2pl[pl.side].append(names['pl']['branch'][pl.t])
        description += f'{names["pl"]["branch"][pl.t].capitalize()} is on {names["branch_ll"]} at proportion {pl.t:.2f}. '
    if len(side2pl['left']) == 0 or len(side2pl['right']) == 0:
        description += f'All landmarks are on the same side of {names["branch_ll"]}.'
    else:
        if len(side2pl['left']) == 1:
            description += f'{side2pl["left"][0].capitalize()} is on one side of {names["branch_ll"]}, '
        else:
            description += f'{", ".join(side2pl["left"]).capitalize()} are on one side of {names["branch_ll"]}, '
        if len(side2pl['right']) == 1:
            description += f'while {side2pl["right"][0]} is on the other side of {names["branch_ll"]}.'
        else:
            description += f'while {", ".join(side2pl["right"])} are on the other side of {names["branch_ll"]}.'

    return description


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
            lls = [area['main_ll'], area['branch_ll']]
            pl1, pl2 = random.sample(pls, 2)
            ll = random.choice(lls)
            if (pl1, pl2, ll) not in selected_tuples:
                selected_tuples.append((pl1, pl2, ll))
                if pl1.attached_to == pl2.attached_to:
                    if pl1.attached_to == 'main' and isinstance(ll, BranchLM):
                        if pl1.t < area['junction'].t_main < pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, names['turn']))
                        elif pl1.t > area['junction'].t_main > pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, ROUTE_OPPOSITE[names['turn']]))
                    elif pl1.attached_to == 'branch' and isinstance(ll, MainLM):
                        if pl1.t < pl2.t:
                            qa_pairs[2].append((pl1, pl2, ll, 'back'))
                        else:
                            qa_pairs[2].append((pl1, pl2, ll, 'front'))

        elif t == 3:
            # qa type 3: go along ll with pl1 on the left/right, where is pl2? pl1 and pl2 are on the ll
            pls = area['point_lm']
            lls = [area['main_ll'], area['branch_ll']]
            ll = random.choice(lls)
            pl1, pl2 = random.sample(pls, 2)
            if (ll, pl1, pl2) not in selected_tuples:
                selected_tuples.append((ll, pl1, pl2))
                if pl1.attached_to == pl2.attached_to:
                    if (pl1.attached_to == 'main' and isinstance(ll, MainLM)) or (pl1.attached_to == 'branch' and isinstance(ll, BranchLM)):
                        direction = random.choice(['left', 'right'])
                        if direction == pl1.side:
                            qa_pairs[3].append((ll, pl1, pl2, direction, pl2.side))
                        else:
                            qa_pairs[3].append((ll, pl1, pl2, direction, ROUTE_OPPOSITE[pl2.side]))

        elif t == 4:
            # qa type 4: go along ll1 with pl on the left/right, where is ll2? pl is on ll1
            pls = area['point_lm']
            lls = [area['main_ll'], area['branch_ll']]
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, pl, ll2) not in selected_tuples:
                selected_tuples.append((ll1, pl, ll2))
                if pl.attached_to == 'main' and isinstance(ll1, MainLM):
                    direction = random.choice(['left', 'right'])
                    if direction == pl.side:
                        qa_pairs[4].append((ll1, pl, ll2, direction, names['turn']))
                    else:
                        qa_pairs[4].append((ll1, pl, ll2, direction, ROUTE_OPPOSITE[names['turn']]))
                elif pl.attached_to == 'branch' and isinstance(ll1, BranchLM):
                    direction = random.choice(['left', 'right'])
                    if direction == pl.side:
                        qa_pairs[4].append((ll1, pl, ll2, direction, 'back'))
                    else:
                        qa_pairs[4].append((ll1, pl, ll2, direction, 'front'))

        elif t == 5:
            # qa type 5: go along ll1 with ll2 on the left/right/front/back, where is pl? pl is on ll1
            pls = area['point_lm']
            lls = [area['main_ll'], area['branch_ll']]
            pl = random.choice(pls)
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2, pl) not in selected_tuples:
                selected_tuples.append((ll1, ll2, pl))
                if pl.attached_to == 'main' and isinstance(ll1, MainLM):
                    direction = random.choice(['left', 'right'])
                    if direction == names['turn']:
                        qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                    else:
                        qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))
                elif pl.attached_to == 'branch' and isinstance(ll1, BranchLM):
                    direction = random.choice(['front', 'back'])
                    if direction == 'back':
                        qa_pairs[5].append((ll1, ll2, pl, direction, pl.side))
                    else:
                        qa_pairs[5].append((ll1, ll2, pl, direction, ROUTE_OPPOSITE[pl.side]))

    return {k: [(lm2names(names, p[0]), lm2names(names, p[1]), lm2names(names, p[2])) + p[3:] for p in v] for k, v in qa_pairs.items()}


def generate_survey_qa(area, names, up='north', qa_num=20):
    up_index = SURVEY_DIRECTIONS.index(up)
    if names['entrance'] == 'left':
        main_direction_index = 2
    else:
        main_direction_index = 6
    if area['branch_ll'].side == 'up':
        branch_direction_index = 0
    else:
        branch_direction_index = 4

    qa_pairs = {k: [] for k in range(1, 4)}
    selected_pairs = []
    while sum([len(v) for v in qa_pairs.values()]) < qa_num:
        t = random.randint(1, 3)

        if t == 1:
            # qa type 1: ll vs ll
            lls = [area['main_ll'], area['branch_ll']]
            ll1, ll2 = random.sample(lls, 2)
            if (ll1, ll2) not in selected_pairs:
                selected_pairs.append((ll1, ll2))
                if isinstance(ll1, MainLM):
                    ll1_to_ll2_dir = SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll2.side]) + up_index) % 8]]
                    qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))
                else:
                    ll1_to_ll2_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[ll1.side]) + up_index) % 8]
                    qa_pairs[1].append((ll1, ll2, ll1_to_ll2_dir))

        elif t == 2:
            # qa type 2: pl vs ll
            pls = area['point_lm']
            lls = [area['main_ll'], area['branch_ll']]
            pl = random.choice(pls)
            ll = random.choice(lls)
            if (pl, ll) not in selected_pairs:
                selected_pairs.append((pl, ll))
                if isinstance(ll, MainLM) and pl.attached_to == 'branch':
                    pl_to_ll_dir = SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[area['branch_ll'].side]) + up_index) % 8]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                elif pl.attached_to == 'main' and isinstance(ll, MainLM):
                    if pl.side == 'left':
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(main_direction_index + up_index - 2) % 8]
                    else:
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(main_direction_index + up_index + 2) % 8]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))
                elif pl.attached_to == 'branch' and isinstance(ll, BranchLM):
                    if pl.side == 'left':
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(branch_direction_index + up_index - 2) % 8]
                    else:
                        pl_to_ll_dir = SURVEY_DIRECTIONS[(branch_direction_index + up_index + 2) % 8]
                    qa_pairs[2].append((pl, ll, pl_to_ll_dir))

        elif t == 3:
            # qa type 3: pl vs pl
            pls = area['point_lm']
            pl1, pl2 = random.sample(pls, 2)
            if (pl1, pl2) not in selected_pairs:
                selected_pairs.append((pl1, pl2))
                if pl1.attached_to == pl2.attached_to and pl1.side == pl2.side:  # on the same side of the same ll
                    if pl1.attached_to == 'main':
                        if pl1.t > pl2.t:
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(main_direction_index + up_index) % 8]))
                        else:
                            qa_pairs[3].append((pl1, pl2, SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(main_direction_index + up_index) % 8]]))
                    else:
                        if pl1.t > pl2.t:
                            qa_pairs[3].append((pl1, pl2, SURVEY_DIRECTIONS[(branch_direction_index + up_index) % 8]))
                        else:
                            qa_pairs[3].append((pl1, pl2, SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(branch_direction_index + up_index) % 8]]))
                elif pl1.attached_to != pl2.attached_to:  # on different lls
                    if pl1.attached_to == 'main':
                        if pl1.t < area['junction'].t_main:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(main_direction_index + up_index) % 8]]}+{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[area["branch_ll"].side]) + up_index) % 8]]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                        else:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(main_direction_index + up_index) % 8]}+{SURVEY_OPPOSITE[SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[area["branch_ll"].side]) + up_index) % 8]]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                    else:
                        if pl2.t < area['junction'].t_main:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(main_direction_index + up_index) % 8]}+{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[area["branch_ll"].side]) + up_index) % 8]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))
                        else:
                            pl1_to_pl2_dir = STR2SURVEY[f'{SURVEY_DIRECTIONS[(main_direction_index + up_index) % 8]}+{SURVEY_DIRECTIONS[(SURVEY_DIRECTIONS.index(ROUTE2SURVEY[area["branch_ll"].side]) + up_index) % 8]}']
                            qa_pairs[3].append((pl1, pl2, pl1_to_pl2_dir))

    return {k: [(lm2names(names, lm1), lm2names(names, lm2), dir) for (lm1, lm2, dir) in v] for k, v in qa_pairs.items()}


if __name__ == '__main__':
    f1 = open('../template3_route_train.jsonl', 'w')
    f2 = open('../template3_survey_train.jsonl', 'w')
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
