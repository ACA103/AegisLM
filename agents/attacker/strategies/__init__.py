"""
Attack Strategies

Contains all attack strategy implementations:
- Injection: Prompt injection attacks
- Jailbreak: Jailbreak attacks
- Bias Trigger: Bias trigger attacks
- Context Poisoning: Context poisoning attacks
- Role Confusion: Role confusion attacks
- Chaining: Multi-turn attack chaining
"""

from agents.attacker.strategies.bias_trigger import BiasTriggerAttack
from agents.attacker.strategies.chaining import ChainingAttack
from agents.attacker.strategies.context_poison import ContextPoisoningAttack
from agents.attacker.strategies.injection import InjectionAttack
from agents.attacker.strategies.jailbreak import JailbreakAttack
from agents.attacker.strategies.role_confusion import RoleConfusionAttack

__all__ = [
    "InjectionAttack",
    "JailbreakAttack",
    "BiasTriggerAttack",
    "ContextPoisoningAttack",
    "RoleConfusionAttack",
    "ChainingAttack",
]
