import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import datetime
from pathlib import Path
import sys 

# ----------------------------------------------------------------------
# L-系统配置 (V4.0)
# ----------------------------------------------------------------------
MONDRIAN_EARLY_RULES = {
    'S': [
        (0.35, 'H[S][S]'), 
        (0.25, 'V[S][S]'), 
        (0.40, 'F')        
    ],
}
COLORS = ['white'] * 40 + ['red', 'yellow', 'blue'] * 4 + ['0.9']*10
SPLIT_RATIOS = [0.25, 0.33, 0.4, 0.6, 0.67, 0.75]
MIN_SIZE = 0.005 

# --- 关键修改 1: 随机线条粗细配置 ---
# 边线的基础宽度和浮动范围
LINE_WIDTH_BASE = 0.005
LINE_WIDTH_DEVIATION = 0.001 
LINE_WIDTH_MIN = LINE_WIDTH_BASE - LINE_WIDTH_DEVIATION
LINE_WIDTH_MAX = LINE_WIDTH_BASE + LINE_WIDTH_DEVIATION
# ------------------------------------

# ----------------------------------------------------------------------
# 核心函数 (生成字符串、解析、解释器逻辑保持稳定)
# ----------------------------------------------------------------------

# ... (generate_l_system_string 函数体不变) ...
def generate_l_system_string(axiom, rules, iterations):
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

# ----------------------------------------------------------------------------------
# parse_and_subdivide 函数 (关键修改 1: 引入随机线条宽度)
# ----------------------------------------------------------------------------------
def parse_and_subdivide(l_string, rect, required_colors_set):
    x, y, w, h = rect
    final_rects = []

    if not l_string:
        return "", []

    char = l_string[0]
    rest_string = l_string[1:]

    # F 填充逻辑保持不变
    if char == 'F':
        if w > MIN_SIZE and h > MIN_SIZE:
            fill_color = random.choice(COLORS)
            if required_colors_set:
                fill_color = required_colors_set.pop() 
            final_rects.append((x, y, w, h, fill_color))
        return rest_string, final_rects 

    elif char == 'H' or char == 'V':
        
        # --- 关键修改 1.1: 每次分割时生成一个随机线条宽度 ---
        current_line_width = random.uniform(LINE_WIDTH_MIN, LINE_WIDTH_MAX)
        
        # 使用随机宽度检查最小尺寸
        if (char == 'H' and h < 2 * MIN_SIZE + current_line_width) or \
           (char == 'V' and w < 2 * MIN_SIZE + current_line_width):
            if w > MIN_SIZE and h > MIN_SIZE:
                 fill_color = random.choice(COLORS)
                 if required_colors_set:
                     fill_color = required_colors_set.pop()
                 final_rects.append((x, y, w, h, fill_color))
            return rest_string, final_rects
            
        split_ratio = random.choice(SPLIT_RATIOS)
        
        # --- 关键修改 1.2: 使用 current_line_width 代替常量 ---
        if char == 'H':
            total_h1 = h * split_ratio
            rect1 = (x, y, w, total_h1 - current_line_width / 2)
            line_rect = (x, y + total_h1 - current_line_width / 2, w, current_line_width)
            rect2 = (x, y + total_h1 + current_line_width / 2, w, h - total_h1 - current_line_width / 2)
        else: # V
            total_w1 = w * split_ratio
            rect1 = (x, y, total_w1 - current_line_width / 2, h)
            line_rect = (x + total_w1 - current_line_width / 2, y, current_line_width, h)
            rect2 = (x + total_w1 + current_line_width / 2, y, w - total_w1 - current_line_width / 2, h)

        final_rects.append((line_rect[0], line_rect[1], line_rect[2], line_rect[3], 'black'))
        # ... (递归调用逻辑不变) ...
        
        if rest_string and rest_string[0] == '[':
            rest_string = rest_string[1:]
            remaining_after_s1, rects_s1 = parse_and_subdivide(rest_string, rect1, required_colors_set)
            final_rects.extend(rects_s1)
            rest_string = remaining_after_s1
            if rest_string and rest_string[0] == ']':
                rest_string = rest_string[1:]

        if rest_string and rest_string[0] == '[':
            rest_string = rest_string[1:]
            remaining_after_s2, rects_s2 = parse_and_subdivide(rest_string, rect2, required_colors_set)
            final_rects.extend(rects_s2)
            rest_string = remaining_after_s2
            if rest_string and rest_string[0] == ']':
                rest_string = rest_string[1:]

        return rest_string, final_rects
    
    elif char == ']':
        return rest_string, []

    return rest_string, []

