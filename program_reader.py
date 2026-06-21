import csv

def load_programs(path='data/programs.csv'):
    programs = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            pid = row['ProgramID']
            step = int(row['StepNo'])
            ch = int(row['ChannelNo'])
            val = int(row['ChannelVal'])
            if pid not in programs:
                programs[pid] = {}
            if step not in programs[pid]:
                programs[pid][step] = {}
            programs[pid][step][ch] = val
    return programs

if __name__ == '__main__':
    p = load_programs()
    for pid, steps in p.items():
        print(f'{pid}: {len(steps)} steps')
        for s, chs in steps.items():
            print(f'  step{s}: {chs}')
