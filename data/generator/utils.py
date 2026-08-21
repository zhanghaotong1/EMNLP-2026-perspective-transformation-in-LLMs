import random

WORDS_DICT = {'linear_ll1': ['Road', 'Street', 'Avenue', 'Highway'],
              'linear_ll2': ['Railway', 'Canal', 'River', 'Coast', 'Shoreline', 'Ridge', 'Valley', 'Forest', 'Beach', 'Bay'],
              'name': ['Madison', 'Lincoln', 'Oak', 'Cedar', 'Maple', 'Highland', 'White', 'Silver', 'Pine', 'Redstone',
                       'Willow', 'Bear', 'Greenwood', 'Black', 'Granite', 'Eagle', 'Old City'],
              'point_ll': ['café', 'restaurant', 'bakery', 'pharmacy', 'bookstore', 'supermarket', 'bank',
                           'post office', 'hotel', 'hospital', 'school', 'church', 'town hall', 'museum', 'theatre',
                           'library', 'cinema', 'flower shop', 'toy store', 'barbershop', 'grocery', 'statue', 'gazebo',
                           'monument', 'fountain', 'playground', 'parking lot', 'bus stop', 'train station', 'clock tower'],
              'transport': ['walk', 'ride', 'drive'],
              'distance': ['kilometre', 'mile']}

SURVEY_DIRECTIONS = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']

ROUTE_DIRECTIONS = ['up', 'right', 'down', 'left']

SURVEY_OPPOSITE = {'north': 'south',
                   'south': 'north',
                   'east': 'west',
                   'west': 'east',
                   'northeast': 'southwest',
                   'southwest': 'northeast',
                   'northwest': 'southeast',
                   'southeast': 'northwest'}

ROUTE_OPPOSITE = {'left': 'right',
                  'right': 'left',
                  'up': 'down',
                  'down': 'up'}

ROUTE2SURVEY = {'up': 'north',
                'left': 'west',
                'down': 'south',
                'right': 'east'}

STR2SURVEY = {'north+east': 'northeast',
              'east+north': 'northeast',
              'north+west': 'northwest',
              'west+north': 'northwest',
              'south+east': 'southeast',
              'east+south': 'southeast',
              'south+west': 'southwest',
              'west+south': 'southwest'}


def routeqa2nl(qa_pairs):
    qa_nls = []

    for k in qa_pairs:
        if k == 1 or k == 2:
            for p in qa_pairs[k]:
                qa_nls.append((f'If you go from {p[0]} to {p[1]}, where is {p[2]}?', p[3]))
        elif k == 3:
            for p in qa_pairs[k]:
                qa_nls.append((f'If {p[1]} is on your {p[3]} as you go along {p[0]}, what side of {p[0]} is {p[2]} on?', p[4]))
        elif k == 4:
            for p in qa_pairs[k]:
                qa_nls.append((f'If {p[1]} is on your {p[3]} as you go along {p[0]}, where is {p[2]}?', p[4]))
        elif k == 5:
            for p in qa_pairs[k]:
                if p[3] == 'front':
                    qa_nls.append((f'If you go along {p[0]} with {p[1]} ahead, what side of {p[0]} is {p[2]} on?', p[4]))
                elif p[3] == 'back':
                    qa_nls.append((f'If you go along {p[0]} with {p[1]} behind, what side of {p[0]} is {p[2]} on?', p[4]))
                else:
                    qa_nls.append((f'If you go along {p[0]} with {p[1]} on your {p[3]}, what side of {p[0]} is {p[2]} on?', p[4]))

    random.shuffle(qa_nls)
    return qa_nls


def surveyqa2nl(qa_pairs):
    qa_nls = []
    for k in qa_pairs:
        for p in qa_pairs[k]:
            qa_nls.append((f'In which direction is {p[0]} from {p[1]}?', p[2]))
    random.shuffle(qa_nls)
    return qa_nls
