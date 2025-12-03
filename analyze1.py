import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ----------------------------------------------------------------------
# L-System 规则和颜色定义 (保持不变)
# ----------------------------------------------------------------------
MONDRIAN_EARLY_RULES = {
    'S': [
        (0.40, 'H[S][S]'), 
        (0.40, 'V[S][S]'), 
        (0.20, 'F')        
    ],
}
COLORS = ['red', 'yellow', 'blue', 'white', 'lightgray'] 
SPLIT_RATIOS = [0.33, 0.4, 0.5, 0.6, 0.67] 
MIN_SIZE = 0.005 # 降低阈值，确保填充

def generate_l_system_string(axiom, rules, iterations):
    # (此函数保持不变，用于生成字符串)
    current_string = axiom
    for i in range(iterations):
        next_string = []
        for char in current_string:
            if char in rules:
                successors = [item[1] for item in rules[char]]
                probabilities = [item[0] for item in rules[char]]
                chosen_successor = random.choices(successors, weights=probabilities, k=1)[0]
                next_string.append(chosen_successor)
            else:
                next_string.append(char)
        current_string = "".join(next_string)
    return current_string

# ----------------------------------------------------------------------
# 几何解释器部分 (稳定、函数式递归版本)
# ----------------------------------------------------------------------

def parse_and_subdivide(l_string, rect):
    """
    递归函数：解析 L 系统字符串的当前片段，分割矩形，并返回剩余字符串。
    
    Args:
        l_string (str): 待处理的字符串片段。
        rect (tuple): 当前矩形 (x, y, w, h)。

    Returns:
        tuple: (剩余未处理的字符串, 最终填充的矩形列表)
    """
    x, y, w, h = rect
    final_rects = []

    if not l_string:
        return "", []

    char = l_string[0]
    rest_string = l_string[1:]

    if char == 'F':
        # F: 终止，填充当前矩形
        if w > MIN_SIZE and h > MIN_SIZE:
            final_rects.append((x, y, w, h, random.choice(COLORS)))
        return rest_string, final_rects # 返回剩余字符串和填充的矩形列表

    elif char == 'H' or char == 'V':
        # H/V: 分割操作
        if w < MIN_SIZE or h < MIN_SIZE:
            # 尺寸太小，自动终止并填充 (递归到此结束)
            final_rects.append((x, y, w, h, random.choice(COLORS)))
            return rest_string, final_rects
            
        split_ratio = random.choice(SPLIT_RATIOS)
        
        if char == 'H':
            rect1 = (x, y, w, h * split_ratio)
            rect2 = (x, y + h * split_ratio, w, h * (1 - split_ratio))
        else: # V
            rect1 = (x, y, w * split_ratio, h)
            rect2 = (x + w * split_ratio, y, w * (1 - split_ratio), h)

        # 检查 S1 分支: 必须以 '[' 开始
        if rest_string and rest_string[0] == '[':
            rest_string = rest_string[1:] # 跳过 '['
            
            # 递归处理第一个子矩形 (S1)
            remaining_after_s1, rects_s1 = parse_and_subdivide(rest_string, rect1)
            final_rects.extend(rects_s1)
            rest_string = remaining_after_s1
            
            # 检查 S1 分支: 必须以 ']' 结束
            if rest_string and rest_string[0] == ']':
                rest_string = rest_string[1:] # 跳过 ']'

        # 检查 S2 分支: 必须以 '[' 开始
        if rest_string and rest_string[0] == '[':
            rest_string = rest_string[1:] # 跳过 '['
            
            # 递归处理第二个子矩形 (S2)
            remaining_after_s2, rects_s2 = parse_and_subdivide(rest_string, rect2)
            final_rects.extend(rects_s2)
            rest_string = remaining_after_s2
            
            # 检查 S2 分支: 必须以 ']' 结束
            if rest_string and rest_string[0] == ']':
                rest_string = rest_string[1:] # 跳过 ']'

        return rest_string, final_rects
    
    elif char == '[' or char == ']':
        # 理论上 '[' 和 ']' 在 H/V 中被处理，这里作为容错直接跳过
        return rest_string, []

    # 遇到未定义符号，直接跳过
    return rest_string, []


def interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)):
    """外部调用函数"""
    _, final_rects = parse_and_subdivide(l_string, initial_rect)
    return final_rects

# ----------------------------------------------------------------------
# 绘图函数
# ----------------------------------------------------------------------
def plot_mondrian_composition(rect_data, title="Mondrian-esque Composition"):
    """
    绘制蒙德里安风格的构图。
    """
    fig, ax = plt.subplots(1, figsize=(8, 8)) # 1x1 单位大小的画布
    
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off() # 隐藏坐标轴
    
    # 背景填充为白色
    ax.add_patch(patches.Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='black', linewidth=2))

    for x, y, w, h, color in rect_data:
        # 使用黑色边框模拟蒙德里安的粗黑线
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor=color)
        ax.add_patch(rect)
        
    plt.title(title)
    plt.show()

# ----------------------------------------------------------------------
# 主程序执行
# ----------------------------------------------------------------------
if __name__ == '__main__':

    print("--- 生成 L 系统字符串（早期蒙德里安构图）---")
    axiom = 'S'
    iterations = 5 # 增加迭代次数以获得更复杂的结构
    l_string = generate_l_system_string(axiom, MONDRIAN_EARLY_RULES, iterations=5)

    print("\n--- 解释 L 系统字符串并生成矩形数据 (函数式递归) ---")
    rectangles = interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)) 
    print(f"生成了 {len(rectangles)} 个填充矩形。")

    print("\n--- 绘制蒙德里安风格的构图 ---")
    plot_mondrian_composition(rectangles, title=f"Mondrian-esque Composition (Iterations: 5, Rects: {len(rectangles)})")
    print(f"生成了 {len(rectangles)} 个填充矩形。")

    # 简单分析：计算一些指标
    total_area = sum(w * h for _, _, w, h, _ in rectangles)
    print(f"所有填充矩形的总面积: {total_area:.4f}")
    
    # 我们可以计算颜色分布
    color_counts = {}
    for _, _, _, _, color in rectangles:
        color_counts[color] = color_counts.get(color, 0) + 1
    print(f"颜色分布: {color_counts}")