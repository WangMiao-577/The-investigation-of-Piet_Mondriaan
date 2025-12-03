import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import datetime
from pathlib import Path
import sys 

# --- 颜色配置 ---
DEEPER_YELLOW = '#FFD700'  # 深黄色 (黄金色)
DEEPER_GRAY = '#C0C0C0'    # 深灰色 (银灰色)
# ----------------

# ----------------------------------------------------------------------
# L-系统配置 (V10.0)
# ----------------------------------------------------------------------
MONDRIAN_EARLY_RULES = {
    'S': [
        (0.40, 'H[S][S]'), 
        (0.40, 'V[S][S]'), 
        (0.20, 'F')        # 终止概率保持 20%
    ],
}

# 颜色比例 (保持高比例的白色和中性色)
COLORS = ['white'] * 50 + ['red', DEEPER_YELLOW, 'blue'] * 2 + [DEEPER_GRAY] * 15 

# 四色线条网格
GRID_COLORS = ['red', DEEPER_YELLOW, 'blue', DEEPER_GRAY] * 4

SPLIT_RATIOS = [0.25, 0.33, 0.4, 0.6, 0.67, 0.75]
MIN_SIZE = 0.005 # 最小可绘制尺寸

# 线条宽度配置
LINE_WIDTH_BASE = 0.010      
LINE_WIDTH_DEVIATION = 0.002 
LINE_WIDTH_MIN = LINE_WIDTH_BASE - LINE_WIDTH_DEVIATION
LINE_WIDTH_MAX = LINE_WIDTH_BASE + LINE_WIDTH_DEVIATION

# --- 关键修改 1: 严格最大尺寸限制 ---
# 任何色块的横向和纵向宽度不得超过页面宽度的 1/12
MAX_RECT_DIMENSION = 1 / 20 
# ------------------------------------

# 纵横比约束
MAX_ASPECT_RATIO = 1.5

# ----------------------------------------------------------------------
# L-System 字符串生成函数 (保持不变)
# ----------------------------------------------------------------------
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
# parse_and_subdivide 函数 (关键修改 2: 严格尺寸与纵横比检查)
# ----------------------------------------------------------------------------------
def parse_and_subdivide(l_string, rect, required_colors_set):
    x, y, w, h = rect
    final_rects = []

    if not l_string:
        return "", []

    char = l_string[0]
    rest_string = l_string[1:]

    if char == 'F': # 填充普通矩形
        # --- 关键修改 2.1: 在 F 填充前进行严格尺寸和纵横比检查 ---
        if w < MIN_SIZE or h < MIN_SIZE: # 小于最小尺寸，直接跳过
            return rest_string, final_rects
            
        is_oversized = (w > MAX_RECT_DIMENSION or h > MAX_RECT_DIMENSION)
        aspect_ratio_bad = (max(w/h, h/w) > MAX_ASPECT_RATIO) if h != 0 and w !=0 else False

        if is_oversized or aspect_ratio_bad:
            # 如果尺寸过大或纵横比太差，强制填充为白色，增加留白，消除丑陋的细长块
            # 不再尝试裁剪，直接将整个区域视为留白
            final_rects.append((x, y, w, h, 'white'))
            return rest_string, final_rects # 不再递归
        # ---------------------------------------------------------
            
        # 尺寸和纵横比都合格，正常选择颜色
        fill_color = random.choice(COLORS)
        if required_colors_set:
            fill_color = required_colors_set.pop() 
            
        final_rects.append((x, y, w, h, fill_color))
        return rest_string, final_rects 

    elif char == 'H' or char == 'V':
        
        current_line_width = random.uniform(LINE_WIDTH_MIN, LINE_WIDTH_MAX)
        
        # 检查是否小于最小尺寸
        if (char == 'H' and h < 2 * MIN_SIZE + current_line_width) or \
           (char == 'V' and w < 2 * MIN_SIZE + current_line_width):
            if w > MIN_SIZE and h > MIN_SIZE:
                 final_rects.append((x, y, w, h, 'white')) # 小尺寸区域强制留白
            return rest_string, final_rects
            
        split_ratio = random.choice(SPLIT_RATIOS)
        
        # 几何计算
        if char == 'H':
            total_h1 = h * split_ratio
            rect1 = (x, y, w, total_h1 - current_line_width / 2)
            line_rect_space = (x, y + total_h1 - current_line_width / 2, w, current_line_width) 
            rect2 = (x, y + total_h1 + current_line_width / 2, w, h - total_h1 - current_line_width / 2)
        else: # V
            total_w1 = w * split_ratio
            rect1 = (x, y, total_w1 - current_line_width / 2, h)
            line_rect_space = (x + total_w1 - current_line_width / 2, y, current_line_width, h) 
            rect2 = (x + total_w1 + current_line_width / 2, y, w - total_w1 - current_line_width / 2, h)

        # 在 line_rect_space 中生成彩色小方块 (模拟破碎线条)
        lx, ly, lw, lh = line_rect_space
        
        is_horizontal = lw > lh
        main_length = lw if is_horizontal else lh
        segment_dimension = lw if is_horizontal else lh
        
        # --- 关键修改 2.2: 线条小方块的尺寸也受 MAX_RECT_DIMENSION 限制 ---
        # 确保线条的每个小方块都不会太长
        num_segments = max(1, int(main_length / MAX_RECT_DIMENSION)) # 至少分割为 MAX_RECT_DIMENSION 的长度
        segment_size = main_length / num_segments
        
        # 进一步限制 segment_size 不超过 MAX_RECT_DIMENSION
        if segment_size > MAX_RECT_DIMENSION:
            segment_size = MAX_RECT_DIMENSION
            num_segments = int(main_length / segment_size) # 重新计算段数

        for seg_i in range(num_segments):
            
            if random.random() < 0.85: 
                fill_color = random.choice(GRID_COLORS)
            else: 
                fill_color = 'white' 

            if is_horizontal:
                # 绘制时确保不超出 MAX_RECT_DIMENSION
                actual_segment_width = min(segment_size, MAX_RECT_DIMENSION)
                final_rects.append((lx + seg_i * segment_size, ly, actual_segment_width, segment_dimension, fill_color))
            else: 
                actual_segment_height = min(segment_size, MAX_RECT_DIMENSION)
                final_rects.append((lx, ly + seg_i * segment_size, segment_dimension, actual_segment_height, fill_color))
        # -------------------------------------------------------------------
        
        # 递归调用
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

