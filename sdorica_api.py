from typing import List, Dict, Optional, Tuple
from soul_board_simulator import SoulOrbSimulator
from sdorica_algorithm import SdoricaSolver

class SdoricaController:
    """
    Sdorica 實驗控制器 (API)。
    作為使用者/GUI 與底層模擬器和演算法之間的中介。
    """

    def __init__(self):
        self.sim: Optional[SoulOrbSimulator] = None
        self.solver: Optional[SdoricaSolver] = None
        
        # 實驗狀態
        self.turn_count = 0
        self.total_score = 0
        self.history: List[str] = [] # 紀錄操作歷史

    def setup_experiment(self, 
                         seed: int, 
                         priority_list: Dict[str, int], 
                         orb_bonus: int = 9,
                         skills: List[str] = None):
        """
        設定並初始化一個新的實驗。
        """
        # 1. 預設技能
        if skills is None:
            skills = ["1-orb", "2-orb", "4-orb-square", "4-orb-L", "4-orb-I"]
            
        # 2. 初始化模擬器
        self.sim = SoulOrbSimulator(skills=skills, seed=seed)
        
        # 3. 初始化演算法
        self.solver = SdoricaSolver(priority_list=priority_list, orb_count_bonus=orb_bonus)
        
        # 4. 重置狀態
        self.turn_count = 0
        self.total_score = 0
        self.history = []
        
        print(f"實驗已初始化 (Seed: {seed})")

    def run_turn(self) -> Dict:
        """
        執行一個回合：
        1. 演算法思考
        2. 執行操作
        3. 更新分數與狀態
        
        :return: 包含本回合執行結果的字典
        """
        if not self.sim or not self.solver:
            raise RuntimeError("請先呼叫 setup_experiment 初始化實驗。")

        # 1. 演算法決策
        best_move = self.solver.get_best_move_greedy(self.sim)
        
        result = {
            "turn": self.turn_count + 1,
            "action": None,
            "score": 0,
            "success": False
        }

        if best_move:
            # 計算該操作的分數 (演算法預估的分數)
            score = self.solver.calculate_score(best_move)
            
            # 2. 執行操作
            success = self.sim.handle_operation(best_move['coords'])
            
            if success:
                self.turn_count += 1
                self.total_score += score
                
                action_desc = f"{best_move['shape']} ({best_move['color']})"
                self.history.append(f"T{self.turn_count}: {action_desc} [+ {score}]")
                
                result["action"] = action_desc
                result["score"] = score
                result["success"] = True
                result["board_after"] = self.get_board_state()
        else:
            self.history.append(f"T{self.turn_count + 1}: 無可執行操作 (Stuck)")
            
        return result

    def run_auto(self, turns: int) -> List[Dict]:
        """
        連續自動執行指定回合數。
        """
        results = []
        for _ in range(turns):
            res = self.run_turn()
            results.append(res)
            if not res["success"]:
                print("實驗中止：無可執行操作")
                break
        return results

    def get_board_state(self) -> str:
        """
        取得當前盤面的字串表示 (用於顯示)。
        """
        if not self.sim:
            return "Sim not initialized"
            
        lines = []
        for r in range(self.sim.rows):
            row_str = " ".join(str(self.sim.board[r][c]) for c in range(self.sim.cols))
            lines.append(f"R{r}: {row_str}")
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """
        取得當前實驗統計數據。
        """
        return {
            "turns": self.turn_count,
            "total_score": self.total_score,
            "average_score": self.total_score / self.turn_count if self.turn_count > 0 else 0
        }

# --- 範例使用 (Example Usage) ---
if __name__ == "__main__":
    # 1. 建立控制器
    controller = SdoricaController()
    
    # 2. 設定實驗參數
    my_priority = {
        "1-orb": 10, "2-orb": 50, "4-orb-square": 100,
        "4-orb-L": 80, "4-orb-I": 80
    }
    
    # 3. 初始化實驗
    print("=== 初始化實驗 ===")
    controller.setup_experiment(seed=999, priority_list=my_priority, orb_bonus=9)
    print(controller.get_board_state())
    
    # 4. 單步執行測試
    print("\n=== 執行單步 (Turn 1) ===")
    res = controller.run_turn()
    print(f"結果: {res['action']}, 得分: {res['score']}")
    print(controller.get_board_state())
    
    # 5. 連續執行測試
    print("\n=== 自動執行 5 回合 ===")
    results = controller.run_auto(5)
    for r in results:
        print(f"Turn {r['turn']}: {r['action']} (+{r['score']})")
        
    # 6. 統計
    print("\n=== 實驗統計 ===")
    stats = controller.get_stats()
    print(f"總回合: {stats['turns']}")
    print(f"總分: {stats['total_score']}")
    print(f"平均分: {stats['average_score']:.2f}")