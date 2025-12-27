"""
Streamlit dashboard for Photo Factory monitoring.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import docker
import streamlit as st
from sqlalchemy import func

from Shared.database import get_db_session, check_database_connection
from Shared.models import MediaAsset, SystemStatus

logger = logging.getLogger("dashboard")

# Configure Streamlit page
st.set_page_config(
    page_title="Photo Factory Dashboard",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Docker client
try:
    docker_client = docker.from_env()
    DOCKER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Docker client unavailable: {e}")
    docker_client = None
    DOCKER_AVAILABLE = False


def get_container_status(container_name: str) -> Optional[dict]:
    """
    Get real-time container status from Docker.
    
    Args:
        container_name: Name of the container
    
    Returns:
        Dictionary with status info or None if unavailable
    """
    if not DOCKER_AVAILABLE:
        return None
    
    try:
        container = docker_client.containers.get(container_name)
        return {
            "status": container.status,
            "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown"),
            "running": container.status == "running",
        }
    except docker.errors.NotFound:
        return {"status": "not_found", "health": "unknown", "running": False}
    except Exception as e:
        logger.error(f"Error getting container status: {e}")
        return None


def get_librarian_heartbeat() -> Optional[SystemStatus]:
    """Get latest heartbeat from librarian service."""
    try:
        with get_db_session() as session:
            status = session.query(SystemStatus).filter(
                SystemStatus.service_name == "librarian"
            ).first()
            return status
    except Exception as e:
        logger.error(f"Error getting heartbeat: {e}")
        return None


def get_total_assets() -> int:
    """Get total number of processed assets."""
    try:
        with get_db_session() as session:
            count = session.query(func.count(MediaAsset.id)).scalar()
            return count or 0
    except Exception as e:
        logger.error(f"Error getting total assets: {e}")
        return 0


def get_assets_last_hour() -> int:
    """Get number of assets processed in the last hour."""
    try:
        with get_db_session() as session:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            count = session.query(func.count(MediaAsset.id)).filter(
                MediaAsset.ingested_at >= one_hour_ago
            ).scalar()
            return count or 0
    except Exception as e:
        logger.error(f"Error getting assets last hour: {e}")
        return 0


def get_recent_assets(limit: int = 10):
    """Get most recently ingested assets."""
    try:
        with get_db_session() as session:
            assets = session.query(MediaAsset).order_by(
                MediaAsset.ingested_at.desc()
            ).limit(limit).all()
            return assets
    except Exception as e:
        logger.error(f"Error getting recent assets: {e}")
        return []


def get_remaining_files() -> Optional[int]:
    """
    Get count of files remaining in Photos_Inbox.
    
    Returns None if calculation is not feasible without major architectural changes.
    """
    # This would require scanning the inbox directory
    # For now, return None to indicate it's not available
    return None


def main():
    """Main dashboard function."""
    st.title("📸 Photo Factory Dashboard")
    st.markdown("---")
    
    # Check database connection
    db_connected = check_database_connection()
    
    # Sidebar
    with st.sidebar:
        st.header("System Status")
        
        # Database status
        db_status = "🟢 Connected" if db_connected else "🔴 Disconnected"
        st.write(f"**Database:** {db_status}")
        
        # Docker status
        docker_status = "🟢 Available" if DOCKER_AVAILABLE else "🔴 Unavailable"
        st.write(f"**Docker:** {docker_status}")
        
        st.markdown("---")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
        
        if auto_refresh:
            st.rerun()
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # Status indicators
    with col1:
        st.subheader("Librarian Status")
        container_status = get_container_status("librarian")
        
        if container_status:
            if container_status["running"]:
                health = container_status.get("health", "unknown")
                if health == "healthy":
                    st.success("🟢 Running (Healthy)")
                elif health == "unhealthy":
                    st.error("🔴 Running (Unhealthy)")
                else:
                    st.info(f"🟡 Running ({health})")
            else:
                st.error(f"🔴 {container_status['status']}")
        else:
            st.warning("⚠️ Status unavailable")
        
        # Heartbeat indicator
        heartbeat = get_librarian_heartbeat()
        if heartbeat:
            time_since = datetime.now() - heartbeat.last_heartbeat
            if time_since.total_seconds() < 30:
                st.success(f"💓 Heartbeat: {int(time_since.total_seconds())}s ago")
            elif time_since.total_seconds() < 120:
                st.warning(f"💓 Heartbeat: {int(time_since.total_seconds())}s ago")
            else:
                st.error(f"💓 Heartbeat: {int(time_since.total_seconds())}s ago")
            
            if heartbeat.current_task:
                st.caption(f"Task: {heartbeat.current_task}")
    
    # Big numbers
    with col2:
        st.subheader("Total Assets")
        total = get_total_assets()
        st.metric("Processed", f"{total:,}")
    
    with col3:
        st.subheader("Last Hour")
        last_hour = get_assets_last_hour()
        st.metric("Processed", f"{last_hour:,}")
    
    with col4:
        st.subheader("Remaining")
        remaining = get_remaining_files()
        if remaining is not None:
            st.metric("In Inbox", f"{remaining:,}")
        else:
            st.metric("In Inbox", "N/A")
            st.caption("Calculation not available")
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_assets = get_recent_assets(limit=10)
    
    if recent_assets:
        # Create dataframe for display
        try:
            import pandas as pd
        except ImportError:
            st.error("pandas not available - install with: pip install pandas")
            return
        
        data = []
        for asset in recent_assets:
            data.append({
                "File": asset.original_name,
                "Size": f"{asset.size_bytes / 1024 / 1024:.2f} MB",
                "Captured": asset.captured_at.strftime("%Y-%m-%d %H:%M") if asset.captured_at else "N/A",
                "Ingested": asset.ingested_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Location": f"{asset.location['lat']:.4f}, {asset.location['lon']:.4f}" if asset.location else "N/A",
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity")
    
    st.markdown("---")
    
    # Logs section (expandable)
    with st.expander("📋 Service Logs", expanded=False):
        st.subheader("Librarian Logs")
        
        if container_status and container_status["running"]:
            try:
                container = docker_client.containers.get("librarian")
                logs = container.logs(tail=50, timestamps=True).decode("utf-8")
                st.code(logs, language=None)
            except Exception as e:
                st.error(f"Error fetching logs: {e}")
        else:
            st.warning("Container not running or unavailable")


if __name__ == "__main__":
    main()

