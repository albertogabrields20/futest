import math
from collections import defaultdict, Counter
from .loaders import get_jugadores, get_pid, get_pos, get_team


def build_trajectories(frames):
    trajs = defaultdict(list)
    for fi, frame in enumerate(frames):
        for det in get_jugadores(frame):
            pid = get_pid(det)
            x, y = get_pos(det)
            team = get_team(det)
            trajs[pid].append((fi, x, y, team))
    return trajs


def majority_team(pts):
    c = Counter(p[3] for p in pts)
    return c.most_common(1)[0][0]


def distance_per_player(trajs):
    result = {}
    for pid, pts in trajs.items():
        d = 0.0
        for i in range(1, len(pts)):
            dx = pts[i][1] - pts[i-1][1]
            dy = pts[i][2] - pts[i-1][2]
            d += math.sqrt(dx*dx + dy*dy)
        result[pid] = round(d, 1)
    return result


def build_player_team_map(trajs):
    return {pid: majority_team(pts) for pid, pts in trajs.items()}


def build_players_by_team(player_team):
    players_by_team = defaultdict(list)
    for pid, team in player_team.items():
        players_by_team[team].append(pid)
    return players_by_team


def precompute_heatmaps(trajs, player_team):
    heatmap_all = {
        0: [(p[1], p[2]) for pid, pts in trajs.items()
            if player_team.get(pid) == 0 for p in pts],
        1: [(p[1], p[2]) for pid, pts in trajs.items()
            if player_team.get(pid) == 1 for p in pts],
    }
    heatmap_diff = {"e0": heatmap_all[0], "e1": heatmap_all[1]}
    return heatmap_all, heatmap_diff
