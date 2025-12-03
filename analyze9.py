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
# L-系统配置 (V11.0)
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
MAX_RECT_DIMENSION = 1 / 12 # 约 0.0833
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
# parse_and_subdivide 函数 (关键修改 2: 严格尺寸与纵横比检查前置)
# ----------------------------------------------------------------------------------
def parse_and_subdivide(l_string, rect, required_colors_set):
    x, y, w, h = rect
    final_rects = []

    # --- 关键修改 2.1: 在函数最开始进行严格的尺寸和纵横比检查 ---
    if w < MIN_SIZE or h < MIN_SIZE: 
        return "", [] # 如果区域太小，直接终止，不绘制
        
    is_oversized = (w > MAX_RECT_DIMENSION or h > MAX_RECT_DIMENSION)
    aspect_ratio_bad = (max(w/h, h/w) > MAX_ASPECT_RATIO) if h != 0 and w != 0 else False

    if is_oversized or aspect_ratio_bad:
        # 如果当前区域 (rect) 尺寸过大或纵横比太差，
        # 强制将整个区域填充为白色，并停止进一步解析和递归。
        # 这确保了任何不符合尺寸要求的区域都变成留白，并且其内部不会再生成任何元素。
        final_rects.append((x, y, w, h, 'white'))
        return "", final_rects # 停止递归
    # -------------------------------------------------------------------

    if not l_string:
        return "", []

    char = l_string[0]
    rest_string = l_string[1:]

    if char == 'F': # 填充普通矩形
        # 到这里，矩形 (w, h) 已经是尺寸和纵横比都合格的了
        fill_color = random.choice(COLORS)
        if required_colors_set:
            fill_color = required_colors_set.pop() 
            
        final_rects.append((x, y, w, h, fill_color))
        return rest_string, final_rects 

    elif char == 'H' or char == 'V':
        
        current_line_width = random.uniform(LINE_WIDTH_MIN, LINE_WIDTH_MAX)
        
        # ... (省略尺寸检查) ...

        # 在 H/V 分割逻辑开始时选择分割比例
        split_ratio = random.choice(SPLIT_RATIOS)
        
        # 几何计算
        if char == 'H':
            total_h1 = h * split_ratio # 修正后的赋值
            rect1 = (x, y, w, total_h1 - current_line_width / 2)
            line_rect_space = (x, y + total_h1 - current_line_width / 2, w, current_line_width) 
            rect2 = (x, y + total_h1 + current_line_width / 2, w, h - total_h1 - current_line_width / 2)
        else: # V
            total_w1 = w * split_ratio # 修正后的赋值
            rect1 = (x, y, total_w1 - current_line_width / 2, h)
            line_rect_space = (x + total_w1 - current_line_width / 2, y, current_line_width, h) 
            rect2 = (x + total_w1 + current_line_width / 2, y, w - total_w1 - current_line_width / 2, h)

        # ... (后续生成线条小方块和递归调用逻辑不变) ...
        # 在 line_rect_space 中生成彩色小方块 (模拟破碎线条)
        lx, ly, lw, lh = line_rect_space
        
        is_horizontal = lw > lh
        main_length = lw if is_horizontal else lh
        segment_dimension = lw if is_horizontal else lh # 线条的宽度/高度

        # --- 关键修改 2.2: 线条小方块的尺寸也严格受 MAX_RECT_DIMENSION 限制 ---
        # 计算每个小方块的理想长度，并限制在 MAX_RECT_DIMENSION 内
        desired_segment_size = LINE_WIDTH_BASE # 之前是LINE_WIDTH_BASE
        actual_segment_size = min(desired_segment_size, MAX_RECT_DIMENSION) # 确保单个段不超过最大尺寸

        num_segments = max(1, int(main_length / actual_segment_size)) 
        
        # 确保每个小方块的实际绘制尺寸不会超出 MAX_RECT_DIMENSION
        final_segment_length = main_length / num_segments
        final_segment_dimension = min(segment_dimension, MAX_RECT_DIMENSION) # 垂直于线条方向的尺寸
        
        for seg_i in range(num_segments):
            # 每个小方块的绘制区域
            current_x = lx + seg_i * final_segment_length if is_horizontal else lx
            current_y = ly if is_horizontal else ly + seg_i * final_segment_length
            current_w = final_segment_length if is_horizontal else final_segment_dimension
            current_h = final_segment_dimension if is_horizontal else final_segment_length

            # 只有当小方块自身的尺寸合格时才绘制彩色，否则强制白色
            if current_w >= MIN_SIZE and current_h >= MIN_SIZE and \
               current_w <= MAX_RECT_DIMENSION and current_h <= MAX_RECT_DIMENSION and \
               max(current_w/current_h, current_h/current_w) <= MAX_ASPECT_RATIO:
                if random.random() < 0.85: 
                    fill_color = random.choice(GRID_COLORS)
                else: 
                    fill_color = 'white' 
            else:
                fill_color = 'white' # 不合格的线条小方块也强制白色

            final_rects.append((current_x, current_y, current_w, current_h, fill_color))
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
    OUTPUT_DIR_NAME = f"Run_BoogieWoogie_V11_{timestamp}"
    
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
    # 迭代次数增加到 8
    iterations = 8 
    
    for i in range(1, NUM_IMAGES + 1):
        try:
            l_string = ''
            while len(l_string) < 10 or len(l_string) > 1000: 
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