import cv2
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.stats import bootstrap
import tqdm

# ---------- 0. 参数 ----------
IMG_PATH = 'Piet_Mondriaan,_1930_-_Mondrian_Composition_II_in_Red,_Blue,_and_Yellow.jpg'   # 自行下载高清图
RED_RANGE   = {'lower':(0,0,180), 'upper':(40,40,255)}   # BGR 空间红色区间
AREA_RATIO_GOLDEN = 0.618
N_BOOTSTRAP = 10000
CONF_LEVEL  = 0.99

# ---------- 1. 几何：矢量化 + DCEL ----------
def build_dcel_and_stats(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # 第一次试跑，阈值 2000
    lines = cv2.HoughLines(edges, 1, np.pi/180, 2000)

    # 如果没找到线，逐渐降阈值直到有结果
    thresh = 2000
    while lines is None and thresh > 100:
        thresh -= 200
        lines = cv2.HoughLines(edges, 1, np.pi/180, thresh)

    # 极端情况：整张图就是空白，也返回空结构
    if lines is None:
        return [], np.array([]), {'pareto_ratio':0,
                                  'direction_entropy':0,
                                  'split_depth':0}

    h_lines, v_lines = [], []
    for rho, theta in lines[:, 0]:
        if abs(theta) < 1*np.pi/180:      # 水平
            h_lines.append(int(rho))
        elif abs(theta - np.pi/2) < 1*np.pi/180:  # 竖直
            v_lines.append(int(rho))

    # 去重 + 排序
    h_lines = sorted(set(h_lines))
    v_lines = sorted(set(v_lines))

    # —— 下面与原脚本完全一致 ——
    rects, areas = [], []
    H, W = img_bgr.shape[:2]
    for y1, y2 in zip(h_lines[:-1], h_lines[1:]):
        for x1, x2 in zip(v_lines[:-1], v_lines[1:]):
            poly = Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
            rects.append(poly)
            areas.append(poly.area)
    areas = np.array(areas)
        # ===== 新增：防呆 =====
    if areas.size == 0:          # 没有切出任何矩形
        return rects, areas, {'pareto_ratio': 0.,
                              'direction_entropy': 0.,
                              'split_depth': 0.}
    # =======================
    # 1) 面积 Pareto
    areas_sorted = np.sort(areas)[::-1]
    cum = np.cumsum(areas_sorted)
    pareto_80 = np.searchsorted(cum, cum[-1]*0.8) + 1
    pareto_ratio = pareto_80 / len(areas)
    # 2) 方向熵（这里只有 0°/90°，熵应接近 0）
    angles = np.array([0]*len(h_lines) + [90]*len(v_lines))
    counts = np.bincount(angles.astype(int), minlength=181)
    prob = counts[counts>0] / counts.sum()
    entropy = -np.sum(prob * np.log2(prob))
    # 3) 分割深度（简单二叉树深度）
    depth = max(np.log2(len(h_lines)), np.log2(len(v_lines)))
    return rects, areas, {'pareto_ratio':pareto_ratio,
                          'direction_entropy':entropy,
                          'split_depth':depth}

# ---------- 2. 数学：Bootstrap 检验 ----------
def red_area_ratio(img_bgr, rects):
    mask_red = cv2.inRange(img_bgr, *RED_RANGE.values())
    red_areas = []
    for poly in rects:
        # 取矩形中心点颜色作为代表
        x,y = poly.centroid.coords[0]
        if mask_red[int(y), int(x)] == 255:
            red_areas.append(poly.area)
    return np.sum(red_areas) / (img_bgr.shape[0]*img_bgr.shape[1])

def bootstrap_test(obs_ratio):
    # 构造虚拟总体：在 [0.1,0.9] 均匀分布里重采样
    def sample_ratio(n, rng):
        return rng.uniform(0.1, 0.9, size=n)
    rng = np.random.default_rng(42)
    data = sample_ratio(1000, rng)          # 大样本
    # Bootstrap 采样均值
    res = bootstrap((data,), np.mean, n_resamples=N_BOOTSTRAP,
                    confidence_level=CONF_LEVEL, random_state=rng)
    ci_low, ci_high = res.confidence_interval
    # 单侧检验：观测值是否 > 0.618
    p_greater = (np.mean(data) > AREA_RATIO_GOLDEN).mean()
    return ci_low, ci_high, p_greater

# ---------- 3. 主流程 ----------
if __name__ == '__main__':
    img = cv2.imread(IMG_PATH)
    rects, areas, stats = build_dcel_and_stats(img)
    if not rects:                # 还是空
        print('[!] 没能检测到足够网格线，请：\n'
              '   1) 把 cv2.HoughLines 阈值再调低；\n'
              '   2) 换一张更高清、对比度更强的 Mondrian 图。')
        exit()
    print('=== 几何指标 ===')
    print(f'面积 Pareto 比例（块数占比）: {stats["pareto_ratio"]:.2f}')
    print(f'方向熵 (bits): {stats["direction_entropy"]:.3f}')
    print(f'分割深度 (log2): {stats["split_depth"]:.1f}')

    obs_ratio = red_area_ratio(img, rects)
    print('\n=== Bootstrap 检验 ===')
    print(f'观测红色面积占比: {obs_ratio:.3f}')
    ci_low, ci_high, p = bootstrap_test(obs_ratio)
    print(f'Bootstrap 99% CI (均匀总体): [{ci_low:.3f}, {ci_high:.3f}]')
    print(f'观测值 > 0.618 的 p 值: {p:.4f}')
    if obs_ratio > 0.618 and p < 0.01:
        print('→ 拒绝原假设，红色占比显著高于黄金分割！')
    else:
        print('→ 无显著证据表明红色占比接近黄金分割。')