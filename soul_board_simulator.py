import random
from typing import List, Tuple, Set, Dict, FrozenSet, Union

# --- 魂芯物件 ---
class SoulOrb:
    """
    代表一個魂芯的物件。
    """
    def __init__(self, color: str):
        # 顏色可以是 'GOLD', 'BLACK', 'WHITE', 或 'EMPTY'
        self.color = color
        # 狀態 (state) 是一個 list, 預設為空, 方便未來擴充 (如 'LOCKED', 'REGEN')
        self.state: List[str] = []

    def __repr__(self) -> str:
        """
        用於在控制台(console)中顯示魂盤的輔助函數。
        """
        if self.color == "EMPTY":
            return "."
        # 只顯示顏色的第一個字母 (G, B, W)
        return self.color[0]

# --- 魂盤模擬器 ---
class SoulOrbSimulator:
    """
    Sdorica 魂盤模擬器。
    職責：
    1. 維護魂盤狀態 (2x7 網格)
    2. 執行物理規則 (消除、重力、回填)
    3. 驗證操作合法性 (形狀、顏色)
    """

    def __init__(self, skills: List[str] = None, seed: int = None):
        """
        初始化模擬器。
        :param skills: 允許的技能列表
        :param seed: 隨機數種子 (若為 None 則隨機)
        """
        self.rows = 2
        self.cols = 7
        self.board: List[List[SoulOrb]] = []
        
        # --- 設定隨機數種子 ---
        if seed is not None:
            random.seed(seed)
            print(f"模擬器：已設定隨機數種子為 {seed} (實驗模式)")
        
        # --- 核心：形狀模板定義 ---
        # (0, 0) 代表該形狀的 "左上角" 基準點 (min_r, min_c)。
        self.SHAPE_TEMPLATES: Dict[str, FrozenSet[Tuple[int, int]]] = {
            # 1-orb (1x1)
            "1-orb": frozenset([(0, 0)]),
            
            # 2-orb (垂直 1x2)
            "2-orb_v": frozenset([(0, 0), (1, 0)]),
            
            # 2-orb (水平 1x2)
            "2-orb_h": frozenset([(0, 0), (0, 1)]),
            
            # 3-orb (L 形)
            "3-orb-L_no_tl": frozenset([(0, 1), (1, 0), (1, 1)]), 
            "3-orb-L_no_tr": frozenset([(0, 0), (1, 0), (1, 1)]), 
            "3-orb-L_no_bl": frozenset([(0, 0), (0, 1), (1, 1)]), 
            "3-orb-L_no_br": frozenset([(0, 0), (0, 1), (1, 0)]), 
            
            # 3-orb (I 形)
            "3-orb-I_h": frozenset([(0, 0), (0, 1), (0, 2)]), 
            
            # 4-orb (方形)
            "4-orb-square": frozenset([(0, 0), (0, 1), (1, 0), (1, 1)]),
            
            # 4-orb (I 形)
            "4-orb-I_h": frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),
            
            # 4-orb (L 形)
            "4-orb-L_1": frozenset([(0, 0), (1, 0), (1, 1), (1, 2)]), 
            "4-orb-L_2": frozenset([(0, 0), (0, 1), (0, 2), (1, 0)]), 
            "4-orb-L_3": frozenset([(0, 0), (0, 1), (0, 2), (1, 2)]), 
            "4-orb-L_4": frozenset([(0, 2), (1, 0), (1, 1), (1, 2)]), 
            
            # 6-orb (2x3 矩形)
            "6-orb-Rect": frozenset([
                (0, 0), (0, 1), (0, 2),
                (1, 0), (1, 1), (1, 2)
            ]),
        }
        
        # 目前模擬器允許的消除技能
        self.valid_skills: Set[str] = set()

        # 初始化魂盤
        self.initialize_board(skills)

    # --- 魂芯建立 ---
    def _create_orb(self, mode: str) -> Union[SoulOrb, List[List[SoulOrb]]]:
        """生成魂芯的唯一入口點。"""
        def _create_single_orb(m: str) -> SoulOrb:
            return SoulOrb(random.choice(["GOLD", "BLACK", "WHITE"]))

        if mode == "INITIALIZE":
            new_board = []
            for r in range(self.rows):
                row_list = []
                for c in range(self.cols):
                    row_list.append(_create_single_orb(mode))
                new_board.append(row_list)
            return new_board 
        
        elif mode == "REFILL":
            return _create_single_orb(mode) 
        
        raise ValueError(f"未知的 _create_orb 模式: {mode}")

    # --- 魂盤管理 ---
    def initialize_board(self, skills: List[str] = None):
        """初始化魂盤與規則。"""
        self.board = self._create_orb("INITIALIZE")
        
        if skills:
            self.set_valid_skills(skills)
        else:
            # 預設規則
            self.set_valid_skills(["1-orb", "2-orb", "4-orb-square"])

    def set_valid_skills(self, skill_names: List[str]):
        """設定允許的消除形狀。"""
        self.valid_skills = set(skill_names)

    def display_board(self):
        """顯示當前魂盤狀態。"""
        print("\n--- 魂盤 (Board) ---")
        for r in range(self.rows):
            print(f"R{r}: " + " ".join(str(self.board[r][c]) for c in range(self.cols)))
        print("--------------------")

    # --- 核心驗證邏輯 ---
    def _validate_colors(self, coords: List[Tuple[int, int]]) -> str:
        """檢查顏色一致性。"""
        first_r, first_c = coords[0]
        if not (0 <= first_r < self.rows and 0 <= first_c < self.cols):
            raise ValueError(f"座標 {coords[0]} 超出魂盤邊界。")
            
        base_color = self.board[first_r][first_c].color
        
        if base_color == "EMPTY":
            raise ValueError("不可消除 'EMPTY' 的魂芯。")

        for r, c in coords[1:]:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"座標 {(r, c)} 超出魂盤邊界。")
            if self.board[r][c].color != base_color:
                raise ValueError(f"魂芯顏色不一致。")
        
        return base_color

    def _validate_shape(self, coords: List[Tuple[int, int]]) -> str:
        """驗證形狀並回傳形狀名稱。"""
        if not coords:
            raise ValueError("座標列表為空")
            
        min_r = min(r for r, c in coords)
        min_c = min(c for r, c in coords)
        origin_r, origin_c = min_r, min_c
        
        normalized_set = set()
        for r, c in coords:
            normalized_set.add((r - origin_r, c - origin_c))
        
        normalized_frozenset = frozenset(normalized_set)

        specific_shape_name = None
        for name, template in self.SHAPE_TEMPLATES.items():
            if template == normalized_frozenset:
                specific_shape_name = name
                break
        
        if specific_shape_name is None:
            raise ValueError(f"無效的魂芯形狀 (未匹配任何模板)")
        
        # 驗證 valid_skills (支援群組與任意形)
        if specific_shape_name in self.valid_skills:
            return specific_shape_name

        parts = specific_shape_name.rsplit('_', 1)
        group_name = parts[0] if len(parts) > 1 else specific_shape_name
        if group_name in self.valid_skills:
            return specific_shape_name 

        orb_count = len(coords)
        any_group_name = f"{orb_count}-orb-any"
        if any_group_name in self.valid_skills:
            return specific_shape_name

        raise ValueError(f"形狀 '{specific_shape_name}' 合法但不被允許。")

    # --- 操作與結算 ---
    def handle_operation(self, operation_coords: List[Tuple[int, int]]):
        """執行使用者的操作。"""
        if not operation_coords:
            raise ValueError("操作列表不可為空。")

        try:
            base_color = self._validate_colors(operation_coords)
            shape_name = self._validate_shape(operation_coords)
        except ValueError as e:
            print(f"[操作失敗] {e}")
            return False

        print(f"[操作成功] 顏色: {base_color}, 形狀: {shape_name}")
        self.eliminate(operation_coords)
        self.resolve_board()
        self.trigger_skill(shape_name, base_color)
        return True

    def eliminate(self, coords_to_eliminate: List[Tuple[int, int]]):
        """將指定魂芯設為 EMPTY。"""
        print(f"  > 消除: {coords_to_eliminate}")
        for r, c in coords_to_eliminate:
            self.board[r][c] = SoulOrb("EMPTY")

    def resolve_board(self):
        """執行物理結算：向左重力 + 從右回填。"""
        for r in range(self.rows):
            write_c = 0
            for read_c in range(self.cols):
                if self.board[r][read_c].color != "EMPTY":
                    if write_c != read_c:
                        self.board[r][write_c] = self.board[r][read_c]
                    write_c += 1
            for c in range(write_c, self.cols):
                self.board[r][c] = SoulOrb("EMPTY")

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c].color == "EMPTY":
                    self.board[r][c] = self._create_orb("REFILL")
        
        print("  > 魂盤結算完成 (向左重力 + 從右回填)")

    def trigger_skill(self, shape_name: str, color: str):
        print(f"[技能觸發] 形狀: {shape_name}, 顏色: {color}")

# --- 測試區 ---
if __name__ == "__main__":
    print("=== 魂盤模擬器測試 ===")
    # 測試 1: 預設種子    
    print("\n--- 測試 3: Seed = 99 ---")
    sim3 = SoulOrbSimulator(skills=["1-orb"], seed=99)
    sim3.display_board()