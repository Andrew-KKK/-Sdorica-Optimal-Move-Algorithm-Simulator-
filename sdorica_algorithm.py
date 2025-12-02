import copy
from typing import List, Tuple, Dict, Optional
from soul_board_simulator import SoulOrbSimulator, SoulOrb 

class SdoricaSolver:
    """
    Sdorica 最佳操作演算法求解器。
    職責：
    1. 管理決策邏輯 (貪婪、搜尋等)
    2. 管理超參數 (優先序、探索獎勵)
    3. 計算操作分數
    """
    def __init__(self, priority_list: Dict[str, int], orb_count_bonus: int = 9):
        """
        初始化求解器，並設定所有與決策相關的超參數。
        :param priority_list: 挖掘 (Exploitation) 的形狀優先分數表
        :param orb_count_bonus: 探索 (Exploration) 的基礎獎勵 (每顆魂芯的分數)
        """
        self.priority_list = priority_list
        self.orb_count_bonus = orb_count_bonus

    def find_all_valid_moves(self, sim: SoulOrbSimulator) -> List[dict]:
        """
        窮舉當前魂盤上所有合法的操作。
        (邏輯不變，只是從 simulator 取得規則)
        """
        valid_moves = []
        seen_moves = set()

        for r in range(sim.rows):
            for c in range(sim.cols):
                for shape_name, template in sim.SHAPE_TEMPLATES.items():
                    coords = []
                    possible = True
                    for dr, dc in template:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < sim.rows and 0 <= nc < sim.cols):
                            possible = False
                            break
                        coords.append((nr, nc))
                    if not possible: continue

                    first_r, first_c = coords[0]
                    base_color = sim.board[first_r][first_c].color
                    if base_color == "EMPTY": continue
                        
                    color_match = True
                    for cr, cc in coords[1:]:
                        if sim.board[cr][cc].color != base_color:
                            color_match = False
                            break
                    if not color_match: continue

                    try:
                        validated_shape_name = sim._validate_shape(coords)
                        coords_set = frozenset(coords)
                        if coords_set not in seen_moves:
                            seen_moves.add(coords_set)
                            valid_moves.append({
                                'coords': coords,
                                'shape': validated_shape_name,
                                'color': base_color,
                                'orb_count': len(coords)
                            })
                    except ValueError:
                        continue
        return valid_moves

    def calculate_score(self, move: dict) -> int:
        """
        計算單一操作的分數。
        使用 self.priority_list 和 self.orb_count_bonus
        """
        shape_name = move['shape']
        
        # 1. 挖掘分數 (Priority)
        p_score = 0
        # 優先檢查具體名稱
        if shape_name in self.priority_list:
            p_score = self.priority_list[shape_name]
        else:
            # 檢查群組名稱
            parts = shape_name.rsplit('_', 1)
            group_name = parts[0] if len(parts) > 1 else shape_name
            if group_name in self.priority_list:
                p_score = self.priority_list[group_name]
        
        # 2. 探索分數 (Exploration)
        e_score = self.orb_count_bonus * move['orb_count']
        
        return p_score + e_score

    def get_best_move_greedy(self, sim: SoulOrbSimulator) -> Optional[dict]:
        """
        [貪婪策略] 找出當前分數最高的一步。
        """
        all_moves = self.find_all_valid_moves(sim)
        
        if not all_moves:
            return None
            
        best_move = None
        highest_score = -float('inf')
        
        print(f"找到 {len(all_moves)} 種可能的操作...")
        
        for move in all_moves:
            score = self.calculate_score(move)
            
            # 除錯用: 顯示分數細節
            # print(f"  - {move['shape']}: {score}")
            
            if score > highest_score:
                highest_score = score
                best_move = move
                
        if best_move:
            print(f"=> 最佳操作: {best_move['shape']} ({best_move['color']}), 分數: {highest_score}")
        return best_move

# --- 測試區 ---
if __name__ == "__main__":
    print("=== 魂盤模擬器測試 ===")
    # 1. 初始化模擬器 (只負責規則)
    skills_to_test = ["1-orb", "2-orb", "4-orb-square", "4-orb-L", "4-orb-I"]
    sim = SoulOrbSimulator(skills=skills_to_test, seed=12345)
    
    # 2. 定義超參數 (現在全部由演算法管理)
    ai_priority = {
        "1-orb": 10,
        "2-orb": 50,
        "4-orb-square": 100,
        "4-orb-L": 80, 
        "4-orb-I": 80   
    }
    exploration_bonus = 9
    
    # 3. 初始化求解器，傳入所有決策參數
    solver = SdoricaSolver(priority_list=ai_priority, orb_count_bonus=exploration_bonus)
    
    print("\n=== 初始盤面 ===")
    sim.display_board()
    
    # 4. 執行貪婪決策
    print("\n=== 演算法運算中 (Greedy) ===")
    # 現在不需要傳參數給 get_best_move_greedy 了，因為 solver 已經記住了
    best_move = solver.get_best_move_greedy(sim)
    
    if best_move:
        print(f"\n=== 執行操作: {best_move['shape']} ===")
        sim.handle_operation(best_move['coords'])
        sim.display_board()
    else:
        print("無可執行的操作")