# ----------------------------------------------------------------------------------
# interpret_mondrian_functional 函数 (关键修改 2: 双色保证)
# ----------------------------------------------------------------------------------
def interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)):
    """随机选择两种原色作为强制保证颜色"""
    all_primaries = ['red', 'yellow', 'blue']
    # --- 关键修改 2: 随机选择两个作为强制保证 ---
    required_colors_list = random.sample(all_primaries, 2)
    required_colors = set(required_colors_list)
    
    _, final_rects = parse_and_subdivide(l_string, initial_rect, required_colors)
    return final_rects

# ... (plot_and_save_composition 函数体不变) ...
def plot_and_save_composition(rect_data, file_path):
    fig, ax = plt.subplots(1, figsize=(8, 8))
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    
    ax.add_patch(patches.Rectangle((0, 0), 1, 1, facecolor='white', linewidth=0)) 

    for x, y, w, h, color in rect_data:
        rect = patches.Rectangle((x, y), w, h, linewidth=0, facecolor=color)
        ax.add_patch(rect)
        
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig) 

# ... (主程序 if __name__ == '__main__': 保持不变) ...
if __name__ == '__main__':
    
    NUM_IMAGES = 100
    BASE_DIR = "mondrian_compositions"
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR_NAME = f"Run_{timestamp}"
    
    output_path = Path(BASE_DIR) / OUTPUT_DIR_NAME
    
    try:
        Path(BASE_DIR).mkdir(exist_ok=True)
        output_path.mkdir(exist_ok=True)
        print(f"--- 图像将保存到新的唯一目录: {output_path.resolve()} ---")
    except Exception as e:
        print(f"致命错误: 无法创建输出目录。请检查权限。", file=sys.stderr)
        print(f"错误详情: {e}", file=sys.stderr)
        sys.exit(1)

    total_rects = 0
    axiom = 'S'
    iterations = 5
    
    for i in range(1, NUM_IMAGES + 1):
        try:
            # 1. 强制首次分割
            l_string = ''
            while len(l_string) <= 1:
                l_string = generate_l_system_string(axiom, MONDRIAN_EARLY_RULES, iterations)
            
            # 2. 解释并生成矩形数据
            rectangles = interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)) 
            
            if not rectangles:
                 print(f"警告: 图像 {i} 未能生成任何矩形。跳过保存。", file=sys.stderr)
                 continue 
                 
            # 3. 绘制并保存图像
            file_name = f"composition_{i:03d}.png"
            file_path = output_path / file_name
            plot_and_save_composition(rectangles, file_path)
            
            total_rects += len(rectangles)
            
            if i % 10 == 0 or i == 1:
                print(f"进度: {i}/{NUM_IMAGES} 张图像已保存。矩形数: {len(rectangles)}。")

        except Exception as e:
            print(f"\n致命错误: 图像 {i} 绘制或保存时发生异常。", file=sys.stderr)
            print(f"错误详情: {e}", file=sys.stderr)
            print("--- 终止批量生成 ---", file=sys.stderr)
            sys.exit(1)

    avg_rects = total_rects / NUM_IMAGES if NUM_IMAGES > 0 else 0
    print("\n--- 批量生成完成 ---")
    print(f"总共生成 {NUM_IMAGES} 张图像。")
    print(f"平均每张图像包含 {avg_rects:.1f} 个矩形/线条元素。")