# Sdorica 最佳操作演算法模擬器 (Sdorica Optimal Move Algorithm Simulator)

這是一個基於 Python 開發的專案，旨在模擬雷亞遊戲《Sdorica 萬象物語》中的核心戰鬥機制——「魂盤操作」，並實作演算法以尋求特定盤面下的最佳解。

本專案不僅包含一個高精確度的遊戲模擬器（sandbox），還包含一個基於權重評分系統的決策演算法，能夠在考慮「操作優先序」與「探索獎勵」的情況下做出自動決策。

## 專案核心

### **1. 魂盤模擬器 (`soul_board_simulator.py`)**

這是一個完全獨立運作的 Sdorica 魂盤環境，具備以下特性：

* **精確的物理機制**：完美模擬遊戲中的「向左重力」與「從右側回填」機制。  
* **複雜形狀支援**：  
  * **通用規則**：1 消、2 消 (水平/垂直)、4 消 (方形)。  
  * **特殊形狀**：支援 L 形 (3 消/4 消)、I 形 (水平)、矩形 (6 消) 等多種變體。  
  * **群組驗證**：支援如 4-orb-L 的群組指令，自動匹配所有旋轉變體。  
* **視覺化輸出**：支援終端機 (Terminal) 的 ANSI 彩色輸出，直觀顯示 金/黑/白 魂芯。

### **2. 決策演算法 (`move_algorithm.py`)**

目前的實作採用 **貪婪策略 (Greedy Strategy)**，其決策邏輯基於兩個維度：

* **挖掘 (Exploitation)**：根據使用者定義的 `PRIORITY_LIST`（例如 4 消 > 2 消 > 1 消）來評估操作價值。  
* **探索 (Exploration)**：引入 `ORB_COUNT_BONUS` 機制，獎勵消除魂芯的行為，防止演算法在低分盤面中陷入僵局，鼓勵觸發隨機回填。

### **3. 實驗控制器 (sdorica_lab_api.py`)**

作為使用者與底層邏輯的中介 API，提供：

* **實驗環境設定**：支援固定隨機種子 (Seed)，確保測試結果可重現。  
* **自動化測試**：可連續執行指定回合數，並統計總分與平均分。  
* **資料格式輸出**：提供純文字的盤面狀態字串，方便串接其他分析工具。

## 快速開始 (Quick Start)

### **需求環境**

* Python 3.6 或以上版本。

### **執行測試**

最簡單的方式是直接執行控制器 (Controller)，它會跑一個範例實驗：

``` python
python sdorica_api.py
```

您將在終端機中看到彩色的魂盤輸出，以及 AI 每回合的決策過程

## **檔案結構**

* `soul_board_simulator.py` (模擬器核心)  
  * 定義 `SoulOrb` 與 `SoulOrbSimulator` 類別。  
  * 包含所有形狀模板 (`SHAPE_TEMPLATES`) 與物理邏輯。  
* `sdorica_algorithm.py` (演算法邏輯)  
  * 定義 `SdoricaSolver` 類別。  
  * 負責窮舉所有合法步數 (`find_all_valid_moves`) 並計算分數。  
* `sdorica_api_controller.py` (主程式/API)  
  * 定義 `SdoricaController` 類別。  
  * 整合模擬器與演算法，管理遊戲狀態與統計數據。

## 自定義參數 (Hyperparameters)

這兩個超參數決定了演算法的「性格」與決策邏輯。您可以在 sdorica_api_controller.py 中調整它們，以觀察 AI 行為的變化。

### **1. 操作優先序 (Priority List) - 挖掘 (Exploitation)**

這個列表定義了 AI 對於**已知收益**的價值判斷。分數越高，AI 越傾向執行該操作。

``` python
# 範例設定：高度重視 4 消，普通重視 2 消  
my_priority = {  
    "1-orb": 10,   
    "2-orb": 50,   
    "4-orb-square": 100,  
    "4-orb-L": 80,   
    "4-orb-I": 80  
}
```

### **2. 探索獎勵 (Orb Bonus) - 探索 (Exploration)**

這個參數定義了 AI 對於**未知潛力**（隨機回填）的期望值。它是每消除一顆魂芯所獲得的額外基礎分數。

* **公式**：`Total_Score = Priority_Score + (Orb_Bonus * 消除數量)`
* **調參指南**：  
  * **保守型 (Low Bonus)**：設為 0 或極低。AI 只會關注 Priority List 上的高分操作。如果在爛盤面（無 Combo），它可能會因為分數過低而停滯或做出次佳選擇。  
  * **平衡型 (Medium Bonus)**：建議設為 **略低於 1-orb 的優先序** (例如 9)。這讓 AI 知道「消除魂芯本身是有價值的」，即使只能執行 1 消，也比「什麼都不做」好，從而解決僵局。  
  * **激進型 (High Bonus)**：設為極高 (例如 50)。AI 會變成「洗牌機器」，傾向於一次消除大量魂芯（即使是低優先級的 1 消或 2 消），只為了看下一張牌。

``` python
# 設定範例：平衡型  
controller.setup_experiment(..., orb_bonus=9)
```

## 未來展望

* 實作 **Minimax** 或 **Expectimax** 演算法，引入搜尋深度 (Search Depth)，預測未來幾步的最佳路徑。  
* 加入 **盤面狀態評估 (Heuristics)**，量化盤面的「潛力」與「雜亂度」。  
* 優化使用介面 (GUI)。
