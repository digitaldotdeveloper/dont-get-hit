# -*- coding: utf-8 -*-
"""Where the raw generations live, now that they no longer live here.

   The game folder holds what SHIPS plus the scripts that rebuild it. The
   sheets those scripts read -- every Gemini render, the reference art, the
   30-second music masters -- are 145MB of source that the game never loads,
   so they sit with the tool that made them instead:

       Gemini Studio / dgh /  sheets  ref  audio  concept  frames  anim_src

   which is also the DGH section in the Studio dashboard, so a sheet can be
   looked at, re-cut or re-generated from the same place.

   Every cut_*.py reads from SHEETS, every gen_*.py writes into it, and the
   art they produce still lands in art/ and anim/ next to the game. Override
   with DGH_ARCHIVE if the studio ever moves."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the game

ARCHIVE = os.environ.get('DGH_ARCHIVE') or os.path.join(
    os.path.dirname(ROOT), 'Gemini Prompt Sender', 'dashboard', 'dgh')

SHEETS  = os.path.join(ARCHIVE, 'sheets')      # v2 / v3 / v4, the raw renders
REF     = os.path.join(ARCHIVE, 'ref')         # key art + attachment references
AUDIOSRC= os.path.join(ARCHIVE, 'audio')       # the 192k music masters

def sheets(*parts):
    return os.path.join(SHEETS, *parts)

def need(path):
    """A cut script that cannot find its sheet should say where it looked."""
    if not os.path.exists(path):
        raise SystemExit(
            'missing source: %s\n'
            'The raw sheets live in the Gemini Studio dgh archive.\n'
            'Set DGH_ARCHIVE if the studio has moved.' % path)
    return path
