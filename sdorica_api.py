from typing import List, Dict, Optional, Tuple

# 1. 從模擬器檔案匯入 模擬器類別 和 顏色設定
# [修正] Colors 已更名為 OrbColor
from soul_board_simulator import SoulOrbSimulator, OrbColor

# 2. 從演算法檔案匯入 求解器類別
from sdorica_algorithm import SdoricaSolver

class SdoricaController:
    """
    Sdorica 實驗控制器 (API)。
    作為使用者/GUI 與底層模擬器和演算法之間的中介。
    """

    def __init__(self):
        self.sim: Optional[SoulOrbSimulator] = None
        self.solver: Optional[SdoricaSolver] = None
        
        # 實驗參數 (需要儲存在這裡，以便傳給 Solver)
        self.priority_list: Dict[str, int] = {}
        self.orb_bonus: int = 0
        
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
            
        # 2. 儲存參數
        self.priority_list = priority_list
        self.orb_bonus = orb_bonus

        # 3. 初始化模擬器
        # [修正] 直接傳入 orb_bonus 和 seed
        self.sim = SoulOrbSimulator(skills=skills, orb_bonus=orb_bonus, seed=seed)
        
        # 4. 初始化演算法
        # [修正] Solver 現在是無狀態的，不需要在 init 傳參數
        self.solver = SdoricaSolver()
        
        # 5. 重置狀態
        self.turn_count = 0
        self.total_score = 0
        self.history = []
        
        print(f"實驗已初始化 (Seed: {seed})")

    def run_turn(self) -> Dict:
        """
        執行一個回合。
        """
        if not self.sim or not self.solver:
            raise RuntimeError("請先呼叫 setup_experiment 初始化實驗。")

        # 1. 演算法決策
        # [修正] 需要將 priority_list 傳給 get_best_move_greedy
        best_move = self.solver.get_best_move_greedy(self.sim, self.priority_list)
        
        result = {
            "turn": self.turn_count + 1,
            "action": None,
            "score": 0,
            "success": False,
            "board_str": "" 
        }

        if best_move:
            # 計算分數
            # [修正] 需要將 priority_list 和 orb_bonus 傳給 calculate_score
            score = self.solver.calculate_score(best_move, self.priority_list, self.orb_bonus)
            
            # 2. 執行操作
            # [修正] handle_operation 會直接執行並返回 True/False
            # 這裡我們不捕捉 print output，直接執行
            print(f"\n[Turn {self.turn_count + 1}] AI 決定執行: {best_move['shape']}")
            success = self.sim.handle_operation(best_move['coords'])
            
            if success:
                self.turn_count += 1
                self.total_score += score
                
                action_desc = f"{best_move['shape']} ({best_move['color']})"
                self.history.append(f"T{self.turn_count}: {action_desc} [+ {score}]")
                
                result["action"] = action_desc
                result["score"] = score
                result["success"] = True
        else:
            self.history.append(f"T{self.turn_count + 1}: 無可執行操作 (Stuck)")
            print(f"\n[Turn {self.turn_count + 1}] 無可執行操作")
            
        # 3. 取得執行後的盤面
        result["board_str"] = self.get_board_state_str()
        return result

    def run_auto(self, turns: int) -> List[Dict]:
        """連續自動執行指定回合數。"""
        results = []
        for _ in range(turns):
            res = self.run_turn()
            results.append(res)
            if not res["success"]:
                print("實驗中止：無可執行操作")
                break
        return results

    def show_board(self):
        """直接在終端機顯示盤面 (使用模擬器的漂亮輸出)。"""
        if self.sim:
            # [修正] 最新的 display_board 不需要參數，它會自動輸出彩色版
            self.sim.display_board()
        else:
            print("Sim not initialized")

    def get_board_state_str(self) -> str:
        """
        取得當前盤面的字串表示 (純資料格式)。
        由於模擬器的 display_board 只負責列印，我們這裡手動構建字串。
        """
        if not self.sim:
            return "Sim not initialized"
        
        lines = []
        for r in range(self.sim.rows):
            # 取出每個魂芯顏色的第一個字母 (G, B, W)
            row_str = " ".join(orb.color[0] for orb in self.sim.board[r])
            lines.append(f"R{r}: {row_str}")
        
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """取得當前實驗統計數據。"""
        return {
            "turns": self.turn_count,
            "total_score": self.total_score,
            "average_score": self.total_score / self.turn_count if self.turn_count > 0 else 0
        }

# --- 範例使用 (Example Usage) ---
if __name__ == "__main__":
    controller = SdoricaController()
    
    # 定義優先序
    my_priority = {
        "1-orb": 10, 
        "2-orb": 50, 
        "4-orb-square": 100,
        "4-orb-L": 80, 
        "4-orb-I": 80
    }
    
    print("=== 測試: 初始化實驗 ===")
    # 設定 seed=999, bonus=9
    controller.setup_experiment(seed=999, priority_list=my_priority, orb_bonus=9)
    controller.show_board()
    
    print("\n=== 測試: 執行單步 (Turn 1) ===")
    res = controller.run_turn()
    print(f"結果: {res['action']}, 得分: {res['score']}")
    controller.show_board()

    # 測試純資料格式輸出
    print("\n=== 測試: 純資料格式輸出 (get_board_state_str) ===")
    data_str = controller.get_board_state_str()
    print(data_str)

    # 連續執行測試
    print("\n=== 測試: 自動執行 5 回合 ===")
    results = controller.run_auto(5)
    
    print("\n=== 自動執行摘要 ===")
    for r in results:
        if r['success']:
            print(f"Turn {r['turn']}: {r['action']} (+{r['score']})")
        else:
            print(f"Turn {r['turn']}: Failed/Stuck")
        
    # 統計
    print("\n=== 實驗統計 ===")
    stats = controller.get_stats()
    print(f"總回合: {stats['turns']}")
    print(f"總分: {stats['total_score']}")
    print(f"平均分: {stats['average_score']:.2f}")