import time
from typing import Dict, List, Optional, Tuple, Callable
from macro_interface import MacroInterface, Position
from cv_utils import click_center

class MacroBaccarat:
    def __init__(self, macro_interface: MacroInterface, logger: Optional[Callable[[str], None]] = None):
        self.macro = macro_interface
        self.logger = logger
    
    def log(self, msg: str) -> None:
        if self.logger:
            self.logger(msg)
    
    def is_configured(self) -> bool:
        """Check if all required positions are configured"""
        return self.macro.is_configured()
    
    def get_bet_area_position(self, side: str) -> Optional[Position]:
        """Get the position for a bet area"""
        if side == 'Player':
            return self.macro.get_position('player_area')
        elif side == 'Banker':
            return self.macro.get_position('banker_area')
        return None
    
    def get_chip_position(self, amount: int) -> Optional[Position]:
        """Get the position for a specific chip amount"""
        return self.macro.get_chip_position(amount)
    
    def get_cancel_button_position(self) -> Optional[Position]:
        """Get the position for the cancel button"""
        return self.macro.get_position('cancel_button')
    
    def compose_amount(self, target: int) -> Optional[List[int]]:
        """Find the best combination of chips to reach the target amount"""
        available_chips = [chip.amount for chip in self.macro.get_all_chips()]
        available_chips.sort(reverse=True)
        
        # Dynamic programming to find the best combination
        dp = {0: []}
        for t in range(1, target + 1):
            for chip in available_chips:
                if t - chip in dp:
                    dp[t] = dp[t - chip] + [chip]
                    break
        return dp.get(target)
    
    def place_bet(self, amount: int, side: str) -> Tuple[bool, str]:
        """Place a bet using macro positions"""
        self.log(f"Place bet start: amount={amount}, side={side}")
        
        # Validate inputs
        if side not in ('Player', 'Banker'):
            self.log("Error: invalid_side")
            return False, 'invalid_side'
        
        if amount <= 0:
            self.log("Error: invalid_amount")
            return False, 'invalid_amount'
        
        # Check if configured
        if not self.is_configured():
            self.log("Error: not_configured")
            return False, 'not_configured'
        
        # Get bet area position
        area_pos = self.get_bet_area_position(side)
        if not area_pos:
            self.log(f"Error: bet_area_not_found ({side})")
            return False, 'bet_area_not_found'
        
        # Try to find exact chip first
        chip_pos = self.get_chip_position(amount)
        if chip_pos:
            self.log(f"Exact chip found: {amount} at ({chip_pos.x},{chip_pos.y})")
            click_center((chip_pos.x, chip_pos.y, chip_pos.width, chip_pos.height))
            time.sleep(0.2)
            click_center((area_pos.x, area_pos.y, area_pos.width, area_pos.height))
            self.log("Click sequence completed (exact chip)")
            return True, 'ok'
        
        # Compose amount using available chips
        plan = self.compose_amount(amount)
        if not plan:
            self.log("Error: cannot_compose_amount")
            return False, 'cannot_compose_amount'
        
        self.log(f"Chip composition plan: {plan}")
        
        # Click each chip in the plan
        for idx, chip_amount in enumerate(plan, start=1):
            chip_pos = self.get_chip_position(chip_amount)
            if not chip_pos:
                self.log(f"Error: chip_not_found ({chip_amount})")
                return False, 'chip_not_found'
            
            self.log(f"Clicking chip {chip_amount} at ({chip_pos.x},{chip_pos.y}) [{idx}/{len(plan)}]")
            click_center((chip_pos.x, chip_pos.y, chip_pos.width, chip_pos.height))
            time.sleep(0.2)
            click_center((area_pos.x, area_pos.y, area_pos.width, area_pos.height))
            time.sleep(0.15)
        
        self.log("Click sequence completed (composed chips)")
        return True, 'ok'
    
    def cancel_bet(self) -> Tuple[bool, str]:
        """Cancel bet using macro position"""
        cancel_pos = self.get_cancel_button_position()
        if not cancel_pos:
            self.log("Error: cancel_button_not_configured")
            return False, 'cancel_button_not_configured'
        
        self.log(f"Clicking cancel button at ({cancel_pos.x},{cancel_pos.y})")
        
        # Click cancel button multiple times to ensure it's cancelled
        clicks = 0
        for i in range(20):
            click_center((cancel_pos.x, cancel_pos.y, cancel_pos.width, cancel_pos.height))
            clicks += 1
            time.sleep(0.25)
        
        self.log(f"Cancel: clicked {clicks} time(s)")
        return True, 'ok'
    
    def test_chip_click(self, amount: int) -> bool:
        """Test clicking a specific chip amount"""
        chip_pos = self.get_chip_position(amount)
        if not chip_pos:
            self.log(f"Test: chip {amount} not found")
            return False
        
        self.log(f"Test: clicking chip {amount} at ({chip_pos.x},{chip_pos.y})")
        click_center((chip_pos.x, chip_pos.y, chip_pos.width, chip_pos.height))
        return True 