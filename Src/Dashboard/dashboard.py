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

from Src.Shared.database import get_db_session, check_database_connection
from Src.Shared.models import MediaAsset, SystemStatus

logger = logging.getLogger("dashboard")

# Configure Streamlit page
st.set_page_config(
    page_title="Photo Factory Dashboard",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="collapsed"
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


def get_available_services() -> list:
    """Get list of available Docker services."""
    if not DOCKER_AVAILABLE:
        return []
    
    try:
        # Get all containers with the photo-factory prefix or known service names
        containers = docker_client.containers.list(all=True)
        service_names = []
        known_services = ["librarian", "dashboard", "factory-db", "factory_postgres", "syncthing"]
        
        for container in containers:
            name = container.name
            # Check if it's a known service or has photo-factory in the name
            if any(known in name for known in known_services) or "photo-factory" in name.lower():
                service_names.append(name)
        
        # Remove duplicates and sort
        return sorted(list(set(service_names)))
    except Exception as e:
        logger.error(f"Error getting available services: {e}")
        return []


def get_service_logs(service_name: str, tail: int = 100) -> str:
    """
    Get logs from a specific service.
    
    Args:
        service_name: Name of the Docker container/service
        tail: Number of lines to retrieve
    
    Returns:
        Logs as string, or empty string if error
    """
    if not DOCKER_AVAILABLE:
        return ""
    
    try:
        container = docker_client.containers.get(service_name)
        logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
        return logs
    except docker.errors.NotFound:
        return f"[Service '{service_name}' not found]"
    except Exception as e:
        logger.error(f"Error fetching logs from {service_name}: {e}")
        return f"[Error fetching logs from {service_name}: {e}]"


def get_all_logs(services: list, tail: int = 100) -> str:
    """
    Get and combine logs from all services.
    
    Args:
        services: List of service names
        tail: Number of lines per service
    
    Returns:
        Combined logs with service headers
    """
    all_logs = []
    
    for service in services:
        logs = get_service_logs(service, tail=tail)
        if logs:
            # Add service header
            all_logs.append(f"\n{'='*80}")
            all_logs.append(f"SERVICE: {service}")
            all_logs.append(f"{'='*80}\n")
            all_logs.append(logs)
    
    return "\n".join(all_logs)


def main():
    """Main dashboard function."""
    # Set page title via JavaScript to prevent flickering
    st.markdown(
        """
        <script>
        document.title = "Photo Factory Dashboard";
        </script>
        """,
        unsafe_allow_html=True
    )
    
    st.title("📸 Photo Factory Dashboard")
    st.markdown("---")
    
    # Check database connection
    db_connected = check_database_connection()
    
    # Auto-refresh in sidebar (minimal)
    with st.sidebar:
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Interval (sec)", 5, 60, 10)
        
        if auto_refresh:
            # Use JavaScript to auto-refresh the page
            st.markdown(
                f"""
                <script>
                setTimeout(function(){{
                    window.location.reload();
                }}, {refresh_interval * 1000});
                </script>
                """,
                unsafe_allow_html=True
            )
        
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    # System Status Row
    st.subheader("System Status")
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        db_status = "🟢 Connected" if db_connected else "🔴 Disconnected"
        st.write(f"**Database:** {db_status}")
    
    with status_col2:
        docker_status = "🟢 Available" if DOCKER_AVAILABLE else "🔴 Unavailable"
        st.write(f"**Docker:** {docker_status}")
    
    with status_col3:
        container_status = get_container_status("librarian")
        if container_status:
            if container_status["running"]:
                health = container_status.get("health", "unknown")
                if health == "healthy":
                    st.write("**Librarian:** 🟢 Running (Healthy)")
                elif health == "unhealthy":
                    st.write("**Librarian:** 🔴 Running (Unhealthy)")
                else:
                    st.write(f"**Librarian:** 🟡 Running ({health})")
            else:
                st.write(f"**Librarian:** 🔴 {container_status['status']}")
        else:
            st.write("**Librarian:** ⚠️ Status unavailable")
        
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
    
    st.markdown("---")
    
    # Stats Row - Big Numbers
    st.subheader("Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Assets Secured", f"{get_total_assets():,}")
    
    with col2:
        st.metric("Processed Last Hour", f"{get_assets_last_hour():,}")
    
    with col3:
        remaining = get_remaining_files()
        if remaining is not None:
            st.metric("Remaining in Inbox", f"{remaining:,}")
        else:
            st.metric("Remaining in Inbox", "N/A")
    
    with col4:
        if heartbeat:
            time_since = datetime.now() - heartbeat.last_heartbeat
            st.metric("Last Heartbeat", f"{int(time_since.total_seconds())}s ago")
        else:
            st.metric("Last Heartbeat", "N/A")
    
    st.markdown("---")
    
    # Latest Processed Files
    st.subheader("📁 Latest Processed Files")
    recent_assets = get_recent_assets(limit=10)
    
    if recent_assets:
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
        st.info("No files processed yet")
    
    st.markdown("---")
    
    # Most Recent Logs with Service Selector
    log_col1, log_col2 = st.columns([1, 4])
    
    with log_col1:
        st.subheader("📋 Service Logs")
        
        # Get available services
        available_services = get_available_services()
        
        if available_services:
            # Add "All Services" option at the beginning
            service_options = ["All Services"] + available_services
            
            selected_service = st.selectbox(
                "Filter by service:",
                options=service_options,
                index=0,  # Default to "All Services"
                key="service_selector"
            )
        else:
            selected_service = None
            st.warning("No services available")
    
    with log_col2:
        if not DOCKER_AVAILABLE:
            st.warning("Docker unavailable - cannot fetch logs")
        elif selected_service:
            if selected_service == "All Services":
                # Show logs from all services
                st.subheader("All Services Logs")
                all_logs = get_all_logs(available_services, tail=50)
                
                if all_logs:
                    # Split into lines, sort by timestamp, and show most recent
                    log_lines = []
                    for line in all_logs.split('\n'):
                        if line.strip():
                            log_lines.append(line)
                    
                    # Show last 100 lines total
                    recent_logs = '\n'.join(log_lines[-100:])
                    st.code(recent_logs, language=None)
                else:
                    st.info("No logs available")
            else:
                # Show logs from selected service
                st.subheader(f"Logs: {selected_service}")
                logs = get_service_logs(selected_service, tail=100)
                
                if logs:
                    # Split logs into lines and show most recent
                    log_lines = logs.strip().split('\n')
                    recent_logs = '\n'.join(log_lines[-50:])  # Show last 50 lines
                    st.code(recent_logs, language=None)
                else:
                    st.info(f"No logs available for {selected_service}")
        else:
            st.info("Select a service to view logs")


if __name__ == "__main__":
    main()

