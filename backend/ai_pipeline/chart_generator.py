"""
Chart generator for trending data.
Creates base64-encoded charts for posts with trend data.
"""
import io
import base64
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Platform colors
PLATFORM_COLORS = {
    "reddit": "#FF4500",
    "hackernews": "#FF6600",
    "github": "#24292E",
    "google_trends": "#4285F4",
    "wikipedia": "#A2A9B1",
    "product_hunt": "#DA552F",
    "newsapi": "#2196F3",
    "gdelt": "#9C27B0",
    "x": "#1DA1F2",
    "youtube": "#FF0000",
}


def generate_trend_chart(
    timestamps: List[str],
    values: List[float],
    topic: str,
    platform: str = "unknown"
) -> Optional[str]:
    """
    Generate a line chart showing trend over time.
    Returns base64-encoded PNG or None if matplotlib unavailable.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        color = PLATFORM_COLORS.get(platform, "#6C63FF")
        
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('#1E1E2E')
        ax.set_facecolor('#1E1E2E')
        
        # Parse timestamps if strings
        if timestamps and isinstance(timestamps[0], str):
            from dateutil import parser
            times = [parser.parse(t) for t in timestamps]
        else:
            times = list(range(len(values)))
        
        ax.plot(times, values, color=color, linewidth=2.5, marker='o', markersize=4)
        ax.fill_between(times, values, alpha=0.2, color=color)
        
        # Styling
        ax.set_title(f"📈 {topic} — Real-Time Trend", color='white', fontsize=12, pad=10)
        ax.tick_params(colors='#AAAAAA')
        ax.spines['bottom'].set_color('#444444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#444444')
        ax.yaxis.label.set_color('#AAAAAA')
        ax.xaxis.label.set_color('#AAAAAA')
        
        if isinstance(times[0], datetime):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            fig.autofmt_xdate()
        
        ax.grid(True, alpha=0.2, color='#444444')
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor='#1E1E2E', edgecolor='none')
        buf.seek(0)
        chart_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{chart_b64}"
    
    except ImportError:
        logger.warning("matplotlib not installed — charts disabled")
        return None
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return None


def generate_platform_comparison_chart(
    platform_stats: Dict[str, int],
    title: str = "Platform Activity"
) -> Optional[str]:
    """Generate a bar chart comparing activity across platforms."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#1E1E2E')
        ax.set_facecolor('#1E1E2E')
        
        platforms = list(platform_stats.keys())
        values = list(platform_stats.values())
        colors = [PLATFORM_COLORS.get(p.lower(), "#6C63FF") for p in platforms]
        
        bars = ax.bar(platforms, values, color=colors, width=0.6, edgecolor='none')
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.5,
                    str(val), ha='center', va='bottom', color='white', fontsize=10)
        
        ax.set_title(f"📊 {title}", color='white', fontsize=12, pad=10)
        ax.tick_params(colors='#AAAAAA')
        ax.spines['bottom'].set_color('#444444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#444444')
        ax.set_facecolor('#1E1E2E')
        ax.grid(True, alpha=0.2, color='#444444', axis='y')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor='#1E1E2E', edgecolor='none')
        buf.seek(0)
        chart_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{chart_b64}"
    
    except Exception as e:
        logger.error(f"Bar chart generation failed: {e}")
        return None


def should_generate_chart(item: dict) -> bool:
    """Determine if this item warrants a trend chart."""
    platform = item.get("platform", "")
    chart_platforms = {"google_trends", "github_trending", "hackernews"}
    return platform in chart_platforms
