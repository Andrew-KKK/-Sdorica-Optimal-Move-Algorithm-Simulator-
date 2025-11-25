import copy
from typing import List, Tuple, Dict, Optional
# 這裡我們 import 您上傳的模擬器檔案
from soul_board_simulator import SoulOrbSimulator, SoulOrb 

class SdoricaSolver:
    """
    Sdorica 最佳操作演算法求解器
    """
    def __init__(self):
        pass

    def find_all_valid_moves(self, sim: SoulOrbSimulator) -> List[dict]:
        """
        窮舉當前魂盤上所有合法的操作。
        
        :param sim: 模擬器實例 (包含當前的 board 和 valid_skills)
        :return: 一個列表，每個元素是代表一個操作的字典:
                 {
                     'coords': List[Tuple[int, int]], 
                     'shape': str, 
                     'color': str,
                     'orb_count': int
                 }
        """
        valid_moves = []
        
        # 為了避免重複 (例如同一個 4-orb 被偵測多次)，我們可以使用 set 來存已驗證過的 coords (轉成 frozenset)
        seen_moves = set()

        # 遍歷魂盤上的每一個位置作為 "基準點" (origin)
        for r in range(sim.rows):
            for c in range(sim.cols):
                # 遍歷所有已知的形狀模板
                for shape_name, template in sim.SHAPE_TEMPLATES.items():
                    
                    # 1. 建構絕對座標
                    coords = []
                    possible = True
                    
                    # 嘗試將模板套用到當前 (r, c)
                    for dr, dc in template:
                        nr, nc = r + dr, c + dc
                        
                        # 檢查邊界
                        if not (0 <= nr < sim.rows and 0 <= nc < sim.cols):
                            possible = False
                            break
                        coords.append((nr, nc))
                    
                    if not possible:
                        continue

                    # 2. 檢查顏色一致性 (且不能是 EMPTY)
                    first_r, first_c = coords[0]
                    base_color = sim.board[first_r][first_c].color
                    
                    if base_color == "EMPTY":
                        continue
                        
                    color_match = True
                    for cr, cc in coords[1:]:
                        if sim.board[cr][cc].color != base_color:
                            color_match = False
                            break
                    
                    if not color_match:
                        continue

                    # 3. 驗證是否為 valid_skills 允許的操作
                    # 我們直接呼叫模擬器的驗證函式，這樣邏輯最強健
                    try:
                        # 注意: 這邊 coords 順序不重要，_validate_shape 會處理
                        validated_shape_name = sim._validate_shape(coords)
                        
                        # 4. 儲存結果 (避免重複)
                        # 因為我們是遍歷 (r,c) 套用模板，理論上同一個形狀只會被其 "左上角" 觸發一次
                        # 但為了保險，我們還是用 coords set 檢查一下
                        coords_set = frozenset(coords)
                        if coords_set not in seen_moves:
                            seen_moves.add(coords_set)
                            valid_moves.append({
                                'coords': coords,
                                'shape': validated_shape_name, # e.g., "4-orb-L_1"
                                'color': base_color,
                                'orb_count': len(coords)
                            })
                            
                    except ValueError:
                        # 不合法的形狀 (不在 valid_skills 中)
                        continue
                        
        return valid_moves

    def calculate_score(self, move: dict, priority_list: Dict[str, int], orb_bonus: int) -> int:
        """
        計算單一操作的分數。
        Score = Priority_Score (挖掘) + Exploration_Score (探索)
        """
        shape_name = move['shape']
        
        # 1. 取得挖掘分數 (Priority)
        # 支援群組查找: 先找具體名稱 (e.g. "2-orb_v"), 再找群組名稱 (e.g. "2-orb")
        p_score = 0
        if shape_name in priority_list:
            p_score = priority_list[shape_name]
        else:
            # 嘗試分割群組 (e.g. "4-orb-L_1" -> "4-orb-L")
            # 這裡假設命名規則是用 '_' 或 '-' 分隔，我們嘗試幾種常見組合
            # 根據 simulator 的邏輯，我們使用 rsplit('_', 1)
            parts = shape_name.rsplit('_', 1)
            group_name = parts[0] if len(parts) > 1 else shape_name
            
            if group_name in priority_list:
                p_score = priority_list[group_name]
            else:
                # 如果還是找不到，分數為 0 (或者可以設一個預設值)
                p_score = 0
        
        # 2. 取得探索分數 (Exploration)
        # 獎勵 = 單顆價值 * 消除數量
        e_score = orb_bonus * move['orb_count']
        
        return p_score + e_score

    def get_best_move_greedy(self, sim: SoulOrbSimulator, priority_list: Dict[str, int]) -> Optional[dict]:
        """
        [最簡單演算法] 貪婪策略 (Greedy)
        找出當前分數最高的一步。
        """
        # 1. 窮舉
        all_moves = self.find_all_valid_moves(sim)
        
        if not all_moves:
            return None
            
        best_move = None
        highest_score = -float('inf')
        
        print(f"找到 {len(all_moves)} 種可能的操作...")
        
        # 2. 評分與決策
        for move in all_moves:
            score = self.calculate_score(move, priority_list, sim.ORB_COUNT_BONUS)
            
            # 用於除錯顯示: 取消註解可以看到每一個動作的分數
            # print(f"  - {move['shape']} ({move['color']}): {score} 分")
            
            if score > highest_score:
                highest_score = score
                best_move = move
                
        if best_move:
            print(f"=> 最佳操作: {best_move['shape']} ({best_move['color']}), 分數: {highest_score}")
        return best_move

# --- 測試區 ---
if __name__ == "__main__":
    # 1. 初始化模擬器
    # 我們允許 1, 2, 4 (方形), 4 (L形), 4 (I形)
    skills_to_test = ["1-orb", "2-orb", "4-orb-square", "4-orb-L", "4-orb-I"]
    
    # 設定探索獎勵 = 9 (略低於 1-orb 的 priority)
    sim = SoulOrbSimulator(skills=skills_to_test, orb_bonus=9)
    
    # 2. 設定 AI 的優先序列表 (Priority List)
    # 這代表 "挖掘" 的價值
    ai_priority = {
        "1-orb": 10,
        "2-orb": 50,
        "4-orb-square": 100,
        "4-orb-L": 80,  # 群組名稱
        "4-orb-I": 80   # 群組名稱
    }
    
    # 3. 初始化求解器
    solver = SdoricaSolver()
    
    print("\n=== 初始盤面 ===")
    sim.display_board()
    
    # 4. 執行一次貪婪決策
    print("\n=== 演算法運算中 (Greedy) ===")
    best_move = solver.get_best_move_greedy(sim, ai_priority)
    
    if best_move:
        # 5. 執行操作
        print(f"\n=== 執行操作: {best_move['shape']} ===")
        sim.handle_operation(best_move['coords'])
        sim.display_board()
    else:
        print("無可執行的操作 (僵局，理論上不應發生，因為有 1-orb)")