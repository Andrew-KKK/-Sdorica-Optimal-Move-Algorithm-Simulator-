import time
from typing import List, Dict, Optional, Any
from soul_board_simulator import SoulOrbSimulator, OrbColor
from move_algorithm import SdoricaSolver

class SdoricaController:
    """
    Sdorica 實驗控制器 (API)。
    用於執行自動化實驗、收集數據並驗證演算法表現。
    """

    def __init__(self):
        self.sim: Optional[SoulOrbSimulator] = None
        self.solver: Optional[SdoricaSolver] = None
        
        # 實驗設定
        self.priority_list: Dict[str, int] = {}
        self.orb_bonus: int = 0
        
        # 統計數據
        self.turn_count = 0
        self.total_score = 0
        self.one_orb_count = 0   # 紀錄 1 消次數
        self.two_orb_count = 0   # 紀錄 2 消次數
        self.four_orb_count = 0  # 紀錄 4 消次數
        self.history: List[str] = []
        self.is_stuck = False

    def setup_experiment(self, 
                         seed: int, 
                         priority_list: Dict[str, int], 
                         orb_bonus: int = 9,
                         skills: List[str] = None) -> None:
        """
        初始化實驗環境。
        """
        if skills is None:
            # 預設支援常見的技能形狀
            skills = ["1-orb", "2-orb", "4-orb-square", "4-orb-L", "4-orb-I"]
            
        self.priority_list = priority_list
        self.orb_bonus = orb_bonus
        self.sim = SoulOrbSimulator(skills=skills, orb_bonus=orb_bonus, seed=seed)
        self.solver = SdoricaSolver()
        
        # 重置統計
        self.turn_count = 0
        self.total_score = 0
        self.one_orb_count = 0
        self.two_orb_count = 0
        self.four_orb_count = 0
        self.history = []
        self.is_stuck = False

    def run_turn(self, verbose: bool = False) -> Dict[str, Any]:
        """
        執行單一回合的 AI 決策。
        """
        if not self.sim or not self.solver:
            raise RuntimeError("請先呼叫 setup_experiment。")

        # 1. AI 決策
        best_move = self.solver.get_best_move_greedy(self.sim, self.priority_list)
        
        result = {
            "turn": self.turn_count + 1,
            "action": None,
            "score": 0,
            "success": False
        }

        if best_move:
            # 計算該步得分
            move_score = self.solver.calculate_score(best_move, self.priority_list, self.orb_bonus)
            
            # 2. 執行操作
            success = self.sim.handle_operation(best_move['coords'])
            
            if success:
                self.turn_count += 1
                self.total_score += move_score
                
                # 紀錄各類消除次數
                shape_str = best_move['shape']
                if "4-orb" in shape_str:
                    self.four_orb_count += 1
                elif "2-orb" in shape_str:
                    self.two_orb_count += 1
                elif "1-orb" in shape_str:
                    self.one_orb_count += 1
                
                action_desc = f"{best_move['shape']} ({best_move['color']})"
                self.history.append(f"T{self.turn_count}: {action_desc} [+ {move_score}]")
                
                result.update({
                    "action": action_desc,
                    "score": move_score,
                    "success": True
                })
                
                if verbose:
                    print(f"Turn {self.turn_count}: {action_desc} -> +{move_score} 分")
        else:
            self.is_stuck = True
            self.history.append(f"T{self.turn_count + 1}: 無可執行操作")
            if verbose:
                print(f"Turn {self.turn_count + 1}: [警告] 無法找到任何合法操作")
            
        return result

    def run_experiment(self, max_turns: int = 50, verbose: bool = False) -> Dict[str, Any]:
        """
        執行完整的實驗流程。
        """
        start_time = time.time()
        for _ in range(max_turns):
            res = self.run_turn(verbose=verbose)
            if not res["success"]:
                break
        
        duration = time.time() - start_time
        avg_score = self.total_score / self.turn_count if self.turn_count > 0 else 0
        
        return {
            "total_score": self.total_score,
            "turns_completed": self.turn_count,
            "one_orb_triggers": self.one_orb_count,
            "two_orb_triggers": self.two_orb_count,
            "four_orb_triggers": self.four_orb_count,
            "average_per_turn": round(avg_score, 2),
            "status": "Finished" if self.turn_count == max_turns else "Stuck",
            "duration_ms": round(duration * 1000, 2)
        }

    def get_board_state_str(self) -> str:
        """取得純文字格式的盤面。"""
        if not self.sim: return "未初始化"
        return "\n".join([" ".join(orb.color[0] for orb in row) for row in self.sim.board])

# --- 實驗指令區 ---
if __name__ == "__main__":
    lab = SdoricaController()
    
    # 定義實驗組 A (標準優先序)
    A_priority = {
        "1-orb": 10,
        "2-orb": 50,
        "4-orb-square": 100,
    }
    # 定義實驗組 B (激進大招優先序)
    B_priority = {
        "1-orb": 5,
        "2-orb": 20,
        "4-orb-square": 500,
    }
    
    test_seed = 999
    max_t = 500

    print("="*60)
    print(f" 開始執行專題實驗 - 總回合設定: {max_t}")
    print("="*60)

    # 執行實驗組 A
    print("\n[實驗組 A] 設定: 平衡型策略")
    lab.setup_experiment(seed=test_seed, priority_list=A_priority, orb_bonus=0)
    results_a = lab.run_experiment(max_turns=max_t)

    # 執行實驗組 B
    print("\n[實驗組 B] 設定: 激進大招型策略")
    lab.setup_experiment(seed=test_seed, priority_list=B_priority, orb_bonus=0)
    results_b = lab.run_experiment(max_turns=max_t)

    print("\n" + "="*60)
    print(f" {'組別':<6} | {'總分':<6} | {'1消':<6} | {'2消':<5} | {'4消':<5} | {'平均分':<6} | {'狀態'}")
    print("-" * 60)
    
    # 格式化輸出結果
    fmt = "{name:<8} | {score:<8} | {o1:<6} | {o2:<6} | {o4:<6} | {avg:<9} | {status}"
    
    print(fmt.format(
        name="A組", 
        score=results_a['total_score'],
        o1=results_a['one_orb_triggers'],
        o2=results_a['two_orb_triggers'],
        o4=results_a['four_orb_triggers'],
        avg=results_a['average_per_turn'],
        status=results_a['status']
    ))
    
    print(fmt.format(
        name="B組", 
        score=results_b['total_score'],
        o1=results_b['one_orb_triggers'],
        o2=results_b['two_orb_triggers'],
        o4=results_b['four_orb_triggers'],
        avg=results_b['average_per_turn'],
        status=results_b['status']
    ))
    print("="*60)