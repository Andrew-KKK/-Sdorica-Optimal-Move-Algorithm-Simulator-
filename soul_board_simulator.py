import random
from typing import List, Tuple, Set, Dict, FrozenSet, Union

# --- 顏色定義 (Color Constants) ---
class OrbColor:
    GOLD = "GOLD"
    BLACK = "BLACK"
    WHITE = "WHITE"
    EMPTY = "EMPTY"

    # RGB 映射表 (供 GUI 或終端機彩色顯示使用)
    RGB_MAP = {
        GOLD: (255, 200, 0),   # 黃色
        BLACK: (150, 200, 255), # 藍色
        WHITE: (255, 255, 255),# 白色
        EMPTY: (105, 105, 105) # 暗灰色
    }

# --- 魂芯物件 ---
class SoulOrb:
    """
    代表一個魂芯的物件。
    """
    def __init__(self, color: str):
        # 建議保持 color 為字串 ID (OrbColor.GOLD)，邏輯判斷最穩
        self.color = color
        self.state: List[str] = []

    @property
    def rgb(self) -> Tuple[int, int, int]:
        """
        取得該魂芯對應的 RGB 數值
        """
        return OrbColor.RGB_MAP.get(self.color, (255, 255, 255))

    def get_colored_char(self) -> str:
        """
        [新增] 回傳帶有 ANSI 顏色代碼的字元，讓終端機顯示顏色。
        """
        if self.color == OrbColor.EMPTY:
            char = "."
        else:
            char = self.color[0] # G, B, W
            
        r, g, b = self.rgb
        # ANSI Escape Code: \033[38;2;R;G;Bm (設定前景 RGB)
        return f"\033[38;2;{r};{g};{b}m{char}\033[0m"

    def __repr__(self) -> str:
        return self.color[0]

