"""
TA Exporter Helper Module.
Evaluates Candlestick & Shape TA blocks on datasets and builds taModulesData payload.
Deduplicates consecutive hourly triggers into clean single-instance pattern events.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd

from modules.candlesticks.hammer import HammerBlock
from modules.candlesticks.engulfing import EngulfingBlock
from modules.candlesticks.piercing import PiercingBlock
from modules.shapes.flags import FlagPatternBlock
from modules.shapes.triangles import TrianglePatternBlock
from modules.shapes.institutional_shapes import InstitutionalGeometryBlock
from modules.shapes.mtf_support_resistance import MultiTimeframeSupportResistanceBlock

__all__ = ['evaluate_all_ta_modules']


def extract_block_instances(block_res, df_1h: pd.DataFrame, min_gap_bars: int = 12) -> list:
    instances = []
    n = len(df_1h)
    mask = block_res.mask
    metadata = block_res.metadata or {}
    visual_data = block_res.visual_data or {}

    hit_indices = np.where(mask)[0]
    last_hit_idx = -9999

    for i in hit_indices:
        # Deduplicate consecutive hourly triggers within min_gap_bars window
        if i - last_hit_idx < min_gap_bars:
            continue
        last_hit_idx = i

        t_sec = int(df_1h.index[i].timestamp())
        meta = metadata.get(i, metadata.get(str(i), {}))
        vis = visual_data.get(i, visual_data.get(str(i), {}))

        start_idx = vis.get('start_idx', max(0, i - 4))
        end_idx = vis.get('end_idx', i)
        start_t_sec = int(df_1h.index[start_idx].timestamp()) if start_idx < n else t_sec
        end_t_sec = int(df_1h.index[end_idx].timestamp()) if end_idx < n else t_sec

        h_val = float(vis.get('high', df_1h['High'].iloc[i]))
        l_val = float(vis.get('low', df_1h['Low'].iloc[i]))

        inst = {
            'id': len(instances) + 1,
            'time': t_sec,
            'startTime': start_t_sec,
            'endTime': end_t_sec,
            'priceHigh': round(h_val, 2),
            'priceLow': round(l_val, 2),
            'label': meta.get('type', vis.get('name', block_res.block_name)),
            'res': meta.get('res', []),
            'sup': meta.get('sup', [])
        }
        instances.append(inst)
    return instances


def evaluate_all_ta_modules(df_daily: pd.DataFrame, df_1h: pd.DataFrame) -> Dict[str, Any]:
    """Runs all 3 Candlestick and 4 Chart Shape TA blocks and returns structured payload."""
    df_1h_slice = df_1h.iloc[-5000:] if len(df_1h) > 5000 else df_1h
    blocks = {
        'hammer': HammerBlock(tf='1H'),
        'engulfing': EngulfingBlock(tf='1H'),
        'piercing': PiercingBlock(tf='1H'),
        'flags': FlagPatternBlock(tf='1H'),
        'triangles': TrianglePatternBlock(tf='1H'),
        'institutional_geometry': InstitutionalGeometryBlock(tf='1H'),
        'mtf_sr': MultiTimeframeSupportResistanceBlock()
    }

    payload = {}
    for key, blk in blocks.items():
        try:
            res = blk.evaluate(df_daily, df_1h_slice)
            instances = extract_block_instances(res, df_1h_slice, min_gap_bars=12)
            payload[key] = {
                'name': blk.name,
                'category': blk.category,
                'tf': blk.tf,
                'count': len(instances),
                'instances': instances
            }
        except Exception as e:
            payload[key] = {'name': blk.name, 'category': blk.category, 'tf': blk.tf, 'count': 0, 'instances': []}
    return payload
