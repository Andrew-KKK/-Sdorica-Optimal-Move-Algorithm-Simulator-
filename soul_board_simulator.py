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

    - 魂盤結構: 2x7 (rows x cols)
    - 操作 (Operations): 接受座標列表，並進行嚴格的顏色與形狀檢查。
    """

    def __init__(self, skills: List[str] = None, orb_bonus: int = 9):
        self.rows = 2
        self.cols = 7
        self.board: List[List[SoulOrb]] = []
        
        # --- 核心：形狀模板定義 ---
        # 我們使用 "frozenset" (不可變集合) 來儲存正規化的形狀。
        # (0, 0) 代表該形狀的 "左上角" 基準點 (min_r, min_c)。
        self.SHAPE_TEMPLATES: Dict[str, FrozenSet[Tuple[int, int]]] = {
            # 1-orb (1x1)
            "1-orb": frozenset([(0, 0)]),
            
            # 2-orb (垂直 1x2)
            # [Fix] 改用底線 _ 分隔，以便與群組邏輯相容 (2-orb_v -> 2-orb)
            "2-orb_v": frozenset([(0, 0), (1, 0)]),
            
            # 2-orb (水平 1x2)
            # [Fix] 改用底線 _ 分隔 (2-orb_h -> 2-orb)
            "2-orb_h": frozenset([(0, 0), (0, 1)]),
            
            # 3-orb (L 形, 2x2 缺少一個角落)
            "3-orb-L_no_tl": frozenset([(0, 1), (1, 0), (1, 1)]), # 缺左上
            "3-orb-L_no_tr": frozenset([(0, 0), (1, 0), (1, 1)]), # 缺右上
            "3-orb-L_no_bl": frozenset([(0, 0), (0, 1), (1, 1)]), # 缺左下
            "3-orb-L_no_br": frozenset([(0, 0), (0, 1), (1, 0)]), # 缺右下
            
            # 3-orb (I 形, 1x3 水平)
            "3-orb-I_h": frozenset([(0, 0), (0, 1), (0, 2)]), # 水平I形
            # 註: 垂直 3-orb (3x1) 在 2x7 魂盤上不可能
            
            # 4-orb (方形, 2x2)
            "4-orb-square": frozenset([(0, 0), (0, 1), (1, 0), (1, 1)]),
            
            # 4-orb (I 形, 1x4 水平)
            "4-orb-I_h": frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),
            
            # 4-orb (L 形, 2x3 網格的變體)
            "4-orb-L_1": frozenset([(0, 0), (1, 0), (1, 1), (1, 2)]), #  stem left, arm bottom-right
            "4-orb-L_2": frozenset([(0, 0), (0, 1), (0, 2), (1, 0)]), # stem left, arm top-right
            "4-orb-L_3": frozenset([(0, 0), (0, 1), (0, 2), (1, 2)]), # arm top, stem top-right
            "4-orb-L_4": frozenset([(0, 2), (1, 0), (1, 1), (1, 2)]), # arm bottom, stem bottom-right
            
            # 6-orb (2x3 矩形)
            "6-orb-Rect": frozenset([
                (0, 0), (0, 1), (0, 2),
                (1, 0), (1, 1), (1, 2)
            ]),
        }
        
        # 目前模擬器允許的消除技能 (可動態設定)
        self.valid_skills: Set[str] = set()

        # --- AI 演算法的超參數 ---
        
        # 2. 探索 (Exploration) 的基礎獎勵
        # 假設 1-orb 的 priority 是 10，我們設定 9
        self.ORB_COUNT_BONUS = 9 

        # 初始化魂盤，並傳入參數
        self.initialize_board(skills, orb_bonus)

    # --- 魂芯建立 (Refinement 3) ---
    def _create_orb(self, mode: str) -> Union[SoulOrb, List[List[SoulOrb]]]:
        """
        所有魂芯建立的唯一入口點 (私有方法)。
        :param mode: 呼叫模式 ("INITIALIZE" 或 "REFILL")
        
        - "INITIALIZE" 模式: 直接回傳一個 2*7 的魂盤 (List[List[SoulOrb]])
        - "REFILL" 模式: 回傳一個單一的魂芯 (SoulOrb)
        """
        
        # 內部輔助函數，用於生成單個魂芯
        def _create_single_orb(m: str) -> SoulOrb:
            """
            根據模式生成單一魂芯。
            """
            return SoulOrb(random.choice(["GOLD", "BLACK", "WHITE"]))

        # 根據使用者要求：如果是 "INITIALIZE" 模式，回傳 2*7 魂盤
        if mode == "INITIALIZE":
            new_board = []
            for r in range(self.rows):
                row_list = []
                for c in range(self.cols):
                    row_list.append(_create_single_orb(mode))
                new_board.append(row_list)
            return new_board # <--- 回傳 List[List[SoulOrb]]
        
        elif mode == "REFILL":
            return _create_single_orb(mode) # <--- 回傳 SoulOrb
        
        raise ValueError(f"未知的 _create_orb 模式: {mode}")

    # --- 魂盤管理 ---
    def initialize_board(self, skills: List[str] = None, orb_bonus: int = 9):
        """
        1. 初始化的 魂芯分派。
        :param skills: 允許的技能形狀列表
        :param orb_bonus: 探索獎勵 (魂芯數基礎獎勵)
        """
        # 呼叫 _create_orb("INITIALIZE")，它將回傳完整的 2x7 魂盤
        self.board = self._create_orb("INITIALIZE")
        
        # 設定允許的技能，如果未提供，則使用預設值
        if skills:
            self.set_valid_skills(skills)
        else:
            # 預設 "2-orb" 會自動匹配 "2-orb_v" 和 "2-orb_h"
            # 預設 "4-orb-square" 是標準的 4 消
            self.set_valid_skills(["1-orb", "2-orb", "4-orb-square"])
            
        # 設定探索獎勵超參數
        self.ORB_COUNT_BONUS = orb_bonus
        print(f"模擬器初始化：探索獎勵 (ORB_COUNT_BONUS) 設為 {self.ORB_COUNT_BONUS}")


    def set_valid_skills(self, skill_names: List[str]):
        """
        設定此模擬器當前允許的消除形狀。
        """
        self.valid_skills = set(skill_names)

    def display_board(self):
        """
        在控制台(console)中印出目前的魂盤狀態。
        """
        print("\n--- 魂盤 (Board) ---")
        for r in range(self.rows):
            # 座標 (r, c) - 頂排是 0, 底排是 1
            print(f"R{r}: " + " ".join(str(self.board[r][c]) for c in range(self.cols)))
        print("--------------------")

    # --- 核心操作邏輯 (Refinement 1 & 2) ---
    def handle_operation(self, operation_coords: List[Tuple[int, int]]):
        """
        處理使用者的魂芯操作 (輸入座標列表)。
        將執行嚴格的檢查。
        """
        if not operation_coords:
            raise ValueError("操作列表 (operation_coords) 不可為空。")

        # --- 檢查 1: 魂芯顏色是否一致 ---
        try:
            base_color = self._validate_colors(operation_coords)
        except ValueError as e:
            print(f"[操作失敗] {e}")
            return False

        # --- 檢查 2: 形狀是否有效且被允許 ---
        try:
            # _validate_shape 會回傳具體的形狀名稱 (e.g., "4-orb-L_1")
            shape_name = self._validate_shape(operation_coords)
        except ValueError as e:
            print(f"[操作失敗] {e}")
            return False

        # --- 執行操作 ---
        print(f"[操作成功] 顏色: {base_color}, 形狀: {shape_name}")
        self.eliminate(operation_coords)
        self.resolve_board()
        self.trigger_skill(shape_name, base_color)
        return True

    def _validate_colors(self, coords: List[Tuple[int, int]]) -> str:
        """
        (檢查 1) 驗證列表中的所有座標是否顏色相同且有效。
        """
        first_r, first_c = coords[0]
        # 檢查第一個座標是否越界
        if not (0 <= first_r < self.rows and 0 <= first_c < self.cols):
            raise ValueError(f"座標 {coords[0]} 超出魂盤邊界。")
            
        base_color = self.board[first_r][first_c].color
        
        if base_color == "EMPTY":
            raise ValueError("不可消除 'EMPTY' 的魂芯。")

        # 檢查剩餘的座標
        for r, c in coords[1:]:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"座標 {(r, c)} 超出魂盤邊界。")
            
            orb_color = self.board[r][c].color
            if orb_color != base_color:
                raise ValueError(f"魂芯顏色不一致：預期為 {base_color}，但在 {(r, c)} 得到 {orb_color}。")
        
        return base_color

    def _validate_shape(self, coords: List[Tuple[int, int]]) -> str:
        """
        (檢查 2) 驗證座標列表是否構成一個有效且被允許的形狀。
        """
        
        # --- 步驟 1: 正規化 (Normalize) 形狀 ---
        if not coords:
            raise ValueError("座標列表為空")
            
        min_r = min(r for r, c in coords)
        min_c = min(c for r, c in coords)
        origin_r, origin_c = min_r, min_c
        
        normalized_set = set()
        for r, c in coords:
            normalized_set.add((r - origin_r, c - origin_c))
        
        normalized_frozenset = frozenset(normalized_set)

        # --- 步驟 2: 在模板中尋找該形狀 ---
        specific_shape_name = None
        for name, template in self.SHAPE_TEMPLATES.items():
            if template == normalized_frozenset:
                specific_shape_name = name # 找到了！ e.g., "4-orb-L_1"
                break
        
        if specific_shape_name is None:
            raise ValueError(f"無效的魂芯形狀：{sorted(coords)} (正規化為: {normalized_frozenset})")
        
        # --- 步驟 3: 檢查該形狀是否在 valid_skills 列表中 (支援群組) ---
        
        # 檢查 3a: 檢查具體名稱
        if specific_shape_name in self.valid_skills:
            return specific_shape_name

        # 檢查 3b: 檢查群組名稱
        # e.g. "2-orb_v" -> "2-orb"
        parts = specific_shape_name.rsplit('_', 1)
        
        group_name = parts[0] if len(parts) > 1 else specific_shape_name
        
        if group_name in self.valid_skills:
            return specific_shape_name 

        # 檢查 3c: 檢查 "任意形"
        orb_count = len(coords)
        any_group_name = f"{orb_count}-orb-any"
        
        if any_group_name in self.valid_skills:
            return specific_shape_name

        raise ValueError(
            f"形狀 '{specific_shape_name}' (群組: {group_name}) 雖然合法，"
            f"但不在當前 valid_skills 允許的操作列表中 ({self.valid_skills})。"
        )

    # --- 結算 ---
    def eliminate(self, coords_to_eliminate: List[Tuple[int, int]]):
        """
        將指定的魂芯標記為 'EMPTY'。
        """
        print(f"  > 消除: {coords_to_eliminate}")
        for r, c in coords_to_eliminate:
            self.board[r][c] = SoulOrb("EMPTY")

    def resolve_board(self):
        """
        2. resolve 的魂芯回填。
        包含 重力(Gravity) 和 生成(Generation) 兩個階段。
        """
        # 階段一：重力 (向左)
        for r in range(self.rows):
            write_c = 0
            for read_c in range(self.cols):
                if self.board[r][read_c].color != "EMPTY":
                    if write_c != read_c:
                        self.board[r][write_c] = self.board[r][read_c]
                    write_c += 1
            for c in range(write_c, self.cols):
                self.board[r][c] = SoulOrb("EMPTY")

        # 階段二：生成 (從右側回填)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c].color == "EMPTY":
                    self.board[r][c] = self._create_orb("REFILL")
        
        print("  > 魂盤結算完成 (向左重力 + 從右回填)")

    def trigger_skill(self, shape_name: str, color: str):
        print(f"[技能觸發] 形狀: {shape_name}, 顏色: {color}")


# --- 範例使用 (Example Usage) ---
if __name__ == "__main__":
    
    # 建立一個模擬器 (直接在建立時設定，避免雙重初始化)
    # 預設只允許 1, 2, 4-orb-square
    sim = SoulOrbSimulator(skills=["1-orb", "2-orb", "4-orb-square"])
    print(f"允許的技能: {sim.valid_skills}")
    sim.display_board()

    # --- 範例 1: 測試 2 消 (垂直) ---
    print("\n--- 測試 2 消 (垂直) ---")
    # 為了確保測試成功，我們手動設定顏色
    target_color_v = sim.board[0][0].color
    sim.board[1][0].color = target_color_v
    sim.display_board()
    
    # 執行操作
    operation_list_v = [(0, 0), (1, 0)] # 座標順序不重要
    sim.handle_operation(operation_list_v)
    sim.display_board() # 顯示結算後的新魂盤

    # --- 範例 1.5: 測試 2 消 (水平) ---
    print("\n--- 測試 2 消 (水平) ---")
    # 手動設定顏色
    target_color_h = sim.board[0][3].color
    sim.board[0][4] = SoulOrb(target_color_h)
    sim.display_board()
    
    # 執行操作
    operation_list_h = [(0, 3), (0, 4)]
    sim.handle_operation(operation_list_h) # 預期成功
    sim.display_board() 

    # --- 範例 2: 測試 4-orb-L (L 形) (啟用並測試) ---
    print("\n--- 測試 4-orb-L (群組) ---")
    # 啟用 "4-orb-L" 群組
    sim.set_valid_skills(["4-orb-L"]) 
    print(f"允許的技能: {sim.valid_skills}")
    
    # 手動設定一個 4-orb-L_1 (stem left, arm bottom-right)
    sim.board[0][2] = SoulOrb("GOLD") # (0, 2)
    sim.board[1][2] = SoulOrb("GOLD") # (1, 2)
    sim.board[1][3] = SoulOrb("GOLD") # (1, 3)
    sim.board[1][4] = SoulOrb("GOLD") # (1, 4)
    sim.display_board()
    
    # 座標順序不重要
    op_list_L = [(1, 4), (0, 2), (1, 2), (1, 3)] 
    sim.handle_operation(op_list_L) # 預期成功
    sim.display_board()
    
    # --- 範例 3: 測試 4-orb-I (I 形) (啟用並測試) ---
    print("\n--- 測試 4-orb-I (群組) ---")
    sim.set_valid_skills(["4-orb-I"]) # 啟用 "4-orb-I"
    print(f"允許的技能: {sim.valid_skills}")
    
    sim.board[0][0] = SoulOrb("BLACK")
    sim.board[0][1] = SoulOrb("BLACK")
    sim.board[0][2] = SoulOrb("BLACK")
    sim.board[0][3] = SoulOrb("BLACK")
    sim.display_board()
    
    op_list_I = [(0, 0), (0, 1), (0, 2), (0, 3)]
    sim.handle_operation(op_list_I) # 預期成功
    
    # --- 範例 4: 測試 4-orb-any (任意形) ---
    print("\n--- 測試 4-orb-any (啟用並測試方形) ---")
    sim.set_valid_skills(["4-orb-any"]) # 啟用 "4-orb-any"
    print(f"允許的技能: {sim.valid_skills}")
    
    sim.board[0][0] = SoulOrb("WHITE")
    sim.board[0][1] = SoulOrb("WHITE")
    sim.board[1][0] = SoulOrb("WHITE")
    sim.board[1][1] = SoulOrb("WHITE")
    sim.display_board()
    
    sim.handle_operation([(0,0), (0,1), (1,0), (1,1)]) # 預期成功
    sim.display_board()