# --- 魂盤模擬器 ---
class SoulOrbSimulator:
    def __init__(self, skills: List[str] = None, orb_bonus: int = 9, seed: int = None):
        self.rows = 2
        self.cols = 7
        self.board: List[List[SoulOrb]] = []
        
        if seed is not None:
            random.seed(seed)
        
        # --- 核心：形狀模板定義 ---
        self.SHAPE_TEMPLATES: Dict[str, FrozenSet[Tuple[int, int]]] = {
            "1-orb": frozenset([(0, 0)]),
            "2-orb_v": frozenset([(0, 0), (1, 0)]),
            "2-orb_h": frozenset([(0, 0), (0, 1)]),
            "3-orb-L_no_tl": frozenset([(0, 1), (1, 0), (1, 1)]),
            "3-orb-L_no_tr": frozenset([(0, 0), (1, 0), (1, 1)]),
            "3-orb-L_no_bl": frozenset([(0, 0), (0, 1), (1, 1)]),
            "3-orb-L_no_br": frozenset([(0, 0), (0, 1), (1, 0)]),
            "3-orb-I_h": frozenset([(0, 0), (0, 1), (0, 2)]),
            "4-orb-square": frozenset([(0, 0), (0, 1), (1, 0), (1, 1)]),
            "4-orb-I_h": frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),
            "4-orb-L_1": frozenset([(0, 0), (1, 0), (1, 1), (1, 2)]), 
            "4-orb-L_2": frozenset([(0, 0), (0, 1), (0, 2), (1, 0)]), 
            "4-orb-L_3": frozenset([(0, 0), (0, 1), (0, 2), (1, 2)]), 
            "4-orb-L_4": frozenset([(0, 2), (1, 0), (1, 1), (1, 2)]), 
            "6-orb-Rect": frozenset([
                (0, 0), (0, 1), (0, 2),
                (1, 0), (1, 1), (1, 2)
            ]),
        }
        
        self.valid_skills: Set[str] = set()
        self.initialize_board(skills, orb_bonus)

    def _create_orb(self, mode: str) -> Union[SoulOrb, List[List[SoulOrb]]]:
        def _create_single_orb(m: str) -> SoulOrb:
            return SoulOrb(random.choice([OrbColor.GOLD, OrbColor.BLACK, OrbColor.WHITE]))

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

    def initialize_board(self, skills: List[str] = None, orb_bonus: int = 9):
        self.board = self._create_orb("INITIALIZE")
        if skills:
            self.set_valid_skills(skills)
        else:
            self.set_valid_skills(["1-orb", "2-orb", "4-orb-square"])
        self.ORB_COUNT_BONUS = orb_bonus

    def set_valid_skills(self, skill_names: List[str]):
        self.valid_skills = set(skill_names)

    def display_settings(self):
        """
        [新增] 顯示目前的設定，包含 RGB 顏色預覽
        """
        print("\n--- 模擬器設定 ---")
        print(f"探索獎勵 (Bonus): {self.ORB_COUNT_BONUS}")
        print("顏色設定 (RGB):")
        for name, rgb in OrbColor.RGB_MAP.items():
            r, g, b = rgb
            # 顯示一個彩色方塊 (如果終端機支援) 和數值
            color_block = f"\033[38;2;{r};{g};{b}m███\033[0m"
            print(f"  {name.ljust(6)}: {str(rgb).ljust(16)} {color_block}")
        print("------------------")

    def display_board(self):
        """
        [更新] 使用 ANSI 顏色顯示魂盤
        """
        print("\n--- 魂盤 (Board) ---")
        for r in range(self.rows):
            # 使用 get_colored_char() 來取得彩色字串
            row_str = " ".join(orb.get_colored_char() for orb in self.board[r])
            print(f"R{r}: {row_str}")
        print("--------------------")

    def handle_operation(self, operation_coords: List[Tuple[int, int]]):
        if not operation_coords:
            raise ValueError("操作列表 (operation_coords) 不可為空。")
        try:
            base_color = self._validate_colors(operation_coords)
            shape_name = self._validate_shape(operation_coords)
        except ValueError as e:
            print(f"[操作失敗] {e}")
            return False

        # 這裡的 base_color 如果要顯示顏色，也可以套用 ANSI
        # 我們簡單用文字描述即可
        print(f"[操作成功] 顏色: {base_color}, 形狀: {shape_name}")
        self.eliminate(operation_coords)
        self.resolve_board()
        self.trigger_skill(shape_name, base_color)
        return True

    def _validate_colors(self, coords: List[Tuple[int, int]]) -> str:
        first_r, first_c = coords[0]
        if not (0 <= first_r < self.rows and 0 <= first_c < self.cols):
            raise ValueError(f"座標 {coords[0]} 超出魂盤邊界。")
        base_color = self.board[first_r][first_c].color
        if base_color == OrbColor.EMPTY:
            raise ValueError("不可消除 'EMPTY' 的魂芯。")
        for r, c in coords[1:]:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"座標 {(r, c)} 超出魂盤邊界。")
            orb_color = self.board[r][c].color
            if orb_color != base_color:
                raise ValueError(f"魂芯顏色不一致：預期為 {base_color}，但在 {(r, c)} 得到 {orb_color}。")
        return base_color

    def _validate_shape(self, coords: List[Tuple[int, int]]) -> str:
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
            raise ValueError(f"無效的魂芯形狀：{sorted(coords)} (正規化為: {normalized_frozenset})")
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
        raise ValueError(
            f"形狀 '{specific_shape_name}' (群組: {group_name}) 雖然合法，"
            f"但不在當前 valid_skills 允許的操作列表中 ({self.valid_skills})。"
        )

    def eliminate(self, coords_to_eliminate: List[Tuple[int, int]]):
        print(f"  > 消除: {coords_to_eliminate}")
        for r, c in coords_to_eliminate:
            self.board[r][c] = SoulOrb(OrbColor.EMPTY)

    def resolve_board(self):
        for r in range(self.rows):
            write_c = 0
            for read_c in range(self.cols):
                if self.board[r][read_c].color != OrbColor.EMPTY:
                    if write_c != read_c:
                        self.board[r][write_c] = self.board[r][read_c]
                    write_c += 1
            for c in range(write_c, self.cols):
                self.board[r][c] = SoulOrb(OrbColor.EMPTY)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c].color == OrbColor.EMPTY:
                    self.board[r][c] = self._create_orb("REFILL")
        print("  > 魂盤結算完成 (向左重力 + 右側回填)")

    def trigger_skill(self, shape_name: str, color: str):
        # 這裡也可以考慮用顏色顯示 color
        r, g, b = OrbColor.RGB_MAP.get(color, (255,255,255))
        color_str = f"\033[38;2;{r};{g};{b}m{color}\033[0m"
        print(f"[技能觸發] 形狀: {shape_name}, 顏色: {color_str}")

# --- 範例測試 ---
if __name__ == "__main__":
    sim = SoulOrbSimulator(skills=["1-orb", "2-orb", "4-orb-square"], seed=42)
    
    # 1. 顯示設定 (這會列印出 RGB 數值和顏色預覽)
    sim.display_settings()
    
    # 2. 顯示魂盤 (現在應該要是彩色的了)
    sim.display_board()
    
    # 測試操作以查看 Log 中的顏色
    sim.handle_operation([(0,2), (1,2)])

    sim.display_board()