"""All kits, in order. One file per kit -- open it like a score, edit notes."""
import importlib
import os

_here = os.path.dirname(__file__)
_mods = sorted(f[:-3] for f in os.listdir(_here)
               if f.startswith("k") and f.endswith(".py") and f[1:3].isdigit())
KITS = [importlib.import_module(f"kits.{m}").KIT for m in _mods]
