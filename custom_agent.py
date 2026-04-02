
import os


import random
from typing import Optional, List, Tuple
from ..agents import Agent
from arcengine import FrameData, GameAction, GameState


class CustomAgent(Agent):
    """
    A simple custom agent that uses frame information to make decisions.

    Strategies:
    1. If game not started or game over -> RESET
    2. For click-based games (ACTION6), try random clicks
    3. Otherwise, cycle through basic actions
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_history = []
        self.last_state = None
        self.reset_count = 0

    def is_done(self, frames: List[FrameData], latest_frame: FrameData) -> bool:
        """Determine if the episode is complete."""
        return latest_frame.state == GameState.WIN

    def _get_available_actions(self, frame: FrameData) -> List[GameAction]:
        """Get available actions for the current frame (v0.9.2+)."""
        if hasattr(frame, 'available_actions') and frame.available_actions:
            return frame.available_actions
        # Fallback to basic actions
        return [a for a in GameAction if a not in [GameAction.RESET]]

    def _analyze_frame(self, frame: FrameData) -> dict:
        """Extract features from the frame for decision making."""
        features = {
            'state': frame.state,
            'levels_completed': frame.levels_completed,
            'win_levels': frame.win_levels,
            'needs_reset': frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER],
            'is_won': frame.state == GameState.WIN,
        }

        # Store for debugging
        self.last_state = frame.state

        return features

    def choose_action(self, frames: List[FrameData], latest_frame: FrameData) -> GameAction:
        """
        Choose the next action based on the current game frame.

        Args:
            frames: List of all frames observed so far
            latest_frame: The most recent frame (current game state)

        Returns:
            The chosen GameAction
        """
        # Analyze the current frame
        features = self._analyze_frame(latest_frame)

        # Strategy 1: Handle game start/end conditions
        if features['needs_reset']:
            print(f"  → Reset (state={latest_frame.state})")
            self.reset_count += 1
            return GameAction.RESET

        if features['is_won']:
            print(f"  🎉 Game won! Completed {latest_frame.levels_completed} levels")
            return GameAction.RESET

        # Strategy 2: Get available actions
        available = self._get_available_actions(latest_frame)

        if not available:
            print("  ⚠️ No actions available, resetting")
            return GameAction.RESET

        # Strategy 3: For click-based games, try random clicks
        # ACTION6 is typically the complex click action
        click_actions = [a for a in available if a.is_complex()]
        if click_actions:
            action = random.choice(click_actions)
            # Random coordinates on a 64x64 grid
            coords = {"x": random.randint(0, 63), "y": random.randint(0, 63)}
            action.set_data(coords)
            print(f"  → Click at {coords}")
            return action

        # Strategy 4: Simple cycling through basic actions
        # Avoid using RESET in normal gameplay
        normal_actions = [a for a in available if a != GameAction.RESET]
        if normal_actions:
            # Try to use a variety of actions, not just the same one
            # Simple strategy: if we've used the same action many times, try something else
            recent_actions = self.action_history[-10:]
            action = random.choice(normal_actions)

            # Avoid getting stuck in a loop
            if len(recent_actions) > 5 and len(set(recent_actions)) == 1:
                # If we've been doing the same action repeatedly, pick a different one
                different_actions = [a for a in normal_actions if a != recent_actions[0]]
                if different_actions:
                    action = random.choice(different_actions)

            print(f"  → Action: {action.name}")
            self.action_history.append(action)
            return action

        # Fallback: random action
        print("  → Random fallback")
        return random.choice(list(GameAction))
