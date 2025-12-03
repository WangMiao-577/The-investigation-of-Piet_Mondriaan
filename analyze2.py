import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ----------------------------------------------------------------------
# 蒙德里安 L 系统配置
# ----------------------------------------------------------------------

# 规则：S -> F 的概率降低，以获得更深的嵌套
MONDRIAN_EARLY_RULES = {
    'S': [
        (0.45, 'H[S][S]'),  # 增加分割概率
        (0.45, 'V[S][S]'), 
        (0.40, 'F')         # 降低终止概率
    ],
}

# 颜色：白色应占绝对主导地位，以模拟蒙德里安的留白
COLORS = ['white'] * 4 + ['red', 'yellow', 'blue']*6 # 10份白色，1份红黄蓝
# 分割比例：避免50/50，符合蒙德里安的动态平衡
SPLIT_RATIOS = [0.25, 0.33, 0.4, 0.6, 0.67, 0.75] 

MIN_SIZE = 0.005      # 最小填充阈值
LINE_WIDTH = 0.005    # 清晰的黑色线条宽度

# ----------------------------------------------------------------------
# L-System 字符串生成函数 (保持不变)
# ----------------------------------------------------------------------

def generate_l_system_string(axiom, rules, iterations):
    # ... (函数体与之前相同，确保它是随机的)
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
# 几何解释器部分 (最终稳定版 - 函数式递归)
# ----------------------------------------------------------------------

def parse_and_subdivide(l_string, rect):
    x, y, w, h = rect
    final_rects = []

    if not l_string:
        return "", []

    char = l_string[0]
    rest_string = l_string[1:]

    # ------------------ F: 终止/填充 ------------------
    if char == 'F':
        if w > MIN_SIZE and h > MIN_SIZE:
            final_rects.append((x, y, w, h, random.choice(COLORS)))
        return rest_string, final_rects 

    # ------------------ H/V: 分割操作 ------------------
    elif char == 'H' or char == 'V':
        
        # 如果尺寸太小，无法再容纳线条和两个子矩形，则强制终止并填充
        if (char == 'H' and h < 2 * MIN_SIZE + LINE_WIDTH) or \
           (char == 'V' and w < 2 * MIN_SIZE + LINE_WIDTH):
            if w > MIN_SIZE and h > MIN_SIZE:
                 final_rects.append((x, y, w, h, random.choice(COLORS)))
            return rest_string, final_rects
            
        # 选择分割比例
        split_ratio = random.choice(SPLIT_RATIOS)
        
        # --- 1. 计算分割和线条空间 ---
        if char == 'H': # 水平分割
            # S1 (上部分) 的总高度
            total_h1 = h * split_ratio
            
            # 实际 S1 高度，线条在中间
            rect1 = (x, y, w, total_h1 - LINE_WIDTH / 2)
            
            # 黑色线条矩形
            line_rect = (x, y + total_h1 - LINE_WIDTH / 2, w, LINE_WIDTH)
            final_rects.append((line_rect[0], line_rect[1], line_rect[2], line_rect[3], 'black'))
            
            # S2 (下部分)
            rect2 = (x, y + total_h1 + LINE_WIDTH / 2, w, h - total_h1 - LINE_WIDTH / 2)
            
        else: # V (垂直分割)
            # S1 (左部分) 的总宽度
            total_w1 = w * split_ratio
            
            # 实际 S1 宽度
            rect1 = (x, y, total_w1 - LINE_WIDTH / 2, h)
            
            # 黑色线条矩形
            line_rect = (x + total_w1 - LINE_WIDTH / 2, y, LINE_WIDTH, h)
            final_rects.append((line_rect[0], line_rect[1], line_rect[2], line_rect[3], 'black'))
            
            # S2 (右部分)
            rect2 = (x + total_w1 + LINE_WIDTH / 2, y, w - total_w1 - LINE_WIDTH / 2, h)

        # --- 2. 递归处理 S1 ---
        if rest_string and rest_string[0] == '[':
            rest_string = rest_string[1:] # 跳过 '['
            remaining_after_s1, rects_s1 = parse_and_subdivide(rest_string, rect1)
            final_rects.extend(rects_s1)
            rest_string = remaining_after_s1
            
            if rest_string and rest_string[0] == ']':
                rest_string = rest_string[1:] # 跳过 ']'

        # --- 3. 递归处理 S2 ---
        if rest_string and rest_string[0] == '[':
            rest_string = rest_string[1:] # 跳过 '['
            remaining_after_s2, rects_s2 = parse_and_subdivide(rest_string, rect2)
            final_rects.extend(rects_s2)
            rest_string = remaining_after_s2
            
            if rest_string and rest_string[0] == ']':
                rest_string = rest_string[1:] # 跳过 ']'

        return rest_string, final_rects
    
    # ------------------ [: 栈操作符 ------------------
    elif char == ']':
        # 遇到结束符，返回父层级，将剩余字符串继续向上传递
        return rest_string, []

    # 遇到未定义符号，直接跳过
    return rest_string, []

def interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)):
    """外部调用函数"""
    _, final_rects = parse_and_subdivide(l_string, initial_rect)
    return final_rects

# ----------------------------------------------------------------------
# 绘图函数 (移除矩形边缘线，因为我们现在有实体线条)
# ----------------------------------------------------------------------
def plot_mondrian_composition(rect_data, title="Mondrian-esque Composition"):
    fig, ax = plt.subplots(1, figsize=(8, 8))
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    
    # 初始背景填充为白色 (底色)
    ax.add_patch(patches.Rectangle((0, 0), 1, 1, facecolor='white', linewidth=0)) 

    for x, y, w, h, color in rect_data:
        # **关键修正：移除 edgecolor。线条现在是独立的黑色矩形**
        rect = patches.Rectangle((x, y), w, h, linewidth=0, facecolor=color)
        ax.add_patch(rect)
        
    plt.title(title)
    plt.show()

# ----------------------------------------------------------------------
# 主程序执行 (移除随机种子)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # *** 移除 random.seed(42) 以恢复随机性 ***
    
    print("--- 生成 L 系统字符串（早期蒙德里安构图）---")
    axiom = 'S'
    iterations = 5 
    l_string = generate_l_system_string(axiom, MONDRIAN_EARLY_RULES, iterations)
    print(f"生成的字符串长度: {len(l_string)}")

    print("\n--- 解释 L 系统字符串并生成矩形数据 (最终稳定版) ---")
    rectangles = interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)) 
    print(f"生成了 {len(rectangles)} 个填充/线条矩形。")

    print("\n--- 绘制蒙德里安风格的构图 ---")
    plot_mondrian_composition(rectangles, title=f"Mondrian-esque Composition (Iterations: 5, Rects: {len(rectangles)})")

    # 简单分析：计算一些指标
    total_area = sum(w * h for _, _, w, h, _ in rectangles)
    # total_area 现在应该接近 1.0
    print(f"所有填充矩形和线条的总面积: {total_area:.4f}")
    
    # 我们可以计算颜色分布
    color_counts = {}
    for _, _, _, _, color in rectangles:
        color_counts[color] = color_counts.get(color, 0) + 1
    print(f"颜色分布: {color_counts}")