# ... (interpret_mondrian_functional, plot_and_save_composition 保持不变) ...
def interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)):
    all_primaries = ['red', DEEPER_YELLOW, 'blue']
    required_colors_list = random.sample(all_primaries, 2)
    required_colors = set(required_colors_list)
    _, final_rects = parse_and_subdivide(l_string, initial_rect, required_colors)
    return final_rects

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

if __name__ == '__main__':
    
    NUM_IMAGES = 100
    BASE_DIR = "mondrian_compositions"
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR_NAME = f"Run_BoogieWoogie_V10_{timestamp}"
    
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
    # 关键修改 3: 迭代次数增加到 8
    iterations = 8 
    
    for i in range(1, NUM_IMAGES + 1):
        try:
            l_string = ''
            # 确保生成的字符串长度适中
            while len(l_string) < 10 or len(l_string) > 1000: # 限制最大长度防止计算量过大
                l_string = generate_l_system_string(axiom, MONDRIAN_EARLY_RULES, iterations)
            
            rectangles = interpret_mondrian_functional(l_string, initial_rect=(0, 0, 1, 1)) 
            
            if not rectangles:
                 print(f"警告: 图像 {i} 未能生成任何矩形。跳过保存。", file=sys.stderr)
                 continue 
                 
            file_name = f"composition_{i:03d}.png"
            file_path = output_path / file_name
            plot_and_save_composition(rectangles, file_path)
            
            total_rects += len(rectangles)
            
            if i % 10 == 0 or i == 1:
                print(f"进度: {i}/{NUM_IMAGES} 张图像已保存。矩形数: {len(rectangles)}个。")

        except Exception as e:
            print(f"\n致命错误: 图像 {i} 绘制或保存时发生异常。", file=sys.stderr)
            print(f"错误详情: {e}", file=sys.stderr)
            print("--- 终止批量生成 ---", file=sys.stderr)
            sys.exit(1)

    avg_rects = total_rects / NUM_IMAGES if NUM_IMAGES > 0 else 0
    print("\n--- 批量生成完成 ---")
    print(f"总共生成 {NUM_IMAGES} 张图像。")
    print(f"平均每张图像包含 {avg_rects:.1f} 个矩形/线条元素。")