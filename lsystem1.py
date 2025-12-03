import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# --- 1. L-System 几何体生成：使用迭代函数系统 (IFS) 生成谢尔宾斯基点集 ---
def generate_sierpinski_points(num_points=10000, initial_points=[(0, 0), (1, 0), (0.5, np.sqrt(3)/2)]):
    """
    通过迭代函数系统 (IFS) 生成谢尔宾斯基垫片的点集。
    """
    P0 = initial_points[0]
    P1 = initial_points[1]
    P2 = initial_points[2]
    
    # 随机选择一个初始点
    points = [P0]
    current_point = P0

    for _ in range(num_points):
        # 随机选择一个初始顶点 (0, 1, or 2)
        target_vertex = initial_points[np.random.randint(3)]
        
        # 将当前点移动到当前点与目标顶点之间距离的一半
        next_x = 0.5 * (current_point[0] + target_vertex[0])
        next_y = 0.5 * (current_point[1] + target_vertex[1])
        
        current_point = (next_x, next_y)
        points.append(current_point)
        
    return np.array(points)

# --- 2. 盒计数法核心实现 ---
def box_counting_dimension(points, min_log_eps=-5, max_log_eps=0, num_scales=15):
    """
    计算给定点集的分形维数。
    
    Args:
        points: (N, 2) 形状的 NumPy 数组，表示点的坐标。
        min_log_eps, max_log_eps: 盒子尺度的对数范围。
        num_scales: 要测试的盒子尺度数量。
    
    Returns:
        float: 计算出的盒计数维数。
    """
    X = points[:, 0]
    Y = points[:, 1]
    
    # 确定计算区域的边界
    min_x, max_x = X.min(), X.max()
    min_y, max_y = Y.min(), Y.max()
    
    # 定义尺度的对数范围 (log(1/epsilon))
    log_1_epsilons = np.linspace(min_log_eps, max_log_eps, num_scales)
    
    counts = [] # 存储 N(epsilon)
    log_epsilons = -log_1_epsilons # 存储 log(epsilon)

    for log_eps in log_epsilons:
        epsilon = np.exp(log_eps) # 盒子边长
        
        # 计算网格划分
        bins_x = np.arange(min_x, max_x + epsilon, epsilon)
        bins_y = np.arange(min_y, max_y + epsilon, epsilon)
        
        # 将点分配到网格中 (二维直方图)
        # H 是一个二维数组，其中每个元素是该盒子中点的数量
        H, _, _ = np.histogram2d(X, Y, bins=[bins_x, bins_y])
        
        # 统计非空盒子的数量 N(epsilon)
        count = np.sum(H > 0)
        counts.append(count)
        
    log_counts = np.log(counts)
    
    # 执行线性回归：拟合 log(N(epsilon)) 和 log(1/epsilon)
    # log(N) = D * log(1/epsilon) + C
    slope, intercept, r_value, p_value, std_err = linregress(log_1_epsilons, log_counts)
    
    # 斜率即为分形维数 D
    dimension = slope
    
    # 可视化结果
    plt.figure(figsize=(8, 6))
    plt.plot(log_1_epsilons, log_counts, 'o', label='Data Points')
    plt.plot(log_1_epsilons, intercept + slope * log_1_epsilons, 'r', 
             label=f'Fit: D={dimension:.4f} (R^2={r_value**2:.4f})')
    plt.xlabel(r'$\log(1/\epsilon)$')
    plt.ylabel(r'$\log(N(\epsilon))$')
    plt.title('Box-Counting Method for Fractal Dimension')
    plt.legend()
    plt.grid(True, linestyle='--')
    plt.show()
    
    return dimension

# --- 主程序执行 ---
if __name__ == '__main__':
    print("--- 1. 生成谢尔宾斯基垫片点集 ---")
    sierpinski_points = generate_sierpinski_points(num_points=50000)
    
    # 可视化生成的点集
    plt.figure(figsize=(6, 6))
    plt.plot(sierpinski_points[:, 0], sierpinski_points[:, 1], 'k.', markersize=0.5)
    plt.title('Generated Sierpinski Gasket Point Set')
    plt.axis('equal')
    plt.show()
    
    print("\n--- 2. 执行盒计数法计算分形维数 ---")
    D = box_counting_dimension(sierpinski_points, min_log_eps=-5, max_log_eps=-0.5, num_scales=20)
    
    print(f"\n计算出的谢尔宾斯基垫片分形维数 D ≈ {D:.4f}")
    print(f"理论值 D_theory = log(3)/log(2) ≈ 1.5850")